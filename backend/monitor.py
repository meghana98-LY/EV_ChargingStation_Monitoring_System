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
            "timestamp": None,
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

    def store_sensor_reading(self, snapshot, score, state):
        """Persist one real sensor sample for the history and analytics APIs."""
        try:
            self.db.record_sensor_reading(
                voltage=snapshot.voltage,
                current=snapshot.current,
                power=snapshot.power,
                anomaly_score=score,
                vehicle_present=snapshot.vehicle_present,
                charging_active=False if self.protection_latched.is_set()
                else self.relay.active,
                protection_status=state,
            )
        except Exception:
            log.exception("Failed to store sensor reading")

    def loop(self):
        while not self.stop_event.is_set():
            try:
                # Always acquire a fresh sensor snapshot. If protection is
                # latched, the reading is for monitoring/history only.
                snapshot = self.sensors.read()

                anomaly = None
                score = None
                state = "IDLE"
                reason = "NO_VEHICLE"

                if self.protection_latched.is_set():
                    # Safety invariant: a latched protection trip must never
                    # energize the relay or clear itself automatically.
                    self.relay.off()
                    state = "PROTECTION_TRIPPED"
                    reason = (
                        "ANOMALY_LATCHED_VEHICLE_PRESENT"
                        if snapshot.vehicle_present
                        else "ANOMALY_LATCHED_VEHICLE_REMOVED"
                    )

                    # Continue scoring new samples for the analytics history.
                    # This prediction does not change the latched state.
                    if (
                        snapshot.vehicle_present
                        and snapshot.current_available
                        and self.detector.available
                    ):
                        try:
                            anomaly = self.detector.predict(
                                snapshot.voltage,
                                snapshot.current,
                                snapshot.power,
                            )
                            score = anomaly.get("anomaly_score")
                        except Exception:
                            log.exception(
                                "ML prediction failed during protection"
                            )

                elif not snapshot.vehicle_present:
                    self.relay.off()
                    state = "IDLE"
                    reason = "NO_VEHICLE"

                elif (
                    ML_REQUIRES_CURRENT
                    and not snapshot.current_available
                ):
                    self.relay.off()
                    state = "SENSOR_ERROR"
                    reason = "CURRENT_SENSOR_NOT_AVAILABLE"

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
                        # Trip immediately and latch protection.
                        self.protection_latched.set()
                        self.relay.off()
                        state = "PROTECTION_TRIPPED"
                        reason = "ANOMALY_DETECTED"
                    else:
                        self.relay.on()
                        state = "CHARGING"
                        reason = "NORMAL_PREDICTION"

                # Publish the latest real sample and state.
                values = {
                    "timestamp": snapshot.timestamp,
                    "state": state,
                    "relay_on": (
                        False
                        if self.protection_latched.is_set()
                        else self.relay.active
                    ),
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

                # Persist every sample, including samples collected after
                # a trip, so /api/history can continue to populate charts.
                self.store_sensor_reading(snapshot, score, state)

                # Only add normal operating samples to training data.
                # Do not feed post-trip readings back into the training set.
                if not self.protection_latched.is_set():
                    try:
                        self.save_training_row(snapshot)
                    except Exception:
                        log.exception("Failed to save training data")

                # Send/store trip notifications only on the transition into
                # protection, not on every subsequent post-trip sample.
                if (
                    anomaly
                    and anomaly.get("is_anomaly", False)
                    and reason == "ANOMALY_DETECTED"
                ):
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
                            log.info(
                                "Anomaly alert email sent successfully"
                            )
                        else:
                            log.warning(
                                "Anomaly email was not sent; check email "
                                "settings and cooldown"
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
                        "Protection tripped. Relay OFF. Sensor sampling "
                        "and history recording will continue; automatic "
                        "charging restart is disabled."
                    )

            except Exception as exc:
                log.exception("Monitoring error")

                try:
                    self.relay.off()
                except Exception:
                    log.exception("Failed to switch relay OFF after error")

                if self.protection_latched.is_set():
                    self.update_latest({
                        "state": "PROTECTION_TRIPPED",
                        "relay_on": False,
                        "reason": "PROTECTION_LATCHED_SENSOR_ERROR",
                    })
                else:
                    self.update_latest({
                        "state": "SENSOR_ERROR",
                        "relay_on": False,
                        "reason": str(exc),
                    })

            self.stop_event.wait(SAMPLE_INTERVAL_SECONDS)

    def reset_protection(self):
        # Switch OFF before clearing the latch. Normal monitoring may resume
        # after this explicit user action; the next sample is evaluated anew.
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
