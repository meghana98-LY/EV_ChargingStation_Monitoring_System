# IoT-Based Smart EV Charging Station Monitoring and Intelligent Anomaly Detection

Raspberry Pi 4 prototype using MCP3008, 0-25V voltage sensing, ACS712 current sensing, HC-SR04 vehicle/load detection, relay protection, Isolation Forest, SQLite, Flask dashboard and SMTP email alerts.

## Current hardware status
ACS712 OUT -> MCP3008 CH1 is intentionally disabled until safe signal conditioning is installed. Keep `CURRENT_SENSOR_ENABLED=false` until then. Hardware mode never fabricates current values.

## Install
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo raspi-config
```
Enable SPI in Raspberry Pi configuration.

## Configure
```bash
cp .env.example .env
nano .env
```

## Train model
Replace the supplied small example CSV with measured normal charging data, then:
```bash
python -m backend.ml.train_model
```

## Run
```bash
python -m backend.app
```
Dashboard: `http://<PI-IP>:5000/dashboard`
Analytics: `http://<PI-IP>:5000/analytics`

## Email
Use a Gmail App Password, never a normal Gmail password. Configure `.env`:
`EMAIL_ENABLED=true`, sender, app password and `ALERT_EMAIL`.

## Safety
Relay is forced OFF on startup, no vehicle, sensor error, anomaly, protection trip and shutdown. Tests use no real hardware.
