"""
Logging system for EV Charging Station Monitoring System.
Handles both console and file logging.
"""
import logging
import logging.handlers
import os
from config import Config


class LoggerSetup:
    """Configure logging for the application."""
    
    _logger = None
    _csv_file = None
    
    @classmethod
    def get_logger(cls, name='ev_charging'):
        """Get or create logger instance."""
        if cls._logger is None:
            cls._logger = logging.getLogger(name)
            cls._logger.setLevel(Config.LOG_LEVEL)
            
            # Create formatters
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(Config.LOG_LEVEL)
            console_handler.setFormatter(formatter)
            cls._logger.addHandler(console_handler)
            
            # File handler
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                os.path.join(Config.LOG_DIR, 'app.log'),
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(Config.LOG_LEVEL)
            file_handler.setFormatter(formatter)
            cls._logger.addHandler(file_handler)
        
        return cls._logger
    
    @classmethod
    def log_sensor_reading(cls, timestamp, voltage, current, power, prediction,
                          anomaly_score, severity, email_sent, data_source):
        """Log sensor reading to CSV file."""
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        
        # Create CSV header if file doesn't exist
        if not os.path.exists(Config.LOG_FILE):
            with open(Config.LOG_FILE, 'w') as f:
                f.write('timestamp,voltage,current,power,prediction,anomaly_score,severity,email_alert_sent,data_source\n')
        
        # Append reading
        with open(Config.LOG_FILE, 'a') as f:
            f.write(f'{timestamp},{voltage:.2f},{current:.2f},{power:.2f},{prediction},{anomaly_score:.4f},{severity},{email_sent},{data_source}\n')


# Convenience function
def get_logger(name='ev_charging'):
    """Get logger instance."""
    return LoggerSetup.get_logger(name)


if __name__ == '__main__':
    logger = get_logger()
    logger.info("Logger initialized successfully")
