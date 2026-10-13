
import csv
import logging
import threading
from datetime import datetime, timezone

from .config import *
from .sensor import SensorManager
from .relay_controller import RelayController
from .ml.anomaly_detector import AnomalyDetector
from .services.email_alert import EmailAlertService
from .database.db import Database


class ChargingMonitor:
    def __init__(self):
        self.db = Database()

        self.relay = RelayController(
            RELAY_GPIO,
            RELAY_ACTIVE_HIGH,
            HARDWARE_MODE,
        )

        self.sensors = SensorManager()
        self.detector = AnomalyDetector(ML_MODEL_PATH)
        self.email = EmailAlertService()

        self.stop_event = threading.Event()
        self.protection_latched = threading.Event()
        self.lock = threading.Lock()

        self.csv_path = TRAINING_DATA
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.csv_path.exists():
            with self.csv_path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "voltage",
                    "current",
                    "power",
                ])

        self.latest = {
            "state": "IDLE",
            "relay_on": False,
            "reason": "WAITING_FOR_VEHICLE",
            "vehicle_present": False,
            "distance_cm": None,
            "voltage": None,
            "current": None,
            "power": None,
            "anomaly_score": None,
            "anomaly": None,
            "current_available": False,
        }

    def start(self):
        self.relay.off()

        threading.Thread(
            target=self.loop,
            daemon=True,
            name="ChargingMonitor",
        ).start()

    def save_training_row(self, s):
        timestamp = datetime.fromtimestamp(
            s.timestamp, timezone.utc
        ).isoformat()

        with self.csv_path.open("a", newline="") as f:
            csv.writer(f).writerow([
                timestamp,
                s.voltage,
                s.current,
                s.power,
            ])

    def update_latest(self, values):
        with self.lock:
            self.latest.update(values)

    def loop(self):
        while not self.stop_event.is_set():

            # AFTER ANOMALY:
            # Do not read voltage/current or run predictions.
            # Only keep checking the ultrasonic sensor.
            if self.protection_latched.is_set():
                self.relay.off()

                try:
                    vehicle, distance = (
                        self.sensors.ultrasonic.vehicle_present(
                            VEHICLE_DISTANCE_THRESHOLD_CM,
                            ULTRASONIC_SAMPLES,
                        )
                    )

                    self.update_latest({
                        "vehicle_present": vehicle,
                        "distance_cm": distance,
                        "relay_on": False,
                        "state": "PROTECTION_TRIPPED",
                        "reason": (
                            "ANOMALY_LATCHED_VEHICLE_PRESENT"
                            if vehicle
                            else "ANOMALY_LATCHED_VEHICLE_REMOVED"
                        ),
                    })

                except Exception:
                    logging.exception(
                        "Ultrasonic check failed during protection"
                    )

                    self.relay.off()

                    self.update_latest({
                        "relay_on": False,
                        "state": "PROTECTION_TRIPPED",
                        "reason": "ANOMALY_LATCHED_VEHICLE_CHECK_ERROR",
                    })

                self.stop_event.wait(SAMPLE_INTERVAL_SECONDS)
                continue

            try:
                # Continuous sensor sampling while protection is clear.
                s = self.sensors.read()

                anomaly = None
                score = None
                state = "IDLE"
                reason = "NO_VEHICLE"

                # VEHICLE ABSENT:
                # Continue sensing, but do not run anomaly prediction.
                if not s.vehicle_present:
                    self.relay.off()
                    state = "IDLE"
                    reason = "NO_VEHICLE"

                # VEHICLE PRESENT:
                # Require a trained model and valid sensor readings.
                elif not self.detector.available:
                    self.relay.off()
                    state = "MODEL_NOT_READY"
                    reason = "ISOLATION_FOREST_MODEL_MISSING"

                elif (
                    s.voltage is None
                    or s.current is None
                    or s.power is None
                ):
                    self.relay.off()
                    state = "SENSOR_ERROR"
                    reason = "REQUIRED_SENSOR_READING_MISSING"

                else:
                    # Predict only when a vehicle is detected.
                    anomaly = self.detector.predict(
                        s.voltage,
                        s.current,
                        s.power,
                    )

                    score = anomaly["anomaly_score"]

                    if anomaly["is_anomaly"]:
                        # Switch off and latch before external operations.
                        self.relay.off()
                        self.protection_latched.set()

                        state = "PROTECTION_TRIPPED"
                        reason = (
                            "Isolation Forest classified the combination "
                            "of voltage, current, and power as anomalous."
                        )

                    else:
                        self.relay.on()
                        state = "CHARGING"
                        reason = "NORMAL_PREDICTION"

                snapshot = {
                    "timestamp": s.timestamp,
                    "state": state,
                    "relay_on": self.relay.active,
                    "reason": reason,
                    "vehicle_present": s.vehicle_present,
                    "distance_cm": s.distance_cm,
                    "voltage": s.voltage,
                    "current": s.current,
                    "power": s.power,
                    "anomaly_score": score,
                    "anomaly": anomaly,
                    "current_available": s.current_available,
                }

                self.update_latest(snapshot)

                # Store this reading, including the reading that tripped
                # protection. The database receives named arguments.
                try:
                    self.db.record_sensor_reading(
                        voltage=s.voltage,
                        current=s.current,
                        power=s.power,
                        anomaly_score=score,
                        vehicle_present=s.vehicle_present,
                        charging_active=self.relay.active,
                        protection_status=state,
                    )
                except Exception:
                    logging.exception(
                        "Failed to store sensor reading"
                    )

                # Do not append a training sample after a trip.
                if not self.protection_latched.is_set():
                    try:
                        self.save_training_row(s)
                    except Exception:
                        logging.exception(
                            "Failed to save training data"
                        )

                # Send one email attempt for this protection trip.
                if anomaly and anomaly["is_anomaly"]:
                    event = {
                        "timestamp": datetime.fromtimestamp(
                            s.timestamp, timezone.utc
                        ).isoformat(),
                        "vehicle_present": s.vehicle_present,
                        "voltage": s.voltage,
                        "current": s.current,
                        "power": s.power,
                        "anomaly_score": score,
                        "reason": reason,
                    }

                    email_sent = False

                    try:
                        email_sent = (
                            self.email.send_anomaly_alert(event)
                        )

                        if email_sent:
                            logging.info(
                                "Anomaly alert email sent successfully"
                            )
                        else:
                            logging.warning(
                                "Anomaly email was not sent. "
                                "Check email configuration and cooldown."
                            )

                    except Exception:
                        logging.exception(
                            "Failed to send anomaly email"
                        )

                    try:
                        self.db.record_anomaly(
                            voltage=s.voltage,
                            current=s.current,
                            power=s.power,
                            anomaly_score=score,
                            reason=reason,
                        )
                    except Exception:
                        logging.exception(
                            "Failed to store anomaly event"
                        )

                    try:
                        self.db.record_protection_event(
                            reason=reason,
                            vehicle_present=s.vehicle_present,
                            charging_active=False,
                            voltage=s.voltage,
                            current=s.current,
                            power=s.power,
                            anomaly_score=score,
                        )
                    except Exception:
                        logging.exception(
                            "Failed to store protection event"
                        )

                    logging.warning(
                        "Protection tripped. Relay OFF. "
                        "Voltage/current sampling and prediction paused; "
                        "vehicle-presence checks continue."
                    )

            except Exception as exc:
                logging.exception("Monitoring error")

                self.relay.off()

                self.update_latest({
                    "state": "SENSOR_ERROR",
                    "relay_on": False,
                    "reason": str(exc),
                })

            self.stop_event.wait(SAMPLE_INTERVAL_SECONDS)

    def reset_protection(self):
        # Always keep the relay OFF during reset.
        self.relay.off()

        with self.lock:
            self.latest.update({
                "state": "IDLE",
                "relay_on": False,
                "reason": "PROTECTION_RESET",
                "anomaly": None,
                "anomaly_score": None,
            })

        self.protection_latched.clear()

        logging.info(
            "Protection reset manually. Sensor monitoring resumed."
        )

    def stop(self):
        self.stop_event.set()
        self.relay.off()

        try:
            self.sensors.close()
        finally:
            self.relay.close()
