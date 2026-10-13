import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

def env_bool(k, d=False): return os.getenv(k, str(d)).lower() in {"1","true","yes","on"}
def env_int(k, d): return int(os.getenv(k, d))
def env_float(k, d): return float(os.getenv(k, d))

HARDWARE_MODE = env_bool("HARDWARE_MODE", True)
CURRENT_SENSOR_ENABLED = env_bool("CURRENT_SENSOR_ENABLED", False)
RELAY_GPIO = env_int("RELAY_GPIO", 18)
RELAY_ACTIVE_HIGH = env_bool("RELAY_ACTIVE_HIGH", True)
HC_SR04_TRIGGER_GPIO = env_int("HC_SR04_TRIGGER_GPIO", 14)
HC_SR04_ECHO_GPIO = env_int("HC_SR04_ECHO_GPIO", 15)
VEHICLE_DISTANCE_THRESHOLD_CM = env_float("VEHICLE_DISTANCE_THRESHOLD_CM", 50)
ULTRASONIC_SAMPLES = env_int("ULTRASONIC_SAMPLES", 3)
ADC_VOLTAGE_CHANNEL = env_int("ADC_VOLTAGE_CHANNEL", 0)
ADC_CURRENT_CHANNEL = env_int("ADC_CURRENT_CHANNEL", 1)
ADC_VREF = env_float("ADC_VREF", 3.3)
VOLTAGE_CALIBRATION_FACTOR = env_float("VOLTAGE_CALIBRATION_FACTOR", 5.0)
ACS712_SENSITIVITY = env_float("ACS712_SENSITIVITY", 0.185)
ACS712_ZERO_OFFSET = env_float("ACS712_ZERO_OFFSET", 2.5)
ML_CONTAMINATION = env_float("ML_CONTAMINATION", 0.10)
ML_REQUIRES_CURRENT = env_bool("ML_REQUIRES_CURRENT", True)
ML_MODEL_PATH = ROOT_DIR / "backend/models/isolation_forest.pkl"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(ROOT_DIR/"backend/database/patha_ev_charging.db")))
if not DATABASE_PATH.is_absolute(): DATABASE_PATH = ROOT_DIR / DATABASE_PATH
TRAINING_DATA = ROOT_DIR / "data/training/charging_data.csv"
LOG_DIR = ROOT_DIR / "data/logs"
SAMPLE_INTERVAL_SECONDS = env_float("SAMPLE_INTERVAL_SECONDS", 1.0)
ANOMALY_EMAIL_COOLDOWN_SECONDS = env_int("ANOMALY_EMAIL_COOLDOWN_SECONDS", 300)
EMAIL_ENABLED = env_bool("EMAIL_ENABLED", False)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = env_int("SMTP_PORT", 587)
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "")
