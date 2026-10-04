"""
Neon PostgreSQL database interface.

Stores:
- Sensor readings
- Anomaly events
- Protection events
- Charging sessions
- System events

The database connection is taken from DATABASE_URL in the .env file.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from backend.config import Config


class Database:
    """Thread-safe PostgreSQL database manager for Neon."""

    def __init__(self):
        if not Config.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not configured. "
                "Add your Neon PostgreSQL connection string to .env"
            )

        self.connection_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=Config.DATABASE_URL
        )

        self.init_db()

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = self.connection_pool.getconn()

        try:
            yield conn
            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            self.connection_pool.putconn(conn)

    def init_db(self):
        """Create all required database tables."""

        with self.get_connection() as conn:
            with conn.cursor() as cur:

                # ---------------------------------------------------------
                # Sensor readings
                # ---------------------------------------------------------
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sensor_readings (
                        id BIGSERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        voltage DOUBLE PRECISION,
                        current DOUBLE PRECISION,
                        power DOUBLE PRECISION,
                        anomaly_score DOUBLE PRECISION,
                        vehicle_present BOOLEAN NOT NULL DEFAULT FALSE,
                        charging_active BOOLEAN NOT NULL DEFAULT FALSE,
                        protection_status VARCHAR(100)
                    );
                """)

                # ---------------------------------------------------------
                # Anomaly events
                # ---------------------------------------------------------
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS anomaly_events (
                        id BIGSERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        voltage DOUBLE PRECISION,
                        current DOUBLE PRECISION,
                        power DOUBLE PRECISION,
                        anomaly_score DOUBLE PRECISION,
                        reason TEXT
                    );
                """)

                # ---------------------------------------------------------
                # Protection events
                # ---------------------------------------------------------
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS protection_events (
                        id BIGSERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        reason TEXT NOT NULL,
                        vehicle_present BOOLEAN,
                        charging_active BOOLEAN,
                        voltage DOUBLE PRECISION,
                        current DOUBLE PRECISION,
                        power DOUBLE PRECISION,
                        anomaly_score DOUBLE PRECISION
                    );
                """)

                # ---------------------------------------------------------
                # Charging sessions
                # ---------------------------------------------------------
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS charging_sessions (
                        id BIGSERIAL PRIMARY KEY,
                        start_time TIMESTAMPTZ NOT NULL,
                        end_time TIMESTAMPTZ,
                        vehicle_detected BOOLEAN NOT NULL DEFAULT FALSE,
                        termination_reason TEXT
                    );
                """)

                # ---------------------------------------------------------
                # System events
                # ---------------------------------------------------------
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS system_events (
                        id BIGSERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        message TEXT
                    );
                """)

                # ---------------------------------------------------------
                # Indexes
                # ---------------------------------------------------------
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp
                    ON sensor_readings(timestamp DESC);
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_anomaly_events_timestamp
                    ON anomaly_events(timestamp DESC);
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_protection_events_timestamp
                    ON protection_events(timestamp DESC);
                """)

    # =====================================================================
    # SENSOR READINGS
    # =====================================================================

    def record_sensor_reading(
        self,
        voltage: Optional[float],
        current: Optional[float],
        power: Optional[float],
        anomaly_score: Optional[float],
        vehicle_present: bool,
        charging_active: bool,
        protection_status: Optional[str]
    ):
        """Store one sensor reading in Neon."""

        timestamp = datetime.now(timezone.utc)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sensor_readings (
                        timestamp,
                        voltage,
                        current,
                        power,
                        anomaly_score,
                        vehicle_present,
                        charging_active,
                        protection_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        timestamp,
                        voltage,
                        current,
                        power,
                        anomaly_score,
                        vehicle_present,
                        charging_active,
                        protection_status
                    )
                )

    def get_recent_readings(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return the latest sensor readings."""

        limit = max(1, min(limit, 1000))

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        timestamp,
                        voltage,
                        current,
                        power,
                        anomaly_score,
                        vehicle_present,
                        charging_active,
                        protection_status
                    FROM sensor_readings
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """,
                    (limit,)
                )

                return [dict(row) for row in cur.fetchall()]

    # =====================================================================
    # ANOMALIES
    # =====================================================================

    def record_anomaly(
        self,
        voltage: Optional[float],
        current: Optional[float],
        power: Optional[float],
        anomaly_score: Optional[float],
        reason: str
    ):
        """Store an anomaly event."""

        timestamp = datetime.now(timezone.utc)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO anomaly_events (
                        timestamp,
                        voltage,
                        current,
                        power,
                        anomaly_score,
                        reason
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        timestamp,
                        voltage,
                        current,
                        power,
                        anomaly_score,
                        reason
                    )
                )

    def get_recent_anomalies(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return recent anomaly events."""

        limit = max(1, min(limit, 1000))

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        timestamp,
                        voltage,
                        current,
                        power,
                        anomaly_score,
                        reason
                    FROM anomaly_events
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """,
                    (limit,)
                )

                return [dict(row) for row in cur.fetchall()]

    # =====================================================================
    # PROTECTION EVENTS
    # =====================================================================

    def record_protection_event(
        self,
        reason: str,
        vehicle_present: bool,
        charging_active: bool,
        voltage: Optional[float] = None,
        current: Optional[float] = None,
        power: Optional[float] = None,
        anomaly_score: Optional[float] = None
    ):
        """Store a protection/cutoff event."""

        timestamp = datetime.now(timezone.utc)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO protection_events (
                        timestamp,
                        reason,
                        vehicle_present,
                        charging_active,
                        voltage,
                        current,
                        power,
                        anomaly_score
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        timestamp,
                        reason,
                        vehicle_present,
                        charging_active,
                        voltage,
                        current,
                        power,
                        anomaly_score
                    )
                )

    def get_recent_protection_events(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return recent protection events."""

        limit = max(1, min(limit, 1000))

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        timestamp,
                        reason,
                        vehicle_present,
                        charging_active,
                        voltage,
                        current,
                        power,
                        anomaly_score
                    FROM protection_events
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """,
                    (limit,)
                )

                return [dict(row) for row in cur.fetchall()]

    # =====================================================================
    # CHARGING SESSIONS
    # =====================================================================

    def start_charging_session(
        self,
        vehicle_detected: bool = True
    ) -> int:
        """Start a charging session and return its ID."""

        timestamp = datetime.now(timezone.utc)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO charging_sessions (
                        start_time,
                        vehicle_detected
                    )
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (
                        timestamp,
                        vehicle_detected
                    )
                )

                return cur.fetchone()[0]

    def end_charging_session(
        self,
        session_id: int,
        termination_reason: str
    ):
        """End a charging session."""

        timestamp = datetime.now(timezone.utc)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE charging_sessions
                    SET
                        end_time = %s,
                        termination_reason = %s
                    WHERE id = %s
                    """,
                    (
                        timestamp,
                        termination_reason,
                        session_id
                    )
                )

    # =====================================================================
    # SYSTEM EVENTS
    # =====================================================================

    def record_system_event(
        self,
        event_type: str,
        message: str
    ):
        """Store a system event."""

        timestamp = datetime.now(timezone.utc)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO system_events (
                        timestamp,
                        event_type,
                        message
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        timestamp,
                        event_type,
                        message
                    )
                )

    def get_recent_system_events(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return recent system events."""

        limit = max(1, min(limit, 1000))

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        timestamp,
                        event_type,
                        message
                    FROM system_events
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """,
                    (limit,)
                )

                return [dict(row) for row in cur.fetchall()]

    # =====================================================================
    # CLOSE
    # =====================================================================

    def close(self):
        """Close all database connections."""

        if self.connection_pool:
            self.connection_pool.closeall()