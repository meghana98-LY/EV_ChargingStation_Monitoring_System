# EV Charging Station Monitoring and Intelligent Anomaly Detection System

An IoT-based early-warning system for EV charging stations using machine learning to detect abnormal charging patterns before they cause battery damage.

## 📋 Table of Contents
1. [Project Objective](#project-objective)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Software Stack](#software-stack)
5. [Hardware Stack](#hardware-stack)
6. [Directory Structure](#directory-structure)
7. [Installation](#installation)
8. [Configuration](#configuration)
9. [Running the System](#running-the-system)
10. [Simulation Mode](#simulation-mode)
11. [Real Sensor Mode](#real-sensor-mode)
12. [ML Methodology](#ml-methodology)
13. [Early-Warning Methodology](#early-warning-methodology)
14. [Email Configuration](#email-configuration)
15. [Cache and Fault Tolerance](#cache-and-fault-tolerance)
16. [GitHub Workflow](#github-workflow)
17. [Raspberry Pi Deployment](#raspberry-pi-deployment)
18. [Testing](#testing)
19. [API Endpoints](#api-endpoints)
20. [Troubleshooting](#troubleshooting)
21. [Limitations](#limitations)
22. [Future Improvements](#future-improvements)

---

## 🎯 Project Objective

The primary objective is to **continuously monitor EV charging parameters and identify abnormal charging behavior at an early stage**, providing warning/critical alerts to enable timely intervention before battery damage occurs.

### Key Points:
- **Early-warning system**: Detects deviations from normal behavior *before* they become severe
- **Not a failure predictor**: The system detects abnormal patterns, not definitive battery failures
- **Timely intervention**: Alerts enable human decision-making to stop charging if needed
- **Fault tolerant**: Continues operation even if sensors fail temporarily

⚠️ **Important**: Simulated sensor values are used during development. These are **TEMPORARY** and will be replaced with real sensor readings when hardware is connected.

---

## ✨ Features

### Core Monitoring
- ✅ Real-time voltage and current monitoring
- ✅ Automatic power calculation
- ✅ Continuous data logging with timestamps
- ✅ Live web dashboard with real-time updates
- ✅ Interactive graph visualization (Voltage, Current, Power over time)

### Anomaly Detection
- ✅ Isolation Forest ML model for anomaly detection
- ✅ Dual-threshold system (Warning and Critical)
- ✅ Trend analysis to detect gradual deviations
- ✅ Persistence checking to avoid false alerts from noise
- ✅ Moving average and standard deviation calculations

### Early-Warning System
- ✅ Consecutive anomaly counting
- ✅ Trend-based warning conditions
- ✅ Rate-of-change analysis
- ✅ Multiple severity levels (NORMAL, WARNING, CRITICAL)
- ✅ Configurable thresholds and parameters

### Fault Tolerance
- ✅ Persistent cache of last-known-good readings
- ✅ Atomic file writes to prevent corruption
- ✅ Automatic fallback to cached data on sensor failure
- ✅ Clear indication of data source (LIVE, STALE, or UNAVAILABLE)
- ✅ Survival of application restarts

### Alerting System
- ✅ Email alerts for Warning and Critical states
- ✅ Configurable email cooldown to prevent spam
- ✅ HTML-formatted alert emails with detailed information
- ✅ Optional alerts (can be disabled for testing)
- ✅ Secure credential storage via .env file

### Sensor Support
- ✅ Simulated sensor for testing without hardware
- ✅ MCP3008 ADC support for Raspberry Pi
- ✅ Pluggable sensor interface for easy extension
- ✅ Automatic calibration factors
- ✅ Support for voltage and current sensors

---

## 🏗️ Architecture

The system follows a modular, event-driven architecture:

```
                 SIMULATED / REAL SENSOR
                           │
                           ▼
                     MCP3008 / Input
                           │
                           ▼
                    Raspberry Pi
                           │
                           ▼
                    Central Monitor (monitor.py)
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Voltage        Current        Power
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    Isolation Forest
                           │
                    Anomaly Score
                           │
                           ▼
                 Trend + Persistence Analysis
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           NORMAL       WARNING      CRITICAL
                           │            │
                           └─────┬──────┘
                                 ▼
                            Email Alert
                                 │
                                 ▼
                           Data Logger
                                 │
                                 ▼
                         Last Good Cache
                                 │
                                 ▼
                            Flask API
                                 │
                                 ▼
                           Web Dashboard
```

### Component Overview

| Component | Purpose |
|-----------|---------|
| **sensor.py** | Sensor abstraction (SimulatedSensor, RealSensor) |
| **monitor.py** | Central monitoring service (thread-safe) |
| **ml_model.py** | Isolation Forest model management |
| **early_warning.py** | Trend analysis + persistence logic |
| **cache_manager.py** | Persistent cache with atomic writes |
| **email_alert.py** | Email alerts with cooldown |
| **app.py** | Flask web server and REST API |
| **config.py** | Centralized configuration |
| **train_model.py** | ML model training script |
| **logger.py** | Logging to console and CSV file |

---

## 💻 Software Stack

- **Python 3.7+**: Core application language
- **Flask 2.3**: Web framework for dashboard and API
- **scikit-learn**: Isolation Forest machine learning
- **numpy & pandas**: Data processing
- **python-dotenv**: Environment configuration
- **smtplib**: Email sending
- **threading**: Multi-threaded monitoring

---

## 🔌 Hardware Stack

### Currently Supported
- Raspberry Pi 3B/4B (primary target)
- Voltage sensor (analog, 0-3.3V range)
- Current sensor (analog, typically Hall effect)
- MCP3008 8-channel ADC converter
- Micro-USB power supply

### Future Support
- Relay module for automatic power cutoff (GPIO control)
- LCD display for local status
- Additional sensor types (temperature, humidity)

⚠️ **Current Status**: Sensors are NOT yet connected. Software is in simulation mode for testing.

---

## 📁 Directory Structure

```
EV_ChargingStation_Monitoring_System/
│
├── data/                          # Runtime data (gitignored)
│   ├── charging_log.csv           # Historical readings
│   └── latest_cache.json          # Last-known-good cache
│
├── models/                        # ML models
│   └── anomaly_model.pkl          # Trained Isolation Forest
│
├── static/                        # Web assets
│   └── style.css                  # Dashboard styling
│
├── templates/                     # HTML templates
│   ├── index.html                 # Main dashboard
│   └── graph.html                 # Graph visualization
│
├── tests/                         # Test suite
│   └── test_system.py             # Comprehensive tests
│
├── app.py                         # Flask application (main entry)
├── config.py                      # Configuration management
├── sensor.py                      # Sensor abstraction layer
├── monitor.py                     # Central monitoring service
├── ml_model.py                    # ML model management
├── early_warning.py               # Early-warning engine
├── cache_manager.py               # Cache management
├── email_alert.py                 # Email alert system
├── logger.py                      # Logging system
├── train_model.py                 # Model training script
│
├── .env.example                   # Example environment config
├── .env                           # Actual config (gitignored)
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── update_project.sh              # Deployment update script
└── ev-charging-monitor.service    # Systemd service file
```

---

## 📦 Installation

### On Windows/Development Machine

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/EV_ChargingStation_Monitoring_System.git
cd EV_ChargingStation_Monitoring_System
```

2. **Create virtual environment**:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Create .env file**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Ensure directories exist**:
```bash
python config.py
```

6. **Train the ML model** (one time):
```bash
python train_model.py
```

### On Raspberry Pi

1. **Update system**:
```bash
sudo apt update
sudo apt upgrade
```

2. **Install Python and dependencies**:
```bash
sudo apt install python3 python3-pip python3-venv git
```

3. **Clone repository**:
```bash
cd ~
git clone https://github.com/yourusername/EV_ChargingStation_Monitoring_System.git
cd EV_ChargingStation_Monitoring_System
```

4. **Set up Python environment**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

5. **Configure environment**:
```bash
cp .env.example .env
nano .env  # Edit with your settings
```

6. **Train model**:
```bash
source venv/bin/activate
python3 train_model.py
```

---

## ⚙️ Configuration

### Configuration Files

All configuration is managed through **environment variables** in `.env` file.

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### Key Configuration Parameters

#### Sensor Settings
- `SENSOR_TYPE`: `simulated` (for testing) or `mcp3008` (real hardware)
- `SAMPLING_INTERVAL`: Seconds between readings (default: 2.0)
- `ADC_REFERENCE_VOLTAGE`: ADC voltage range (default: 3.3V for Raspberry Pi)
- `MCP3008_CHANNEL_VOLTAGE`: ADC channel for voltage (default: 0)
- `MCP3008_CHANNEL_CURRENT`: ADC channel for current (default: 1)

#### ML and Thresholds
- `ANOMALY_THRESHOLD`: Isolation Forest score for anomaly (-0.5)
- `WARNING_THRESHOLD`: Score threshold for warning (-0.2)
- `CRITICAL_THRESHOLD`: Score threshold for critical (0.8)
- `CONSECUTIVE_ANOMALIES_FOR_WARNING`: Count before warning (3)
- `CONSECUTIVE_ANOMALIES_FOR_CRITICAL`: Count before critical (10)

#### Caching and Logging
- `CACHE_MAX_AGE_SECONDS`: Cache validity period (300 seconds)
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
- `TREND_WINDOW_SIZE`: Readings for trend analysis (10)

#### Email Alerts
- `EMAIL_ALERT_ENABLED`: Enable/disable alerts (True/False)
- `SMTP_HOST`: SMTP server (smtp.gmail.com for Gmail)
- `SMTP_PORT`: SMTP port (587 for TLS)
- `SMTP_USER`: Email address for sending
- `SMTP_PASSWORD`: App-specific password (NOT your regular password!)
- `ALERT_EMAIL_TO`: Recipient email address
- `EMAIL_ALERT_COOLDOWN`: Seconds between emails (300)

#### Flask
- `FLASK_HOST`: Server host (0.0.0.0 for all interfaces)
- `FLASK_PORT`: Server port (5000)
- `FLASK_DEBUG`: Debug mode (False for production)

#### Simulation
- `SIMULATION_MODE_NORMAL`: `stable`, `gradual`, or `abrupt`
- `SIMULATION_VOLTAGE_BASE`: Base voltage for simulation (12.0V)
- `SIMULATION_CURRENT_BASE`: Base current for simulation (7.0A)
- `SIMULATION_NOISE_LEVEL`: Noise standard deviation (0.1)

---

## 🚀 Running the System

### Development (Windows/Mac/Linux)

1. **Start in simulation mode**:
```bash
source venv/bin/activate
python app.py
```

2. **Open dashboard**:
   - Navigate to: `http://localhost:5000`
   - Dashboard tab: Main monitoring interface
   - Graph tab: Real-time voltage/current/power graphs

3. **Verify monitoring**:
   - Check API status: `http://localhost:5000/api/status`
   - Check latest readings: `http://localhost:5000/api/latest`
   - View history: `http://localhost:5000/api/history?limit=20`

### Production (Raspberry Pi with systemd)

1. **Install as system service**:
```bash
sudo cp ev-charging-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ev-charging-monitor
```

2. **Start the service**:
```bash
sudo systemctl start ev-charging-monitor
```

3. **Check service status**:
```bash
sudo systemctl status ev-charging-monitor
```

4. **View logs**:
```bash
sudo journalctl -u ev-charging-monitor -f
```

5. **Access dashboard**:
   - Local machine: `http://raspberry-pi-ip:5000`
   - Configure reverse proxy (nginx) for public access

---

## 🧪 Simulation Mode

The system includes a simulated sensor for testing without hardware.

### Running Simulations

By default, `.env` is set to `SENSOR_TYPE=simulated`.

### Simulation Modes

#### 1. Stable Mode (Normal Operation)
```
SIMULATION_MODE_NORMAL=stable
```
Generates normal, stable voltage and current readings with small random noise.

**Expected behavior**: System shows NORMAL status consistently.

#### 2. Gradual Anomaly Mode
```
SIMULATION_MODE_NORMAL=gradual
```
Gradually increases voltage and current over time, simulating a developing fault.

**Expected behavior**:
- First 50 readings: NORMAL
- Readings 50-80: Gradual increase
- Readings 80+: WARNING then CRITICAL status

#### 3. Abrupt Anomaly Mode
```
SIMULATION_MODE_NORMAL=abrupt
```
Sudden voltage/current spike at reading #50.

**Expected behavior**:
- Readings 1-50: NORMAL
- Reading 50: Sudden spike
- Reading 50+: CRITICAL status

### Testing Workflow

1. **Start in stable mode**:
   - Verify system generates normal readings
   - Check dashboard shows NORMAL status
   - Confirm no emails sent

2. **Switch to gradual mode**:
   - Update `.env`: `SIMULATION_MODE_NORMAL=gradual`
   - Restart `app.py`
   - Observe WARNING status appearing
   - Later observe CRITICAL status
   - If email enabled, verify alert emails received with proper cooldown

3. **Test cache fallback**:
   - While running, kill the process (`Ctrl+C`)
   - Check `data/latest_cache.json` still has data
   - Restart app - should still show last known state

4. **Test fault tolerance**:
   - Modify sensor to simulate exception
   - Verify app doesn't crash
   - Check dashboard shows SENSOR_DATA_UNAVAILABLE
   - Verify cached data is served as STALE

---

## 🔍 Real Sensor Mode

When MCP3008 sensors are connected to Raspberry Pi:

### Hardware Setup

1. **Connect MCP3008 ADC to Raspberry Pi**:
   - VDD → GPIO 3.3V
   - VREF → GPIO 3.3V
   - AGND → GPIO GND
   - DGND → GPIO GND
   - CS → GPIO 8 (CE0)
   - DIN → GPIO 10 (MOSI)
   - DOUT → GPIO 9 (MISO)
   - CLK → GPIO 11 (SCLK)

2. **Enable SPI on Raspberry Pi**:
```bash
sudo raspi-config
# Interface Options > SPI > Enable
# Reboot
```

3. **Install MCP3008 library**:
```bash
pip install Adafruit_MCP3008
```

### Switching to Real Sensor

1. **Update .env**:
```bash
SENSOR_TYPE=mcp3008
```

2. **Calibrate sensors**:
   - Measure known voltage: adjust `VOLTAGE_CALIBRATION_FACTOR`
   - Measure known current: adjust `CURRENT_SENSITIVITY` and `CURRENT_ZERO_OFFSET`

3. **Test readings**:
```python
from sensor import get_sensor
sensor = get_sensor()
voltage, current = sensor.read()
print(f"V: {voltage:.2f}V, I: {current:.2f}A")
```

4. **Restart monitoring**:
```bash
sudo systemctl restart ev-charging-monitor
```

### Establishing Baseline

Before the system can effectively detect anomalies, it needs to learn what "normal" looks like for your specific installation:

1. **Collect normal charging data**:
   - Let system run for 2-4 charging cycles
   - Record stable voltage/current during normal charging

2. **Retrain model** with real data:
```bash
python train_model.py
```

3. **Monitor early behavior**:
   - False positives are expected initially
   - Adjust thresholds as needed in `.env`
   - Fine-tune `CONSECUTIVE_ANOMALIES_FOR_WARNING` and `CONSECUTIVE_ANOMALIES_FOR_CRITICAL`

---

## 🤖 ML Methodology

### Isolation Forest Algorithm

The system uses **Isolation Forest** as the primary anomaly detection algorithm.

**Why Isolation Forest?**
- ✅ Unsupervised learning (no labeled anomaly data needed)
- ✅ Efficient and lightweight (suitable for Raspberry Pi)
- ✅ Anomaly scores are interpretable
- ✅ Works well with 2D feature space (voltage + current)
- ✅ Minimal configuration needed

### Training Process

1. **Feature Engineering**:
   - Features: `[Voltage, Current]`
   - Power is calculated post-prediction: `Power = Voltage × Current`

2. **Training Data**:
   - Generated from simulated normal charging behavior
   - ~200 samples of stable V/I readings
   - Small random noise to represent sensor variability

3. **Model Parameters**:
   - `contamination=0.1`: Expect ~10% anomalies in the wild
   - `n_estimators=100`: Number of isolation trees
   - `random_state=42`: Reproducible results

4. **Model File**:
   - Saved to: `models/anomaly_model.pkl`
   - Size: ~50KB (very portable)
   - Can be retrained anytime with new data

### Prediction Process

For each new reading:

1. **Input**: Voltage and Current values
2. **Isolation Forest**: Calculate anomaly score
   - Score range: -1.0 to 1.0
   - Higher score = more likely to be anomalous
3. **Output**: Binary classification + score
   - `score < ANOMALY_THRESHOLD`: Normal
   - `score >= ANOMALY_THRESHOLD`: Anomaly Detected

### Known Limitations

- ⚠️ ML alone may have false positives/negatives
- ⚠️ Only uses voltage + current (not temperature, time, etc.)
- ⚠️ Requires retraining when hardware characteristics change
- ⚠️ Cannot predict beyond learned distribution

---

## 📈 Early-Warning Methodology

The **Isolation Forest + Trend Analysis + Persistence Layer** provides true early-warning detection:

```
Raw ML Score
    ↓
    ├─→ Is anomalous?
    │
    ├─→ Trend Analysis
    │   ├─ Voltage trend
    │   ├─ Current trend
    │   ├─ Power trend
    │   ├─ Moving average/std
    │   └─ Rate of change
    │
    ├─→ Persistence Check
    │   └─ Consecutive anomaly count
    │
    ↓
Severity: NORMAL / WARNING / CRITICAL
```

### Stages

#### NORMAL
- **Conditions**: 
  - ML prediction is Normal, AND
  - No persistent anomalies, AND
  - No concerning trends
- **Action**: No alert

#### WARNING
- **Conditions**:
  - 3+ consecutive anomalies detected, OR
  - Multiple warning factors (trending up, high variability)
- **Email**: Sent (with cooldown)
- **Action**: Operator should monitor closely

#### CRITICAL
- **Conditions**:
  - 10+ consecutive anomalies detected, OR
  - Severe combination of factors
- **Email**: Sent immediately (with cooldown)
- **Action**: Operator should consider stopping charge

### Trend Analysis Features

The engine analyzes:

1. **Linear Trend** (slope calculation):
   - Voltage trend > 0.02 → Warning factor
   - Current trend > 0.02 → Warning factor
   - Power trend > 0.03 → Warning factor

2. **Volatility**:
   - Voltage std > 1.0V → High variability
   - Current std > 0.8A → High variability

3. **Rate of Change**:
   - Rapid voltage changes > 0.15V/reading
   - Rapid current changes > 0.2A/reading
   - Rapid power changes > 2W/reading

4. **Extreme Values**:
   - Voltage > 15.0V → High voltage alert
   - Current > 12.0A → High current alert

### Consecutive Anomaly Tracking

The system counts consecutive anomalous readings:

```
Reading 1: Anomaly → count = 1
Reading 2: Anomaly → count = 2
Reading 3: Anomaly → count = 3 → WARNING trigger
...
Reading 10: Anomaly → count = 10 → CRITICAL trigger
Reading 11: Normal → count = 0 → Back to NORMAL
```

This prevents false alarms from isolated noisy readings.

---

## 📧 Email Configuration

### Gmail Setup

1. **Enable 2-Factor Authentication**:
   - Go to: https://myaccount.google.com/security
   - Enable 2FA if not already enabled

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select Mail, Windows/Linux/Other
   - Copy the 16-character password

3. **Configure .env**:
```bash
EMAIL_ALERT_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # 16-char app password
ALERT_EMAIL_TO=recipient@example.com
EMAIL_ALERT_COOLDOWN=300
```

### Other Email Providers

Check provider documentation for SMTP settings. Common examples:

**Outlook/Microsoft**:
```
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
```

**Yahoo Mail**:
```
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=465
```

### Email Alert Content

**Warning Email**:
```
Subject: ⚠️ EV Charging Early Warning

Includes:
- Timestamp
- Voltage, Current, Power values
- Anomaly Score
- Alert Reason
- Recommended Actions
```

**Critical Email**:
```
Subject: 🚨 EV Charging Critical Alert

Same information with CRITICAL severity
```

### Email Cooldown

The system prevents email spam with a configurable cooldown:

```
EMAIL_ALERT_COOLDOWN=300  # 5 minutes
```

**Example**:
```
14:00:00 → Anomaly detected → Email sent
14:00:30 → Anomaly continues → Email blocked (cooldown active)
14:01:00 → Anomaly continues → Email blocked
14:04:59 → Anomaly continues → Email blocked
14:05:00 → Anomaly continues → Cooldown expired → Email sent
```

---

## 💾 Cache and Fault Tolerance

### Persistent Cache

The system saves the latest valid reading to `data/latest_cache.json`:

```json
{
  "timestamp": "2026-08-14T14:20:02.123456",
  "voltage": 12.50,
  "current": 8.20,
  "power": 102.50,
  "prediction": "Normal",
  "anomaly_score": -0.8234,
  "severity": "NORMAL",
  "cached_at": "2026-08-14T14:20:02.123456",
  "is_live": true,
  "data_source": "sensor"
}
```

### Atomic Writes

Cache is written atomically using temporary files + rename:

1. Write to temporary file in same directory
2. Atomic rename replaces old cache
3. If write fails, old cache is never corrupted

### Cache Staleness

Cache age is checked when loaded:

```
Age < CACHE_MAX_AGE_SECONDS (default: 300s)
  → is_live = true
  → data_source = "sensor"
  → Dashboard shows: 🟢 LIVE SENSOR DATA

Age > CACHE_MAX_AGE_SECONDS
  → is_live = false
  → data_source = "stale_cache"
  → Dashboard shows: 🟡 STALE / CACHED DATA

No cache at all
  → data_source = "unavailable"
  → Dashboard shows: 🔴 SENSOR DATA UNAVAILABLE
```

### Fault Tolerance Scenarios

#### Scenario 1: Temporary Sensor Failure
```
Sensor OK
  ↓ (Sensor fails)
  ↓ (App catches exception)
Cache loaded + marked STALE
  ↓ (User continues viewing dashboard)
  ↓ (Sensor recovers)
Fresh reading obtained
Cache updated
Dashboard shows LIVE again
```

#### Scenario 2: Application Restart
```
App crashes or restarts
  ↓
App starts up
  ↓
First sensor read
  ↓
(If fails) Load cache
  ↓
Dashboard available with latest data
```

#### Scenario 3: Sustained Sensor Failure
```
Sensor OK
  ↓ (Multiple failed reads)
Cache marked STALE and aged
  ↓
(Time passes, cache becomes too old)
  ↓
Cache not loaded (too stale)
  ↓
Dashboard shows UNAVAILABLE
  ↓
(Sensor restored)
Fresh reading obtained
```

### Cache Statistics API

Endpoint: `GET /api/cache`

Response:
```json
{
  "status": "fresh",
  "has_cache": true,
  "age_seconds": 5,
  "cached_at": "2026-08-14T14:20:02",
  "last_voltage": 12.50,
  "last_current": 8.20,
  "last_severity": "NORMAL"
}
```

---

## 🔄 GitHub Workflow

### Initial Setup (On Development Machine)

1. **Initialize local repository**:
```bash
cd EV_ChargingStation_Monitoring_System
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

2. **Add remote repository**:
```bash
git remote add origin https://github.com/yourusername/EV_ChargingStation_Monitoring_System.git
```

3. **Add and commit files**:
```bash
git add .
git commit -m "Initial commit: Complete EV charging monitoring system"
```

4. **Create and push to main branch**:
```bash
git branch -M main
git push -u origin main
```

### Development Workflow

1. **Create feature branch**:
```bash
git checkout -b feature/new-feature
# Make changes
git add .
git commit -m "Add new feature"
```

2. **Push to GitHub**:
```bash
git push origin feature/new-feature
```

3. **Merge to main**:
```bash
git checkout main
git pull origin main
git merge feature/new-feature
git push origin main
```

### Deployment Workflow (Raspberry Pi)

1. **Pull latest from GitHub**:
```bash
cd ~/EV_ChargingStation_Monitoring_System
git pull origin main
```

2. **Or use update script**:
```bash
./update_project.sh
```

3. **Verify changes**:
```bash
git status
git log --oneline -5
```

### .gitignore

The following files are automatically excluded from Git:

```
.env                      # Credentials (IMPORTANT!)
data/charging_log.csv     # Runtime logs
data/latest_cache.json    # Cache files
models/anomaly_model.pkl  # Trained models
__pycache__/              # Python bytecode
*.pyc, *.pyo              # Python files
.venv/, venv/             # Virtual environments
.DS_Store                 # macOS files
.vscode/, .idea/          # IDE settings
*.log                     # Log files
```

---

## 🍓 Raspberry Pi Deployment

### Prerequisites

- Raspberry Pi 3B or newer
- Raspberry Pi OS (Lite or Desktop)
- Internet connection
- SSH access enabled
- Admin/sudo privileges

### Step-by-Step Deployment

#### 1. Prepare Raspberry Pi

```bash
# SSH into Raspberry Pi
ssh pi@192.168.1.xxx

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git nano
```

#### 2. Clone Repository

```bash
cd ~
git clone https://github.com/yourusername/EV_ChargingStation_Monitoring_System.git
cd EV_ChargingStation_Monitoring_System
```

#### 3. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure System

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
# Set SENSOR_TYPE=mcp3008 if hardware connected
# Set EMAIL_ALERT_ENABLED=True if using email
```

#### 5. Ensure Directories and Data

```bash
python3 config.py

# Create initial model
python3 train_model.py
```

#### 6. Test Locally

```bash
python3 app.py
# Visit http://localhost:5000 from Raspberry Pi
# Press Ctrl+C to stop
```

#### 7. Install as System Service

```bash
# Copy service file
sudo cp ev-charging-monitor.service /etc/systemd/system/

# Update service file path if needed
sudo sed -i 's|/home/pi/EV_ChargingStation_Monitoring_System|~/EV_ChargingStation_Monitoring_System|g' /etc/systemd/system/ev-charging-monitor.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service (starts on boot)
sudo systemctl enable ev-charging-monitor

# Start service
sudo systemctl start ev-charging-monitor

# Check status
sudo systemctl status ev-charging-monitor
```

#### 8. Verify Service

```bash
# Check if running
sudo systemctl is-active ev-charging-monitor

# View logs
sudo journalctl -u ev-charging-monitor -n 50

# Live logs
sudo journalctl -u ev-charging-monitor -f
```

### Service Management Commands

```bash
# Start service
sudo systemctl start ev-charging-monitor

# Stop service
sudo systemctl stop ev-charging-monitor

# Restart service
sudo systemctl restart ev-charging-monitor

# Reload configuration
sudo systemctl reload ev-charging-monitor

# Check status
sudo systemctl status ev-charging-monitor

# View logs (last 50 lines)
sudo journalctl -u ev-charging-monitor -n 50

# Follow logs (live)
sudo journalctl -u ev-charging-monitor -f

# View logs for today
sudo journalctl -u ev-charging-monitor --since today

# Disable autostart
sudo systemctl disable ev-charging-monitor
```

### Updating from GitHub

1. **Using update script**:
```bash
cd ~/EV_ChargingStation_Monitoring_System
./update_project.sh
```

The script will:
- Stop the service
- Pull latest from GitHub
- Update dependencies
- Validate configuration
- Restart service

2. **Manual update**:
```bash
cd ~/EV_ChargingStation_Monitoring_System
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ev-charging-monitor
```

### Remote Access to Dashboard

1. **Find Raspberry Pi IP**:
```bash
hostname -I
# Example: 192.168.1.100
```

2. **Access from laptop**:
   - Open browser: `http://192.168.1.100:5000`

3. **Configure firewall** (if needed):
```bash
sudo ufw allow 5000
```

4. **Production setup** (with reverse proxy):
   - Install nginx
   - Configure as reverse proxy
   - Use SSL certificates
   - Restrict access to local network only

---

## 🧪 Testing

### Run Test Suite

```bash
source venv/bin/activate
python tests/test_system.py
```

### Test Categories

#### 1. Sensor Tests
- ✓ Simulated sensor generates normal data
- ✓ Simulated sensor generates gradual anomalies
- ✓ Simulated sensor generates abrupt anomalies

#### 2. ML Model Tests
- ✓ Model training on normal data
- ✓ Model predictions on normal data
- ✓ Model predictions on anomalous data

#### 3. Cache Tests
- ✓ Save and load cache
- ✓ Atomic writes prevent corruption
- ✓ Staleness detection works correctly
- ✓ Cache survives application restart

#### 4. Early-Warning Tests
- ✓ Normal data generates NORMAL status
- ✓ Persistent anomalies trigger WARNING
- ✓ Severe anomalies trigger CRITICAL
- ✓ Trends detected correctly

#### 5. Email Alert Tests
- ✓ Cooldown mechanism prevents spam
- ✓ Alert formatting is correct
- ✓ Severity levels differentiate

#### 6. Integration Tests
- ✓ Complete monitoring pipeline
- ✓ Sensor → ML → Alert flow
- ✓ Dashboard data consistency

### Manual Testing Scenarios

#### Test 1: Normal Operation (Simulation)
```bash
# Set in .env:
SENSOR_TYPE=simulated
SIMULATION_MODE_NORMAL=stable
EMAIL_ALERT_ENABLED=False

# Run app and verify:
# - Dashboard shows NORMAL
# - Voltage: ~12V, Current: ~7A
# - No emails sent
# - Log file growing
```

#### Test 2: Gradual Anomaly Detection
```bash
# Set in .env:
SIMULATION_MODE_NORMAL=gradual

# Run and observe:
# - First 50 readings: NORMAL
# - Readings 50-80: Trend detected → WARNING
# - Readings 80+: Persistent → CRITICAL
# - Emails sent (if enabled)
```

#### Test 3: Sensor Failure Recovery
```bash
# Set in .env:
SENSOR_TYPE=mcp3008  # (or simulate connection failure)

# Verify:
# - Error logged
# - Cache loaded
# - Dashboard shows STALE DATA
# - No crash
# - When sensor recovered, LIVE again
```

#### Test 4: Cache Persistence
```bash
# Create cache with test data
python cache_manager.py

# Check file exists and is valid JSON:
cat data/latest_cache.json

# Restart app and verify cache loaded:
python app.py
# Check /api/latest shows cached data if sensor fails
```

#### Test 5: Email Alerts
```bash
# Set in .env:
EMAIL_ALERT_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_EMAIL_TO=test@example.com
EMAIL_ALERT_COOLDOWN=10  # Short for testing

# Run with gradual anomaly mode
# First WARNING should send email
# Second WARNING within cooldown should not send
# After cooldown expires, next WARNING should send
```

---

## 🔌 API Endpoints

### GET /api/latest
Get latest sensor readings and status.

**Response**:
```json
{
  "status": "ok",
  "data": {
    "timestamp": "2026-08-14T14:20:02",
    "voltage": 12.50,
    "current": 8.20,
    "power": 102.50,
    "prediction": "Normal",
    "anomaly_score": -0.8234,
    "severity": "NORMAL",
    "reason": "All parameters within normal range",
    "is_live": true,
    "data_source": "sensor",
    "email_alert_sent": false,
    "cache_status": "valid",
    "ml_status": "ok"
  }
}
```

### GET /api/status
Get detailed system status.

**Response**:
```json
{
  "status": "ok",
  "monitoring_service": {
    "running": true,
    "sampling_interval": 2.0
  },
  "latest_state": { ... },
  "cache": {
    "status": "fresh",
    "has_cache": true,
    "age_seconds": 5
  },
  "email": {
    "enabled": true,
    "warning_cooldown_active": false,
    "critical_cooldown_active": false
  },
  "early_warning": {
    "current_severity": "NORMAL",
    "consecutive_anomalies": 0
  }
}
```

### GET /api/history
Get historical readings.

**Query Parameters**:
- `limit`: Max records (default: 100, max: 1000)
- `offset`: Records to skip (default: 0)

**Response**:
```json
{
  "status": "ok",
  "data": [
    {
      "timestamp": "2026-08-14 14:19:02",
      "voltage": "12.48",
      "current": "8.15",
      "power": "101.71",
      "prediction": "Normal",
      "anomaly_score": "-0.8123",
      "severity": "NORMAL",
      "email_alert_sent": "No",
      "data_source": "sensor"
    },
    ...
  ],
  "limit": 100,
  "offset": 0
}
```

### GET /api/statistics
Get aggregated statistics.

**Response**:
```json
{
  "status": "ok",
  "data": {
    "total_readings": 1250,
    "voltage": {
      "avg": 12.32,
      "min": 11.80,
      "max": 14.25,
      "unit": "V"
    },
    "current": {
      "avg": 7.85,
      "min": 6.20,
      "max": 11.50,
      "unit": "A"
    },
    "power": {
      "avg": 96.80,
      "min": 73.40,
      "max": 146.30,
      "unit": "W"
    },
    "alerts": {
      "warnings": 3,
      "criticals": 1,
      "last_anomaly": "2026-08-14 14:15:30"
    }
  }
}
```

### GET /api/cache
Get cache status.

**Response**:
```json
{
  "status": "ok",
  "cache": {
    "status": "fresh",
    "has_cache": true,
    "age_seconds": 12,
    "cached_at": "2026-08-14T14:19:50",
    "last_voltage": 12.50,
    "last_current": 8.20,
    "last_severity": "NORMAL"
  }
}
```

### GET /api/config
Get public configuration (no secrets).

**Response**:
```json
{
  "status": "ok",
  "data": {
    "sensor_type": "simulated",
    "sampling_interval": 2.0,
    "anomaly_threshold": -0.5,
    "warning_threshold": -0.2,
    "critical_threshold": 0.8,
    "consecutive_anomalies_warning": 3,
    "consecutive_anomalies_critical": 10,
    "email_enabled": false,
    "email_cooldown": 300
  }
}
```

---

## 🐛 Troubleshooting

### Issue: Dashboard won't load

**Symptom**: `http://localhost:5000` shows connection refused

**Solutions**:
```bash
# Check if Flask is running
ps aux | grep python

# Check port is listening
netstat -tlnp | grep 5000

# Start Flask manually
python app.py

# Check for port conflicts
sudo lsof -i :5000
```

### Issue: Sensor reads are all zeros

**Symptom**: API shows voltage=0, current=0

**Solutions**:
```bash
# Check sensor configuration in .env
cat .env | grep SENSOR_TYPE

# If mcp3008, test manually
from sensor import get_sensor
sensor = get_sensor()
v, i = sensor.read()
print(f"V: {v}, I: {i}")

# If simulated, verify it's working
python -c "from sensor import SimulatedSensor; s = SimulatedSensor(); print(s.read())"

# Check MCP3008 library is installed (if needed)
python -c "import Adafruit_MCP3008"
```

### Issue: ML model missing

**Symptom**: `FileNotFoundError: models/anomaly_model.pkl`

**Solutions**:
```bash
# Train model
python train_model.py

# Verify file exists
ls -l models/anomaly_model.pkl

# Check permissions
chmod 644 models/anomaly_model.pkl
```

### Issue: Emails not sending

**Symptom**: Email alerts not working despite `EMAIL_ALERT_ENABLED=True`

**Solutions**:
```bash
# Verify email config
grep EMAIL .env

# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your_email@gmail.com', 'your_app_password')
print('Success!')
"

# Check service logs
sudo journalctl -u ev-charging-monitor | grep -i email

# Verify app password (not regular password) for Gmail
# Go to: https://myaccount.google.com/apppasswords
```

### Issue: Service won't start

**Symptom**: `sudo systemctl start ev-charging-monitor` fails

**Solutions**:
```bash
# Check service status
sudo systemctl status ev-charging-monitor

# View error logs
sudo journalctl -u ev-charging-monitor -n 50

# Verify service file exists
ls -l /etc/systemd/system/ev-charging-monitor.service

# Check Python path in service file
grep ExecStart /etc/systemd/system/ev-charging-monitor.service

# Verify virtual environment path exists
ls -l ~/EV_ChargingStation_Monitoring_System/venv/bin/python

# Test app manually
source ~/EV_ChargingStation_Monitoring_System/venv/bin/activate
cd ~/EV_ChargingStation_Monitoring_System
python app.py
```

### Issue: Cache file corrupted

**Symptom**: "JSON decode error" when loading cache

**Solutions**:
```bash
# Check cache file
cat data/latest_cache.json

# If corrupted, delete it
rm data/latest_cache.json

# Restart app to regenerate
python app.py

# Verify new cache is valid JSON
python -c "import json; json.load(open('data/latest_cache.json'))"
```

### Issue: High CPU usage

**Symptom**: Raspberry Pi running hot, high CPU %

**Solutions**:
```bash
# Check what's using CPU
top -b -n 1 | head -20

# Increase sampling interval in .env
SAMPLING_INTERVAL=5.0

# Reduce trend window size
TREND_WINDOW_SIZE=5

# Reduce history limit in dashboard
# Edit templates/index.html, change HISTORY_LIMIT
```

### Issue: Disk space filling up

**Symptom**: Raspberry Pi runs out of disk space

**Solutions**:
```bash
# Check disk usage
df -h

# See what's taking space
du -sh *

# Rotate/compress logs
gzip data/charging_log.csv

# Remove old cache
rm data/latest_cache.json

# Clear old logs
rm data/*.log

# Consider reducing log level
# Set LOG_LEVEL=WARNING in .env
```

---

## 📌 Limitations

### Current Limitations

1. **No Temperature Monitoring**: System doesn't monitor battery/charger temperature
2. **No Time-Series Forecasting**: Uses snapshot analysis, not time-series predictions
3. **2D Feature Space**: Only uses Voltage + Current (not Power directly in ML)
4. **No Predictive Maintenance**: Cannot predict component failures
5. **Limited Historical Analysis**: No seasonality or pattern learning over months
6. **No Automatic Control**: Cannot cut power (manual intervention required)
7. **Single Charging Station**: Designed for one station (not multi-site management)
8. **Local Dashboard Only**: No cloud integration or remote monitoring
9. **No Battery Chemistry Support**: Same model for all battery types
10. **Calibration Required**: Needs manual sensor calibration per installation

### Hardware Limitations (Raspberry Pi)

- Limited processing power (CPU: ARM 32/64-bit)
- Limited memory (1-4GB typical)
- Single-threaded core bottleneck (shared with GPIO)
- USB bandwidth limitations
- Thermal constraints in enclosures

### Software Limitations

- Python (not as performant as C/Rust)
- SQLite instead of full database
- No data replication or clustering
- Single process (not load-balanced)
- Basic web interface (not mobile-optimized)

---

## 🚀 Future Improvements

### Phase 2: Enhanced Detection
- [ ] Multi-feature ML (add temperature, humidity)
- [ ] LSTM neural network for time-series forecasting
- [ ] Ensemble methods combining multiple algorithms
- [ ] Bayesian anomaly detection
- [ ] Real-time model retraining with online learning

### Phase 3: Automation
- [ ] Automatic relay control for power cutoff
- [ ] GPIO-based notification lights
- [ ] Buzzer/beeper for audible alerts
- [ ] SMS/Telegram alerts in addition to email
- [ ] Slack/Discord webhook integrations

### Phase 4: Intelligence
- [ ] Battery chemistry detection and per-type models
- [ ] Learning from multiple charging cycles
- [ ] Predictive maintenance scheduling
- [ ] Cost optimization (off-peak charging)
- [ ] Multi-charger coordination

### Phase 5: Cloud Integration
- [ ] Cloud data synchronization
- [ ] Mobile app (iOS/Android)
- [ ] Web-based remote dashboard
- [ ] Multi-site management portal
- [ ] Analytics and reporting dashboards

### Phase 6: Advanced Features
- [ ] Blockchain for audit logging
- [ ] Integration with EV telematics
- [ ] Vehicle-specific charging profiles
- [ ] Driver behavior analysis
- [ ] Predictive ETA-based charging

---

## 📝 License

This project is provided as-is for educational and research purposes.

## 👥 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make changes with clear commit messages
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues, questions, or suggestions:
- GitHub Issues: [Report a bug](https://github.com/yourusername/EV_ChargingStation_Monitoring_System/issues)
- Email: your.email@example.com
- Documentation: This README + inline code comments

---

## ⚖️ Disclaimer

**This system is for monitoring and early-warning purposes only.**

- ⚠️ NOT a replacement for professional battery management systems
- ⚠️ Cannot guarantee prevention of battery damage
- ⚠️ Requires human judgment for decisions
- ⚠️ Should not be used as sole safety mechanism
- ⚠️ Always follow manufacturer guidelines for charging

**Use at your own risk. The developers are not responsible for any damage to equipment or data.**

---

## 📚 References

- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08.pdf)
- [scikit-learn Documentation](https://scikit-learn.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Raspberry Pi GPIO Documentation](https://www.raspberrypi.org/documentation/)
- [MCP3008 Datasheet](https://www.microchip.com/en-us/product/MCP3008)

---

**Last Updated**: 2026-08-14  
**Version**: 1.0.0  
**Status**: Production Ready
