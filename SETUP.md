# Setup Guide - Exact Commands for All Environments

This guide provides step-by-step commands to set up the EV Charging Station Monitoring System on different platforms.

## Quick Start (Development - Windows/Mac/Linux)

### Prerequisites
- Python 3.7 or higher
- Git
- 200 MB free disk space
- Terminal/Command Prompt

### Commands

```bash
# 1. Clone repository (replace YOUR_USERNAME with your GitHub username)
git clone https://github.com/YOUR_USERNAME/EV_ChargingStation_Monitoring_System.git
cd EV_ChargingStation_Monitoring_System

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Create environment configuration
cp .env.example .env

# 6. Ensure directories exist
python config.py

# 7. Train ML model (one-time)
python train_model.py

# 8. Run the application
python app.py

# 9. Open dashboard
# Visit: http://localhost:5000 in your browser
```

Done! Dashboard should be available at `http://localhost:5000`

---

## GitHub Setup (One-Time: Initialize Repository)

### If you're starting from scratch and need to push to GitHub:

```bash
# 1. Create empty repository on GitHub
# Go to https://github.com/new
# Name: EV_ChargingStation_Monitoring_System
# Do NOT initialize with README
# Click Create Repository

# 2. Initialize local repository
cd ~/EV_ChargingStation_Monitoring_System
git init

# 3. Configure Git (one-time)
git config user.name "Your Full Name"
git config user.email "your.email@github.com"

# 4. Add remote (replace YOURUSERNAME)
git remote add origin https://github.com/YOURUSERNAME/EV_ChargingStation_Monitoring_System.git

# 5. Add all files
git add .

# 6. Initial commit
git commit -m "Initial commit: Complete EV charging monitoring system with Isolation Forest ML"

# 7. Create main branch and push
git branch -M main
git push -u origin main

# 8. Verify
git log --oneline
git remote -v
```

### After Initial Setup: Normal Development Workflow

```bash
# 1. Make changes to code...

# 2. Check what changed
git status

# 3. Stage changes
git add .

# 4. Commit changes
git commit -m "Brief description of changes"

# 5. Push to GitHub
git push origin main

# 6. Pull latest from GitHub (if working with others)
git pull origin main
```

---

## Raspberry Pi Deployment

### Prerequisites
- Raspberry Pi 3B or newer with Raspberry Pi OS installed
- Micro-USB power supply
- Ethernet or WiFi connection
- SSH access enabled
- User account with sudo privileges (default: pi)

### Complete Deployment Commands

```bash
# ============================================
# STEP 1: Prepare Raspberry Pi
# ============================================

# SSH into your Raspberry Pi
ssh pi@192.168.1.100  # Replace with your Pi's IP

# Update system packages
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git nano

# Enable SPI (for MCP3008 ADC - if using real sensors)
sudo raspi-config
# Navigate: Interface Options > SPI > Enable > Finish

# Reboot if SPI was enabled
sudo reboot


# ============================================
# STEP 2: Clone Repository
# ============================================

# Navigate to home directory
cd ~

# Clone the project
git clone https://github.com/YOURUSERNAME/EV_ChargingStation_Monitoring_System.git
cd EV_ChargingStation_Monitoring_System

# Create directories
mkdir -p data models


# ============================================
# STEP 3: Python Environment
# ============================================

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# For real MCP3008 hardware (optional):
pip install Adafruit_MCP3008


# ============================================
# STEP 4: Configuration
# ============================================

# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env

# Key settings to check/modify:
# - SENSOR_TYPE: Set to 'simulated' or 'mcp3008'
# - FLASK_HOST: 0.0.0.0 (to access from other machines)
# - FLASK_PORT: 5000
# - EMAIL_ALERT_ENABLED: True/False
# - If email enabled: Fill SMTP settings with Gmail or other provider
# - MCP3008_CHANNEL_VOLTAGE: ADC channel for voltage (usually 0)
# - MCP3008_CHANNEL_CURRENT: ADC channel for current (usually 1)

# Exit nano: Ctrl+X, then Y, then Enter


# ============================================
# STEP 5: Initialize System
# ============================================

# Ensure directories exist
python3 config.py

# Train ML model
python3 train_model.py

# Test the application (optional)
python3 app.py
# Visit http://192.168.1.100:5000 from another machine
# Press Ctrl+C to stop


# ============================================
# STEP 6: Install as System Service
# ============================================

# Copy service file
sudo cp ev-charging-monitor.service /etc/systemd/system/

# Update file permissions
sudo chmod 644 /etc/systemd/system/ev-charging-monitor.service

# Update the service file with correct paths
sudo sed -i "s|/home/pi/|$HOME/|g" /etc/systemd/system/ev-charging-monitor.service

# Alternative: Edit manually if paths are different
sudo nano /etc/systemd/system/ev-charging-monitor.service
# Make sure WorkingDirectory and ExecStart point to correct paths
# Save: Ctrl+X, Y, Enter

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable ev-charging-monitor

# Start the service
sudo systemctl start ev-charging-monitor

# Check service status
sudo systemctl status ev-charging-monitor

# If service failed, check logs
sudo journalctl -u ev-charging-monitor -n 50


# ============================================
# STEP 7: Verify Installation
# ============================================

# Check service is running
sudo systemctl is-active ev-charging-monitor
# Should output: active

# Check from another machine
# Open browser: http://192.168.1.100:5000
# Should see dashboard with live data

# View live logs
sudo journalctl -u ev-charging-monitor -f
# Press Ctrl+C to exit logs


# ============================================
# STEP 8: Useful Commands (Ongoing)
# ============================================

# Start/stop service
sudo systemctl start ev-charging-monitor
sudo systemctl stop ev-charging-monitor
sudo systemctl restart ev-charging-monitor

# Check status
sudo systemctl status ev-charging-monitor

# View logs
sudo journalctl -u ev-charging-monitor -n 50        # Last 50 lines
sudo journalctl -u ev-charging-monitor -f           # Live follow
sudo journalctl -u ev-charging-monitor --since today  # Today's logs
sudo journalctl -u ev-charging-monitor -p err       # Errors only

# Update from GitHub
cd ~/EV_ChargingStation_Monitoring_System
./update_project.sh
# Or manually:
# git pull origin main
# source venv/bin/activate
# pip install -r requirements.txt
# sudo systemctl restart ev-charging-monitor

# Check disk usage
df -h
du -sh ~/EV_ChargingStation_Monitoring_System

# Monitor system resources
top
# Press Q to exit

# Network test (ping)
ping github.com
```

---

## Email Configuration (Gmail Example)

```bash
# 1. Enable 2-Factor Authentication on Gmail
# Visit: https://myaccount.google.com/security
# Click 2-Step Verification, follow instructions

# 2. Generate App Password
# Visit: https://myaccount.google.com/apppasswords
# Select: Mail, Windows/Linux/Other
# Copy the 16-character password

# 3. Edit .env file
nano .env

# 4. Fill in email settings:
EMAIL_ALERT_ENABLED=True
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
ALERT_EMAIL_FROM=your.email@gmail.com
ALERT_EMAIL_TO=recipient@example.com
EMAIL_ALERT_COOLDOWN=300

# 5. Restart service
sudo systemctl restart ev-charging-monitor

# 6. Trigger an alert to test (set to gradual anomaly mode)
# SIMULATION_MODE_NORMAL=gradual
# Check if email arrives
```

---

## Testing Commands

```bash
# Run complete test suite
source venv/bin/activate
python tests/test_system.py

# Test sensor directly
python -c "from sensor import get_sensor; s = get_sensor(); print(s.read())"

# Test ML model
python -c "from ml_model import get_model; m = get_model(); print(m.get_status())"

# Test cache
python -c "from cache_manager import get_cache_manager; c = get_cache_manager(); print(c.get_cache_status())"

# Test API endpoints
curl http://localhost:5000/api/latest
curl http://localhost:5000/api/status
curl http://localhost:5000/api/statistics
```

---

## Troubleshooting Commands

```bash
# Check if service is running
sudo systemctl is-active ev-charging-monitor

# Detailed service status
sudo systemctl status ev-charging-monitor

# Service logs (last 100 lines)
sudo journalctl -u ev-charging-monitor -n 100

# Real-time logs
sudo journalctl -u ev-charging-monitor -f

# Check if port 5000 is listening
sudo lsof -i :5000
netstat -tlnp | grep 5000

# Check Python processes
ps aux | grep python
ps aux | grep app.py

# Check disk space
df -h
df -i

# Check memory usage
free -h
top -b -n 1 | head -20

# Check network connectivity
ping 8.8.8.8
curl https://github.com

# Verify SSH access
ssh -v pi@192.168.1.100

# Check Raspberry Pi temperature
vcgencmd measure_temp

# Check CPU usage
mpstat 1 5
```

---

## Git Commands Reference

```bash
# Configuration
git config user.name "Your Name"
git config user.email "your@email.com"
git config --list                          # View all config

# Repository
git init                                    # Initialize new repo
git clone https://github.com/...            # Clone repo
git remote -v                               # View remotes
git remote add origin https://github.com/.. # Add remote

# Status and Changes
git status                                  # See changes
git diff                                    # See differences
git log --oneline                           # See commit history
git log --oneline -n 10                     # Last 10 commits

# Staging and Committing
git add .                                   # Stage all changes
git add file.py                             # Stage specific file
git commit -m "Message"                     # Commit with message
git commit -am "Message"                    # Stage and commit tracked files

# Branching
git branch                                  # List branches
git branch feature-name                     # Create branch
git checkout feature-name                   # Switch branch
git checkout -b feature-name                # Create and switch
git branch -d feature-name                  # Delete branch

# Merging
git merge feature-name                      # Merge branch into current
git merge --no-ff feature-name              # Merge without fast-forward

# Pushing and Pulling
git push origin main                        # Push to GitHub
git push origin feature-name                # Push feature branch
git pull origin main                        # Pull latest changes
git fetch origin                            # Fetch without merging

# Undoing Changes
git restore file.py                         # Discard changes
git restore --staged file.py                # Unstage file
git reset HEAD~1                            # Undo last commit (keep changes)
git reset --hard HEAD~1                     # Undo last commit (discard changes)

# Tags (for releases)
git tag v1.0.0                              # Create tag
git push origin v1.0.0                      # Push tag
git tag -l                                  # List tags
```

---

## Environment Variables Reference

```bash
# Sensor Configuration
SENSOR_TYPE=simulated                       # simulated or mcp3008
SAMPLING_INTERVAL=2.0                       # Seconds

# Calibration
ADC_REFERENCE_VOLTAGE=3.3
VOLTAGE_CALIBRATION_FACTOR=1.0
CURRENT_ZERO_OFFSET=0.0
CURRENT_SENSITIVITY=1.0

# MCP3008 Channels
MCP3008_CHANNEL_VOLTAGE=0
MCP3008_CHANNEL_CURRENT=1

# ML Parameters
ML_MODEL_PATH=models/anomaly_model.pkl
ANOMALY_THRESHOLD=-0.5
WARNING_THRESHOLD=-0.2
CRITICAL_THRESHOLD=0.8
CONSECUTIVE_ANOMALIES_FOR_WARNING=3
CONSECUTIVE_ANOMALIES_FOR_CRITICAL=10

# Trend Analysis
TREND_WINDOW_SIZE=10

# Cache
CACHE_DIR=data
CACHE_MAX_AGE_SECONDS=300.0

# Logging
LOG_DIR=data
LOG_LEVEL=INFO

# Email
EMAIL_ALERT_ENABLED=False
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=
EMAIL_ALERT_COOLDOWN=300.0

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# Simulation
SIMULATION_MODE_NORMAL=stable
SIMULATION_VOLTAGE_BASE=12.0
SIMULATION_CURRENT_BASE=7.0
SIMULATION_NOISE_LEVEL=0.1
```

---

## File Locations Reference

```
~/ or %USERPROFILE% on Windows
├── EV_ChargingStation_Monitoring_System/
│   ├── .env                              (Sensitive - gitignored)
│   ├── app.py                            (Main Flask app)
│   ├── config.py                         (Configuration)
│   ├── sensor.py                         (Sensor abstraction)
│   ├── monitor.py                        (Central monitor)
│   ├── ml_model.py                       (ML model)
│   ├── early_warning.py                  (Early warning engine)
│   ├── cache_manager.py                  (Cache management)
│   ├── email_alert.py                    (Email alerts)
│   ├── logger.py                         (Logging)
│   ├── train_model.py                    (Model training)
│   ├── data/
│   │   ├── charging_log.csv              (Runtime - gitignored)
│   │   └── latest_cache.json             (Runtime - gitignored)
│   ├── models/
│   │   └── anomaly_model.pkl             (Trained model)
│   ├── templates/
│   │   ├── index.html                    (Dashboard)
│   │   └── graph.html                    (Graphs)
│   ├── static/
│   │   └── style.css                     (Styling)
│   ├── tests/
│   │   └── test_system.py                (Tests)
│   ├── venv/                             (Virtual environment)
│   └── requirements.txt                  (Dependencies)
```

---

## Port Forwarding (For Remote Access)

### On Raspberry Pi

```bash
# Check if service is accessible locally
curl http://localhost:5000

# Get Raspberry Pi IP
hostname -I

# From another machine on same network
curl http://192.168.1.100:5000  # Replace IP
```

### Using ngrok (Temporary Public URL)

```bash
# Download ngrok from https://ngrok.com
# Or on Linux:
sudo apt install ngrok

# Expose local port
ngrok http 5000

# This gives you a public URL like:
# https://xxxx-xx-xxx-xxx-xx.ngrok.io

# Use this to access dashboard from anywhere
# (Expires when ngrok disconnects)
```

### Using Nginx Reverse Proxy (Production)

```bash
# Install nginx
sudo apt install -y nginx

# Edit nginx config
sudo nano /etc/nginx/sites-available/default

# Replace server block with:
server {
    listen 80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Test config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Now access from http://192.168.1.100:80 (port 80 is default)
```

---

## Monitoring and Logs

```bash
# Real-time monitoring
watch -n 2 'sudo systemctl status ev-charging-monitor'
watch -n 2 'df -h'
watch -n 2 'free -h'

# Log analysis
sudo journalctl -u ev-charging-monitor --since today
sudo journalctl -u ev-charging-monitor --until today
sudo journalctl -u ev-charging-monitor | grep -i error
sudo journalctl -u ev-charging-monitor | grep -i warning
sudo journalctl -u ev-charging-monitor | tail -f

# Application logs (CSV)
tail -f ~/EV_ChargingStation_Monitoring_System/data/charging_log.csv
wc -l ~/EV_ChargingStation_Monitoring_System/data/charging_log.csv

# Disk usage
du -sh ~/EV_ChargingStation_Monitoring_System/*
du -sh ~/EV_ChargingStation_Monitoring_System/data/
```

---

## Useful Shortcuts

```bash
# Quick start on Raspberry Pi
cd ~/EV_ChargingStation_Monitoring_System
source venv/bin/activate
python3 app.py

# Quick logs
sl  # Show logs (alias - add to ~/.bashrc)
alias sl='sudo journalctl -u ev-charging-monitor -f'

# Quick restart
alias restart-ev='sudo systemctl restart ev-charging-monitor'

# Quick status
alias status-ev='sudo systemctl status ev-charging-monitor'
```

Add to `~/.bashrc`:
```bash
alias restart-ev='sudo systemctl restart ev-charging-monitor'
alias status-ev='sudo systemctl status ev-charging-monitor'
alias logs-ev='sudo journalctl -u ev-charging-monitor -f'
```

Then: `source ~/.bashrc`

---

## Database Cleanup

```bash
# Archive old log data
cd ~/EV_ChargingStation_Monitoring_System/data
gzip charging_log.csv -o charging_log_backup_$(date +%Y%m%d).csv.gz

# Reset log file (fresh start)
rm data/charging_log.csv

# Clear cache
rm data/latest_cache.json

# Retrain model
python3 train_model.py

# Restart service
sudo systemctl restart ev-charging-monitor
```

---

**For more detailed information, see README.md**
