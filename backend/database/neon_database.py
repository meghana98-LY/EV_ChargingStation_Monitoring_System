"""
Neon PostgreSQL database service.

This module provides cloud database connectivity for the
Smart EV Charging Station Monitoring System.

SQLite remains available for local/offline storage.

Neon connection is configured through:

    DATABASE_URL

stored in the project's .env file.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


class NeonDatabase:
    """
    Handles connection and operations for Neon PostgreSQL.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
    ):
        self.database_url = (
            database_url
            or DATABASE_URL
        )

        if not self.database_url:

            raise RuntimeError(
                "DATABASE_URL is not configured. "
                "Add your Neon PostgreSQL connection "
                "string to the .env file."
            )

    # ========================================================
    # CONNECTION
    # ========================================================

    def get_connection(self):
        """
        Create a new Neon PostgreSQL connection.
        """

        return psycopg2.connect(
            self.database_url,
            sslmode="require",
        )

    # ========================================================
    # DATABASE INITIALIZATION
    # ========================================================

    def initialize_database(self) -> None:
        """
        Create the monitoring_records table if it does
        not already exist.
        """

        connection = self.get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS
                    monitoring_records (

                        id BIGSERIAL PRIMARY KEY,

                        timestamp TIMESTAMPTZ
                            NOT NULL DEFAULT CURRENT_TIMESTAMP,

                        voltage DOUBLE PRECISION,

                        current DOUBLE PRECISION,

                        power DOUBLE PRECISION,

                        distance_cm DOUBLE PRECISION,

                        vehicle_present BOOLEAN,

                        vehicle_status TEXT,

                        charging_active BOOLEAN,

                        charging_status TEXT,

                        anomaly_status TEXT,

                        is_anomaly BOOLEAN,

                        anomaly_score DOUBLE PRECISION,

                        model_available BOOLEAN,

                        protection_triggered BOOLEAN,

                        protection_status TEXT,

                        protection_reason TEXT
                    )
                    """
                )

            connection.commit()

        finally:

            connection.close()

    # ========================================================
    # INSERT MONITORING READING
    # ========================================================

    def insert_reading(
        self,
        reading: Dict[str, Any],
    ) -> None:
        """
        Store one monitoring result in Neon.
        """

        connection = self.get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO monitoring_records (

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

                        %s, %s, %s,

                        %s, %s, %s,

                        %s, %s,

                        %s, %s, %s, %s,

                        %s, %s, %s
                    )
                    """,
                    (
                        reading.get("voltage"),
                        reading.get("current"),
                        reading.get("power"),

                        reading.get("distance_cm"),
                        reading.get("vehicle_present"),
                        reading.get("vehicle_status"),

                        reading.get("charging_active"),
                        reading.get("charging_status"),

                        reading.get("anomaly_status"),
                        reading.get("is_anomaly"),
                        reading.get("anomaly_score"),
                        reading.get("model_available"),

                        reading.get(
                            "protection_triggered"
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
    # RECENT READINGS
    # ========================================================

    def get_recent_readings(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent monitoring records.
        """

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        connection = self.get_connection()

        try:

            with connection.cursor(
                cursor_factory=RealDictCursor
            ) as cursor:

                cursor.execute(
                    """
                    SELECT
                        id,
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

                    FROM monitoring_records

                    ORDER BY id DESC

                    LIMIT %s
                    """,
                    (limit,),
                )

                return [
                    dict(row)
                    for row in cursor.fetchall()
                ]

        finally:

            connection.close()

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    def test_connection(self) -> bool:
        """
        Test whether Neon is reachable.
        """

        connection = self.get_connection()

        try:

            with connection.cursor() as cursor:

                cursor.execute(
                    "SELECT 1"
                )

                result = cursor.fetchone()

                return result == (1,)

        finally:

            connection.close()