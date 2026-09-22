"""
Configuration for the Smart EV Charging Station Monitoring System.
"""

import os
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "backend" / "database"
DATABASE_PATH = DATABASE_DIR / "ev_charging.db"

MODEL_DIR = BASE_DIR / "backend" / "models"
MODEL_PATH = MODEL_DIR / "isolation_forest.pkl"


# ============================================================
# FLASK CONFIGURATION
# ============================================================

HOST = os.getenv("FLASK_HOST", "0.0.0.0")
PORT = int(os.getenv("FLASK_PORT", "5000"))

DEBUG = os.getenv(
    "FLASK_DEBUG",
    "True"
).lower() == "true"


# ============================================================
# MCP3008 CONFIGURATION
# ============================================================

# SPI channel used by MCP3008
SPI_BUS = 0
SPI_DEVICE = 0

# MCP3008 analog channels
VOLTAGE_CHANNEL = 0
CURRENT_CHANNEL = 1


# ============================================================
# HC-SR04 ULTRASONIC SENSOR
# ============================================================

# BCM GPIO numbering
ULTRASONIC_TRIGGER_PIN = 14
ULTRASONIC_ECHO_PIN = 15

# Object/vehicle detection threshold
VEHICLE_DISTANCE_THRESHOLD_CM = 30.0


# ============================================================
# CHARGING STATUS SWITCH
# ============================================================

# BCM GPIO pin connected to charging toggle switch
CHARGING_SWITCH_PIN = 18


# ============================================================
# SENSOR SAMPLING
# ============================================================

# Time between sensor readings
SENSOR_READ_INTERVAL = 1.0


# ============================================================
# ISOLATION FOREST
# ============================================================

ISOLATION_FOREST_ESTIMATORS = 100
ISOLATION_FOREST_CONTAMINATION = 0.10
ISOLATION_FOREST_RANDOM_STATE = 42


# ============================================================
# PROTECTION LOGIC
# ============================================================

# Protection requires:
#
# 1. Charging is active
# 2. Electrical anomaly is detected
# 3. Vehicle/object is detected
#
# No physical relay is assumed in this configuration.

PROTECTION_REQUIRES_VEHICLE = True