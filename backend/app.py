
import logging

from flask import Flask, jsonify, render_template, request

from .config import LOG_DIR
from .monitor import ChargingMonitor


LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "application.log"),
    ],
)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

monitor = ChargingMonitor()


@app.get("/")
def index():
    return render_template("dashboard.html")


@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.get("/analytics")
def analytics():
    return render_template("analytics.html")


@app.get("/api/monitor")
def api_monitor():
    with monitor.lock:
        return jsonify(dict(monitor.latest))


@app.get("/api/status")
def api_status():
    with monitor.lock:
        return jsonify(dict(monitor.latest))


@app.get("/api/history")
def history():
    try:
        limit = int(request.args.get("limit", 200))
    except (TypeError, ValueError):
        limit = 200

    limit = min(max(limit, 1), 1000)
    return jsonify(monitor.db.recent(limit))


@app.get("/api/anomalies")
def anomalies():
    return jsonify(monitor.db.anomalies())


@app.get("/api/protection")
def protection():
    return jsonify(monitor.db.protections())


@app.post("/api/reset-protection")
def reset_protection():
    monitor.reset_protection()

    with monitor.lock:
        return jsonify(dict(monitor.latest))


if __name__ == "__main__":
    try:
        monitor.start()

        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False,
            use_reloader=False,
        )

    except KeyboardInterrupt:
        logging.info("Shutdown requested")

    finally:
        monitor.stop()
