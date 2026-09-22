"""
Data logging service for the EV charging station.

Stores monitoring results in a local SQLite database.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from backend.config import DATABASE_DIR, DATABASE_PATH


class DataLogger:
    """
    Handles SQLite database creation and monitoring-data logging.
    """

    def __init__(
        self,
        database_path: Path = DATABASE_PATH,
    ):
        self.database_path = Path(database_path)

        # Make sure the database directory exists.
        DATABASE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize_database()

    # ========================================================
    # DATABASE INITIALIZATION
    # ========================================================

    def _get_connection(self):
        """
        Create a SQLite database connection.
        """

        return sqlite3.connect(
            self.database_path
        )

    def _initialize_database(self) -> None:
        """
        Create the monitoring table if it does not exist.
        """

        connection = self._get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS monitoring_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    timestamp TEXT NOT NULL,

                    voltage REAL,
                    current REAL,
                    power REAL,

                    distance_cm REAL,
                    vehicle_present INTEGER,
                    vehicle_status TEXT,

                    charging_active INTEGER,
                    charging_status TEXT,

                    anomaly_status TEXT,
                    is_anomaly INTEGER,
                    anomaly_score REAL,
                    model_available INTEGER,

                    protection_triggered INTEGER,
                    protection_status TEXT,
                    protection_reason TEXT
                )
                """
            )

            connection.commit()

        finally:
            connection.close()

    # ========================================================
    # LOG DATA
    # ========================================================

    def log_reading(
        self,
        reading: Dict[str, Any],
    ) -> None:
        """
        Store one monitoring reading in the database.
        """

        timestamp = datetime.now().isoformat(
            timespec="seconds"
        )

        connection = self._get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO monitoring_records (
                    timestamp,

                    voltage,
                    current,
                    power,

                    distance_cm,
                    vehicle_present,
                    vehicle_status,

                    charging_active,
                    charging_status,

                    anomaly_status,
                    is_anomaly,
                    anomaly_score,
                    model_available,

                    protection_triggered,
                    protection_status,
                    protection_reason
                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?
                )
                """,
                (
                    timestamp,

                    reading.get("voltage"),
                    reading.get("current"),
                    reading.get("power"),

                    reading.get("distance_cm"),
                    int(
                        reading.get(
                            "vehicle_present",
                            False,
                        )
                    ),
                    reading.get(
                        "vehicle_status"
                    ),

                    int(
                        reading.get(
                            "charging_active",
                            False,
                        )
                    ),
                    reading.get(
                        "charging_status"
                    ),

                    reading.get(
                        "anomaly_status"
                    ),
                    int(
                        reading.get(
                            "is_anomaly",
                            False,
                        )
                    ),
                    reading.get(
                        "anomaly_score"
                    ),
                    int(
                        reading.get(
                            "model_available",
                            False,
                        )
                    ),

                    int(
                        reading.get(
                            "protection_triggered",
                            False,
                        )
                    ),
                    reading.get(
                        "protection_status"
                    ),
                    reading.get(
                        "protection_reason"
                    ),
                ),
            )

            connection.commit()

        finally:
            connection.close()

    # ========================================================
    # READ LATEST RECORDS
    # ========================================================

    def get_recent_readings(
        self,
        limit: int = 10,
    ) -> list:
        """
        Return the most recent monitoring records.
        """

        connection = self._get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM monitoring_records
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()

            return rows

        finally:
            connection.close()