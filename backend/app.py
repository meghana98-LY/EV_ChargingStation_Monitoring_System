"""
Flask application for the Smart EV Charging Station
Monitoring System.

The monitoring loop runs independently in the background.
The dashboard/API only reads the latest monitoring state.
"""

from __future__ import annotations
from backend.routes.analytics import analytics_bp
from flask import Flask, jsonify

from backend.config import HOST, PORT, DEBUG
from backend.routes.dashboard import dashboard_bp
from backend.services.monitor_loop import MonitoringLoop


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)


# ============================================================
# MONITORING LOOP
# ============================================================

monitoring_loop = MonitoringLoop()


# ============================================================
# BLUEPRINTS
# ============================================================

app.register_blueprint(
    dashboard_bp
)
app.register_blueprint(analytics_bp)

# ============================================================
# BASIC ROUTES
# ============================================================

@app.route("/")
def home():

    return jsonify(
        {
            "application":
                "Smart EV Charging Station Monitoring System",

            "status":
                "running",
        }
    )


@app.route("/api/health")
def health():

    return jsonify(
        {
            "status":
                "healthy",

            "service":
                "EV Charging Monitor",

            "monitoring":
                "running",
        }
    )


# ============================================================
# LATEST MONITORING DATA
# ============================================================

@app.route("/api/monitor")
def get_monitor_data():

    reading = (
        monitoring_loop.get_latest_reading()
    )

    # Monitoring has not completed its first cycle yet.
    if reading is None:

        return jsonify(
            {
                "status":
                    "starting",

                "message":
                    "Monitoring loop has not produced "
                    "its first reading yet.",
            }
        ), 503

    response = dict(
        reading
    )

    response["neon_status"] = (
        monitoring_loop.get_neon_status()
    )

    return jsonify(
        response
    )


# ============================================================
# LOCAL SQLITE HISTORY
# ============================================================

@app.route("/api/history")
def get_history():

    try:

        records = (
            monitoring_loop.logger
            .get_recent_readings(20)
        )

        return jsonify(
            {
                "count":
                    len(records),

                "records":
                    records,
            }
        )

    except Exception as exc:

        return jsonify(
            {
                "status":
                    "error",

                "message":
                    str(exc),
            }
        ), 500


# ============================================================
# NEON HISTORY
# ============================================================

@app.route("/api/neon-history")
def get_neon_history():

    try:

        records = (
            monitoring_loop.neon_database
            .get_recent_readings(20)
        )

        return jsonify(
            {
                "count":
                    len(records),

                "records":
                    records,
            }
        )

    except Exception as exc:

        return jsonify(
            {
                "status":
                    "error",

                "message":
                    str(exc),
            }
        ), 500


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(
        "SMART EV CHARGING STATION MONITORING SYSTEM"
    )
    print("=" * 60)

    print(
        f"Host : {HOST}"
    )

    print(
        f"Port : {PORT}"
    )

    print(
        f"Debug: {DEBUG}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # Start continuous monitoring BEFORE Flask starts.
    # --------------------------------------------------------

    monitoring_loop.start()

    try:

        app.run(
            host=HOST,
            port=PORT,
            debug=DEBUG,

            # Prevent Flask's development reloader from
            # creating a second monitoring thread.
            use_reloader=False,
        )

    except KeyboardInterrupt:

        print(
            "\nStopping application..."
        )

    finally:

        monitoring_loop.cleanup()

        print(
            "Application stopped."
        )