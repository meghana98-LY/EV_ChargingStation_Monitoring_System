"""
Continuous monitoring loop for the Smart EV Charging Station.

Responsibilities:

    1. Read sensor and system state.
    2. Run anomaly detection and protection logic.
    3. Store readings in SQLite.
    4. Store readings in Neon PostgreSQL.
    5. Maintain the latest monitoring result.

The dashboard can later read the latest result without
triggering a new sensor acquisition.
"""

from __future__ import annotations

import threading
import time
from typing import Optional

from backend.config import SENSOR_READ_INTERVAL
from backend.services.monitor import ChargingMonitor
from backend.services.data_logger import DataLogger
from backend.database.neon_database import NeonDatabase


class MonitoringLoop:
    """
    Manages continuous EV charging station monitoring.
    """

    def __init__(
        self,
        monitor: Optional[ChargingMonitor] = None,
        logger: Optional[DataLogger] = None,
        neon_database: Optional[NeonDatabase] = None,
        interval: float = SENSOR_READ_INTERVAL,
    ):
        self.monitor = (
            monitor
            or ChargingMonitor()
        )

        self.logger = (
            logger
            or DataLogger()
        )

        self.neon_database = (
            neon_database
            or NeonDatabase()
        )

        if interval <= 0:
            raise ValueError(
                "Monitoring interval must be greater than zero."
            )

        self.interval = interval

        self.latest_reading = None

        self.neon_status = "NOT_STARTED"

        self._thread = None

        self._stop_event = threading.Event()

        self._lock = threading.Lock()

    # ========================================================
    # SINGLE MONITORING CYCLE
    # ========================================================

    def run_once(self) -> dict:
        """
        Execute one complete monitoring cycle.

        Returns
        -------
        dict
            Latest monitoring result.
        """

        # ----------------------------------------------------
        # Read sensors and calculate system state
        # ----------------------------------------------------

        reading = self.monitor.read_all()

        # ----------------------------------------------------
        # Local SQLite logging
        #
        # Local storage is the primary persistence layer.
        # ----------------------------------------------------

        self.logger.log_reading(
            reading
        )

        # ----------------------------------------------------
        # Neon cloud logging
        #
        # Failure here must not stop local monitoring.
        # ----------------------------------------------------

        try:

            self.neon_database.insert_reading(
                reading
            )

            neon_status = "STORED"

        except Exception as exc:

            neon_status = "FAILED"

            print(
                "Warning: Neon logging failed:",
                exc,
            )

        # ----------------------------------------------------
        # Store latest state
        # ----------------------------------------------------

        with self._lock:

            self.latest_reading = dict(
                reading
            )

            self.neon_status = neon_status

        return dict(
            reading
        )

    # ========================================================
    # LATEST READING
    # ========================================================

    def get_latest_reading(self) -> Optional[dict]:
        """
        Return the latest monitoring result.

        Returns None if monitoring has not completed
        its first cycle.
        """

        with self._lock:

            if self.latest_reading is None:
                return None

            return dict(
                self.latest_reading
            )

    def get_neon_status(self) -> str:
        """
        Return the status of the most recent Neon write.
        """

        with self._lock:
            return self.neon_status

    # ========================================================
    # BACKGROUND LOOP
    # ========================================================

    def _monitoring_worker(self) -> None:
        """
        Background worker that continuously acquires data.
        """

        while not self._stop_event.is_set():

            cycle_start = time.monotonic()

            try:

                self.run_once()

            except Exception as exc:

                print(
                    "Monitoring cycle failed:",
                    exc,
                )

            elapsed = (
                time.monotonic()
                - cycle_start
            )

            sleep_time = max(
                0.0,
                self.interval - elapsed,
            )

            self._stop_event.wait(
                sleep_time
            )

    # ========================================================
    # START
    # ========================================================

    def start(self) -> None:
        """
        Start the background monitoring loop.
        """

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._monitoring_worker,
            name="EVMonitoringLoop",
            daemon=True,
        )

        self._thread.start()

        print(
            "Monitoring loop started."
        )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self) -> None:
        """
        Stop the background monitoring loop.
        """

        self._stop_event.set()

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):

            self._thread.join(
                timeout=self.interval + 1
            )

        self._thread = None

        print(
            "Monitoring loop stopped."
        )

    # ========================================================
    # CLEANUP
    # ========================================================

    def cleanup(self) -> None:
        """
        Stop monitoring and release hardware resources.
        """

        self.stop()

        self.monitor.cleanup()