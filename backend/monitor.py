
import csv
import logging
import threading
import time
from datetime import datetime, timezone

from .config import *
from .sensor import SensorManager
from .relay_controller import RelayController
from .ml.anomaly_detector import AnomalyDetector
from .services.email_alert import EmailAlertService
from .database.db import Database


log = logging.getLogger(__name__)


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
        self.stop_lock = threading.Lock()

        self.thread = None
        self.stopped = False

        self.csv_path = TRAINING_DATA
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.csv_path.exists():
            with self.csv_path.open("w", newline="") as file:
                writer = csv.writer(file)
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
        with self.stop_lock:
            if self.stopped:
                raise RuntimeError(
                    "ChargingMonitor cannot restart after shutdown"
                )

            if self.thread and self.thread.is_alive():
                return

            self.stop_event.clear()
            self.relay.off()

            self.thread = threading.Thread(
                target=self.loop,
                daemon=True,
                name="ChargingMonitor",
            )
            self.thread.start()

        log.info("Charging monitor started")

    def save_training_row(self, snapshot):
        timestamp = datetime.fromtimestamp(
            snapshot.timestamp,
            timezone.utc,
        ).isoformat()

        with self.csv_path.open("a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                timestamp,
                snapshot.voltage,
                snapshot.current,
                snapshot.power,
            ])

    def update_latest(self, values):
        with self.lock:
            self.latest.update(values)

    def loop(self):
        while not self.stop_event.is_set():

            # After a protection trip, only check vehicle presence.
            # Do not sample voltage/current or run ML predictions.
            if self.protection_latched.is_set():
                try:
                    vehicle, distance = (
                        self.sensors.ultrasonic.vehicle_present(
                            VEHICLE_DISTANCE_THRESHOLD_CM,
                            ULTRASONIC_SAMPLES,
                        )
                    )

                    self.relay.off()

                    self.update_latest({
                        "state": "PROTECTION_TRIPPED",
                        "relay_on": False,
                        "vehicle_present": vehicle,
                        "distance_cm": distance,
                        "reason": (
                            "ANOMALY_LATCHED_VEHICLE_PRESENT"
                            if vehicle
                            else "ANOMALY_LATCHED_VEHICLE_REMOVED"
                        ),
                    })

                except Exception:
                    log.exception(
                        "Vehicle detection failed during protection"
                    )
                    self.relay.off()

                    self.update_latest({
                        "state": "PROTECTION_TRIPPED",
                        "relay_on": False,
                        "reason": "ANOMALY_LATCHED_VEHICLE_CHECK_ERROR",
                    })

                self.stop_event.wait(SAMPLE_INTERVAL_SECONDS)
                continue

            try:
                # Read voltage, vehicle presence and current sensors.
                snapshot = self.sensors.read()

                anomaly = None
                score = None
                state = "IDLE"
                reason = "NO_VEHICLE"

                # No vehicle: charging and prediction remain disabled.
                if not snapshot.vehicle_present:
                    self.relay.off()
                    state = "IDLE"
                    reason = "NO_VEHICLE"

                # A vehicle is present, but current sensing is unavailable.
                elif (
                    ML_REQUIRES_CURRENT
                    and not snapshot.current_available
                ):
                    self.relay.off()
                    state = "SENSOR_ERROR"
                    reason = "CURRENT_SENSOR_NOT_AVAILABLE"

                # A vehicle is present: run anomaly detection.
                else:
                    if not self.detector.available:
                        raise RuntimeError(
                            "Isolation Forest model is unavailable"
                        )

                    anomaly = self.detector.predict(
                        snapshot.voltage,
                        snapshot.current,
                        snapshot.power,
                    )

                    score = anomaly.get("anomaly_score")

                    if anomaly.get("is_anomaly", False):
                        # Latch protection immediately and switch OFF.
                        self.protection_latched.set()
                        self.relay.off()

                        state = "PROTECTION_TRIPPED"
                        reason = "ANOMALY_DETECTED"

                    else:
                        self.relay.on()
                        state = "CHARGING"
                        reason = "NORMAL_PREDICTION"

                # Publish the current reading and protection status.
                values = {
                    "timestamp": snapshot.timestamp,
                    "state": state,
                    "relay_on": self.relay.active,
                    "reason": reason,
                    "vehicle_present": snapshot.vehicle_present,
                    "distance_cm": snapshot.distance_cm,
                    "voltage": snapshot.voltage,
                    "current": snapshot.current,
                    "power": snapshot.power,
                    "anomaly_score": score,
                    "anomaly": anomaly,
                    "current_available": snapshot.current_available,
                }

                self.update_latest(values)

                # Store the sensor reading.
                try:
                    self.db.record_sensor_reading(
                        voltage=snapshot.voltage,
                        current=snapshot.current,
                        power=snapshot.power,
                        anomaly_score=score,
                        vehicle_present=snapshot.vehicle_present,
                        charging_active=self.relay.active,
                        protection_status=state,
                    )
                except Exception:
                    log.exception("Failed to store sensor reading")

                # Only save training data when protection is not latched.
                if not self.protection_latched.is_set():
                    try:
                        self.save_training_row(snapshot)
                    except Exception:
                        log.exception("Failed to save training data")

                # An anomaly triggers the alert and protection records.
                if anomaly and anomaly.get("is_anomaly", False):
                    event = {
                        "timestamp": datetime.fromtimestamp(
                            snapshot.timestamp,
                            timezone.utc,
                        ).isoformat(),
                        "vehicle_present": snapshot.vehicle_present,
                        "voltage": snapshot.voltage,
                        "current": snapshot.current,
                        "power": snapshot.power,
                        "anomaly_score": score,
                        "reason": reason,
                    }

                    try:
                        sent = self.email.send_anomaly_alert(event)

                        if sent:
                            log.info("Anomaly alert email sent successfully")
                        else:
                            log.warning(
                                "Anomaly email was not sent; "
                                "check email settings and cooldown"
                            )
                    except Exception:
                        log.exception("Failed to send anomaly email")

                    try:
                        self.db.record_anomaly(
                            voltage=snapshot.voltage,
                            current=snapshot.current,
                            power=snapshot.power,
                            anomaly_score=score,
                            reason=reason,
                        )
                    except Exception:
                        log.exception("Failed to store anomaly event")

                    try:
                        self.db.record_protection_event(
                            reason=reason,
                            vehicle_present=snapshot.vehicle_present,
                            charging_active=False,
                            voltage=snapshot.voltage,
                            current=snapshot.current,
                            power=snapshot.power,
                            anomaly_score=score,
                        )
                    except Exception:
                        log.exception("Failed to store protection event")

                    log.warning(
                        "Protection tripped. Relay OFF. "
                        "Voltage/current sampling and prediction paused; "
                        "vehicle-presence checks continue."
                    )

            except Exception as exc:
                log.exception("Monitoring error")

                try:
                    self.relay.off()
                except Exception:
                    log.exception("Failed to switch relay OFF after error")

                self.update_latest({
                    "state": "SENSOR_ERROR",
                    "relay_on": False,
                    "reason": str(exc),
                })

            self.stop_event.wait(SAMPLE_INTERVAL_SECONDS)

    def reset_protection(self):
        # Always switch OFF before clearing the protection latch.
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

        log.info(
            "Protection reset manually. Sensor monitoring resumed."
        )

    def stop(self):
        # Make shutdown safe if multiple callers invoke stop().
        with self.stop_lock:
            if self.stopped:
                return

            self.stopped = True
            self.stop_event.set()
            thread = self.thread

        # Do not close GPIO resources while the loop is running.
        if thread and thread.is_alive():
            thread.join(
                timeout=max(SAMPLE_INTERVAL_SECONDS + 5, 10)
            )

        if thread and thread.is_alive():
            log.error(
                "Monitoring thread did not stop in time. "
                "Hardware cleanup was deferred."
            )
            return

        try:
            self.relay.off()
        except Exception:
            log.exception("Failed to switch relay OFF during shutdown")

        try:
            self.sensors.close()
        except Exception:
            log.exception("Failed to close sensors")

        try:
            self.relay.close()
        except Exception:
            log.exception("Failed to close relay")

        log.info("Charging monitor stopped")
