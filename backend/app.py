import logging
from datetime import date, datetime
from decimal import Decimal

from flask import Flask, jsonify, redirect, render_template, request
from psycopg2.extras import RealDictRow

from .monitor import ChargingMonitor


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

log = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates", static_folder="static")

# One monitor instance owns the sensor/relay loop for this process.
monitor = ChargingMonitor()


def json_safe(value):
    """Recursively convert database values into JSON-compatible values."""
    if isinstance(value, dict) or isinstance(value, RealDictRow):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


@app.get("/")
def index():
    return redirect("/dashboard")


@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.get("/analytics")
def analytics():
    return render_template("analytics.html")


@app.get("/api/monitor")
def api_monitor():
    """Return the latest monitoring snapshot."""
    with monitor.lock:
        snapshot = dict(monitor.latest)
    return jsonify(json_safe(snapshot))


@app.get("/api/status")
def api_status():
    """Compatibility endpoint for clients requesting system status."""
    with monitor.lock:
        snapshot = dict(monitor.latest)
    return jsonify(json_safe(snapshot))


@app.get("/api/history")
def history():
    """Return chronological sensor history for the dashboard and charts."""
    try:
        limit = request.args.get("limit", default=200, type=int)
        limit = max(1, min(limit or 200, 1000))

        # This is the method implemented by backend/database/db.py.
        rows = monitor.db.get_recent_readings(limit)

        # Database method returns newest first; charts need oldest first.
        rows.reverse()
        return jsonify(json_safe(rows))
    except Exception:
        log.exception("Failed to retrieve sensor history")
        return jsonify({"error": "Unable to retrieve sensor history"}), 500


@app.get("/api/anomalies")
def anomalies():
    try:
        limit = request.args.get("limit", default=100, type=int)
        limit = max(1, min(limit or 100, 1000))
        rows = monitor.db.get_recent_anomalies(limit)
        rows.reverse()
        return jsonify(json_safe(rows))
    except Exception:
        log.exception("Failed to retrieve anomaly history")
        return jsonify({"error": "Unable to retrieve anomaly history"}), 500


@app.get("/api/protection")
def protection():
    try:
        limit = request.args.get("limit", default=100, type=int)
        limit = max(1, min(limit or 100, 1000))
        rows = monitor.db.get_recent_protection_events(limit)
        rows.reverse()
        return jsonify(json_safe(rows))
    except Exception:
        log.exception("Failed to retrieve protection history")
        return jsonify({"error": "Unable to retrieve protection history"}), 500


@app.post("/api/reset-protection")
def reset_protection():
    try:
        monitor.reset_protection()
        with monitor.lock:
            snapshot = dict(monitor.latest)
        return jsonify({
            "success": True,
            "message": "Protection reset requested. Monitoring will evaluate the next sample.",
            "monitor": json_safe(snapshot),
        })
    except Exception:
        log.exception("Failed to reset protection")
        return jsonify({
            "success": False,
            "error": "Unable to reset protection",
        }), 500


def main():
    monitor.start()
    try:
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
    finally:
        monitor.stop()


if __name__ == "__main__":
    main()
