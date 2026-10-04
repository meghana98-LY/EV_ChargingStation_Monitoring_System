# IoT-Based Smart EV Charging Station Monitoring and Intelligent Anomaly Detection

This project implements a smart EV charging station prototype that continuously monitors charging conditions, distinguishes vehicle presence from idle states, detects abnormal behavior, and cuts power safely when unsafe or suspicious conditions occur.

It is designed around a Raspberry Pi 4 and an MCP3008 ADC, with live monitoring, anomaly detection, relay protection, a web dashboard, and email alerting for operational safety.

## Project overview

The system monitors:
- vehicle presence using an HC-SR04 ultrasonic sensor
- DC charging voltage using an analog voltage-sensing circuit
- current using an ACS712 current sensor when calibrated and enabled
- real power derived from voltage and current
- relay state that controls the charging output

The monitoring loop evaluates each reading using a trained Isolation Forest model to detect abnormal charging conditions. If a fault, unsafe condition, or anomaly is detected, the relay is immediately switched off and the event is logged.

## Key features

- Real-time charging monitoring dashboard
- Analytics view for recent readings and events
- Vehicle detection and idle-state handling
- Automatic relay shutdown on anomaly or unsafe conditions
- Isolation Forest-based anomaly detection
- Email notifications for anomaly events
- Persistent event and sensor logging
- Model training workflow using measured normal charging data
- Hardware-safe operation defaults for prototype testing

## System architecture

The project is organized into these main areas:

- `backend/app.py` — Flask application and REST endpoints
- `backend/monitor.py` — main monitoring loop and state management
- `backend/sensor.py` — sensor aggregation and snapshot creation
- `backend/relay_controller.py` — relay control logic
- `backend/services/protection.py` — safety evaluation and lockout behavior
- `backend/services/email_alert.py` — anomaly email alerts
- `backend/ml/anomaly_detector.py` — runtime anomaly classifier
- `backend/ml/train_model.py` — training pipeline for the Isolation Forest model
- `backend/database/` — database storage support for sensor and protection events
- `backend/templates/` and `backend/static/` — web dashboard and analytics UI
- `data/training/charging_data.csv` — sample training dataset

## Hardware components

- Raspberry Pi 4
- MCP3008 ADC for analog voltage/current sampling
- Voltage sensing circuit for 0–25 V input range
- ACS712 current sensor (optional; disabled by default until safely conditioned)
- HC-SR04 ultrasonic sensor for vehicle detection
- Relay module for charging control
- Power supply and protection circuitry appropriate for lab/prototype use

## Software stack

- Python 3
- Flask
- NumPy and Pandas
- scikit-learn
- Isolation Forest model from scikit-learn
- joblib for model persistence
- python-dotenv for environment configuration
- gpiozero / spidev for Raspberry Pi hardware access
- pytest for automated validation

## Installation

1. Clone the repository
2. Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Enable SPI on the Raspberry Pi:

```bash
sudo raspi-config
```

Then enable the SPI interface from the Raspberry Pi configuration menu.

## Configuration

Set up the project environment before running the monitor.

```bash
# edit the root .env file
nano .env
```

The project reads settings such as:
- `HARDWARE_MODE`
- `CURRENT_SENSOR_ENABLED`
- `RELAY_GPIO`
- `RELAY_ACTIVE_HIGH`
- `VEHICLE_DISTANCE_THRESHOLD_CM`
- `ADC_VOLTAGE_CHANNEL`
- `ADC_CURRENT_CHANNEL`
- `VOLTAGE_CALIBRATION_FACTOR`
- `ACS712_SENSITIVITY`
- `ACS712_ZERO_OFFSET`
- `EMAIL_ENABLED`
- `SENDER_EMAIL`
- `SENDER_PASSWORD`
- `ALERT_EMAIL`

## Training the anomaly model

The Isolation Forest model should be trained on representative normal charging data. Replace the default example dataset with your own measured data when available, then run:

```bash
python -m backend.ml.train_model
```

This produces the serialized model used by the live monitor.

## Running the application

Start the monitor and Flask dashboard:

```bash
python -m backend.app
```

Open the following pages in a browser:
- Dashboard: `http://<PI-IP>:5000/dashboard`
- Analytics: `http://<PI-IP>:5000/analytics`

API endpoints include:
- `GET /api/monitor`
- `GET /api/status`
- `GET /api/history`
- `GET /api/anomalies`
- `GET /api/protection`
- `POST /api/reset-protection`

## Safety and protection model

This system is designed for safe prototype operation. The relay is forced off in the following conditions:
- no vehicle is detected
- a sensor error occurs
- current data is unavailable when required
- an anomaly is detected
- the protection lockout is active
- shutdown is triggered

Important safety notes:
- The ACS712 current channel is intentionally disabled by default until the analog signal is safely conditioned and calibrated.
- `CURRENT_SENSOR_ENABLED=false` should remain active until the circuit and calibration are verified.
- `HARDWARE_MODE` should be set to `false` for software-only testing when no real sensors are connected.
- The relay is never left energized during startup or when the system is in a fault state.

## Email alerts

To enable email notifications, configure the SMTP credentials in `.env` and set:

```bash
EMAIL_ENABLED=true
```

Use a Gmail App Password and not a normal Gmail password. The project is designed to prevent repeated alert spam using a cooldown timer.

## Testing

The repository includes pytest-based validation for anomaly detection and protection logic. Test mode avoids real hardware interaction.

```bash
pytest
```

## Project structure

```text
EV_ChargingStation_Monitoring_System/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── monitor.py
│   ├── sensor.py
│   ├── relay_controller.py
│   ├── database/
│   ├── hardware/
│   ├── ml/
│   ├── services/
│   ├── static/
│   ├── templates/
│   └── tests/
├── data/
│   ├── logs/
│   └── training/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── .venv/
```

## Current status

This is a functional prototype for EV charging safety monitoring, anomaly detection, and protection logic. It is especially useful for student projects, research prototypes, and lab validation where live sensing, intelligent fault detection, and safe relay control are required.

## Future enhancements

- add a more complete database layer for historical analytics
- improve sensor calibration and signal conditioning
- add a richer UI with charts and event timeline
- integrate OTA updates or remote monitoring
- extend anomaly detection with additional charging profiles and edge-case scenarios
