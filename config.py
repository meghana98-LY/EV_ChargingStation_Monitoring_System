"""
Configuration management for EV Charging Station Monitoring System.
Centralizes all configurable parameters from environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""
    
    # Sensor Configuration
    SENSOR_TYPE = os.getenv('SENSOR_TYPE', 'simulated')  # 'simulated' or 'mcp3008'
    SAMPLING_INTERVAL = float(os.getenv('SAMPLING_INTERVAL', '2.0'))  # seconds
    
    # ADC and Sensor Calibration
    ADC_REFERENCE_VOLTAGE = float(os.getenv('ADC_REFERENCE_VOLTAGE', '3.3'))  # volts
    VOLTAGE_CALIBRATION_FACTOR = float(os.getenv('VOLTAGE_CALIBRATION_FACTOR', '1.0'))
    CURRENT_ZERO_OFFSET = float(os.getenv('CURRENT_ZERO_OFFSET', '0.0'))  # amps
    CURRENT_SENSITIVITY = float(os.getenv('CURRENT_SENSITIVITY', '1.0'))  # amps per volt
    
    # MCP3008 ADC Configuration
    MCP3008_CHANNEL_VOLTAGE = int(os.getenv('MCP3008_CHANNEL_VOLTAGE', '0'))
    MCP3008_CHANNEL_CURRENT = int(os.getenv('MCP3008_CHANNEL_CURRENT', '1'))
    
    # ML Model Configuration
    ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', 'models/anomaly_model.pkl')
    ANOMALY_THRESHOLD = float(os.getenv('ANOMALY_THRESHOLD', '-0.5'))  # Isolation Forest threshold
    
    # Early Warning Thresholds
    WARNING_THRESHOLD = float(os.getenv('WARNING_THRESHOLD', '-0.2'))
    CRITICAL_THRESHOLD = float(os.getenv('CRITICAL_THRESHOLD', '0.8'))
    CONSECUTIVE_ANOMALIES_FOR_WARNING = int(os.getenv('CONSECUTIVE_ANOMALIES_FOR_WARNING', '3'))
    CONSECUTIVE_ANOMALIES_FOR_CRITICAL = int(os.getenv('CONSECUTIVE_ANOMALIES_FOR_CRITICAL', '10'))
    
    # Trend Analysis Window
    TREND_WINDOW_SIZE = int(os.getenv('TREND_WINDOW_SIZE', '10'))  # number of readings
    
    # Cache Configuration
    CACHE_DIR = os.getenv('CACHE_DIR', 'data')
    CACHE_FILE = os.path.join(CACHE_DIR, 'latest_cache.json')
    CACHE_MAX_AGE_SECONDS = float(os.getenv('CACHE_MAX_AGE_SECONDS', '300.0'))
    
    # Data Logging
    LOG_DIR = os.getenv('LOG_DIR', 'data')
    LOG_FILE = os.path.join(LOG_DIR, 'charging_log.csv')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Email Alert Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    ALERT_EMAIL_FROM = os.getenv('ALERT_EMAIL_FROM', '')
    ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO', '')
    EMAIL_ALERT_ENABLED = os.getenv('EMAIL_ALERT_ENABLED', 'False').lower() == 'true'
    EMAIL_ALERT_COOLDOWN = float(os.getenv('EMAIL_ALERT_COOLDOWN', '300.0'))  # seconds
    
    # Flask Configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Simulation Configuration (for testing without hardware)
    SIMULATION_MODE_NORMAL = os.getenv('SIMULATION_MODE_NORMAL', 'stable')  # 'stable', 'gradual', 'abrupt'
    SIMULATION_VOLTAGE_BASE = float(os.getenv('SIMULATION_VOLTAGE_BASE', '12.0'))
    SIMULATION_CURRENT_BASE = float(os.getenv('SIMULATION_CURRENT_BASE', '7.0'))
    SIMULATION_NOISE_LEVEL = float(os.getenv('SIMULATION_NOISE_LEVEL', '0.1'))
    
    @staticmethod
    def ensure_directories():
        """Ensure required directories exist."""
        os.makedirs(Config.CACHE_DIR, exist_ok=True)
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        os.makedirs('models', exist_ok=True)
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static', exist_ok=True)


if __name__ == '__main__':
    # Print configuration for debugging
    Config.ensure_directories()
    print("Configuration loaded successfully")
    print(f"Sensor Type: {Config.SENSOR_TYPE}")
    print(f"Sampling Interval: {Config.SAMPLING_INTERVAL}s")
    print(f"Email Alerts Enabled: {Config.EMAIL_ALERT_ENABLED}")
