#!/bin/bash
# EV Charging Station Monitoring System - Update and Deployment Script
# Run this on Raspberry Pi to safely update from GitHub
# Usage: ./update_project.sh

set -e  # Exit on any error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="ev-charging-monitor"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}EV Charging Station - Update Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Step 1: Check if running on Raspberry Pi
echo -e "\n${YELLOW}[1/6]${NC} Checking environment..."
if ! grep -qi "raspberry" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}Warning: This may not be running on Raspberry Pi${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled"
        exit 1
    fi
fi

# Step 2: Stop the monitoring service
echo -e "\n${YELLOW}[2/6]${NC} Stopping monitoring service..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "Stopping $SERVICE_NAME service..."
    sudo systemctl stop $SERVICE_NAME
    echo "Service stopped"
else
    echo "Service not running (this is okay)"
fi

# Step 3: Pull latest from GitHub
echo -e "\n${YELLOW}[3/6]${NC} Pulling latest code from GitHub..."
cd "$PROJECT_DIR"
if ! git pull; then
    echo -e "${RED}Git pull failed! Restoring service...${NC}"
    sudo systemctl start $SERVICE_NAME || true
    exit 1
fi
echo "Code updated successfully"

# Step 4: Install/update dependencies
echo -e "\n${YELLOW}[4/6]${NC} Checking dependencies..."
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing/updating dependencies..."
pip install -q -r requirements.txt
echo "Dependencies installed"

# Step 5: Validate configuration
echo -e "\n${YELLOW}[5/6]${NC} Validating configuration..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please copy .env.example to .env and fill in your configuration"
    echo "Example: cp .env.example .env"
    exit 1
fi

echo "Configuration validated"

# Step 6: Restart service
echo -e "\n${YELLOW}[6/6]${NC} Restarting monitoring service..."
if sudo systemctl is-enabled $SERVICE_NAME >/dev/null 2>&1; then
    echo "Starting $SERVICE_NAME service..."
    sudo systemctl start $SERVICE_NAME
    
    # Wait a moment and check status
    sleep 2
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✓ Service started successfully${NC}"
    else
        echo -e "${RED}✗ Service failed to start${NC}"
        echo "Check service status: sudo systemctl status $SERVICE_NAME"
        echo "View logs: sudo journalctl -u $SERVICE_NAME -n 50"
        exit 1
    fi
else
    echo "Service not installed as systemd service"
    echo "To run manually: python app.py"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Update completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Dashboard available at: http://localhost:5000"
echo "View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "Check status: sudo systemctl status $SERVICE_NAME"
