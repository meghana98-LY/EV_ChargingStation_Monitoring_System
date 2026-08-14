"""
Central monitoring service for continuous sensor monitoring.
Runs the complete data pipeline:
Read sensor → Validate → Calculate power → Run ML → Trend analysis → Alert
"""
import threading
import time
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from config import Config
from logger import get_logger, LoggerSetup
from sensor import get_sensor, SensorException
from ml_model import get_model
from early_warning import get_early_warning_engine
from cache_manager import get_cache_manager
from email_alert import get_email_system

logger = get_logger('monitor')


class MonitoringService:
    """
    Central monitoring service that runs the complete charging station monitoring pipeline.
    Thread-safe with locking for shared state access.
    """
    
    def __init__(self):
        """Initialize monitoring service."""
        self.running = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        # Latest state (thread-safe, protected by lock)
        self.latest_state = {
            'timestamp': None,
            'voltage': 0.0,
            'current': 0.0,
            'power': 0.0,
            'prediction': 'Unknown',
            'anomaly_score': 0.0,
            'severity': 'UNKNOWN',
            'reason': 'Not initialized',
            'is_live': False,
            'data_source': 'unavailable',
            'email_alert_sent': False,
            'cache_status': 'unavailable',
            'ml_status': 'unknown'
        }
        
        # Configuration
        self.sampling_interval = Config.SAMPLING_INTERVAL
        self.cache_manager = get_cache_manager()
        self.email_system = get_email_system()
        self.early_warning = get_early_warning_engine()
        
        logger.info("Monitoring service initialized")
    
    def start(self):
        """Start the monitoring service."""
        if self.running:
            logger.warning("Monitoring service already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitoring service started")
    
    def stop(self):
        """Stop the monitoring service."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Monitoring service stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop (runs in separate thread)."""
        logger.info("Monitoring loop started")
        
        while self.running:
            try:
                # Read sensor data
                voltage, current, power, is_live = self._read_sensor()
                
                if not is_live:
                    # Sensor failed, will use cached data
                    time.sleep(self.sampling_interval)
                    continue
                
                # Run ML prediction
                prediction, anomaly_score, ml_ok = self._run_ml(voltage, current)
                
                # Run early-warning analysis
                severity, reason = self._analyze_severity(
                    voltage, current, power, anomaly_score, prediction
                )
                
                # Determine if anomaly
                is_anomaly = prediction == 'Anomaly Detected'
                
                # Update cache
                email_sent = False
                if ml_ok:
                    self._update_cache(
                        voltage, current, power, prediction,
                        anomaly_score, severity
                    )
                    
                    # Send alert if needed
                    if severity in ['WARNING', 'CRITICAL']:
                        email_sent = self._send_alert(
                            severity, voltage, current, power,
                            anomaly_score, reason
                        )
                
                # Log reading
                self._log_reading(
                    voltage, current, power, prediction,
                    anomaly_score, severity, email_sent, 'sensor'
                )
                
                # Update latest state
                with self.lock:
                    self.latest_state = {
                        'timestamp': datetime.now().isoformat(),
                        'voltage': round(voltage, 2),
                        'current': round(current, 2),
                        'power': round(power, 2),
                        'prediction': prediction,
                        'anomaly_score': round(anomaly_score, 4),
                        'severity': severity,
                        'reason': reason,
                        'is_live': True,
                        'data_source': 'sensor',
                        'email_alert_sent': email_sent,
                        'cache_status': 'valid',
                        'ml_status': 'ok' if ml_ok else 'error'
                    }
                
                logger.debug(
                    f"Monitoring cycle: {severity} | V:{voltage:.2f}V "
                    f"I:{current:.2f}A P:{power:.2f}W | "
                    f"Score:{anomaly_score:.4f} | Email:{email_sent}"
                )
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}\n{traceback.format_exc()}")
                self._handle_monitoring_error()
            
            # Sleep before next cycle
            time.sleep(self.sampling_interval)
        
        logger.info("Monitoring loop stopped")
    
    def _read_sensor(self) -> tuple:
        """
        Read sensor data with fault tolerance.
        
        Returns:
            Tuple of (voltage, current, power, is_live)
        """
        try:
            sensor = get_sensor()
            voltage, current = sensor.read()
            power = voltage * current
            
            return voltage, current, power, True
        
        except SensorException as e:
            logger.warning(f"Sensor read failed: {str(e)}")
            
            # Load cached data
            cache = self.cache_manager.load_cache()
            if cache:
                logger.info("Using cached sensor data")
                with self.lock:
                    self.latest_state = {
                        'timestamp': cache.get('timestamp'),
                        'voltage': cache.get('voltage', 0.0),
                        'current': cache.get('current', 0.0),
                        'power': cache.get('power', 0.0),
                        'prediction': cache.get('prediction'),
                        'anomaly_score': cache.get('anomaly_score', 0.0),
                        'severity': cache.get('severity'),
                        'reason': 'Using cached data - sensor unavailable',
                        'is_live': False,
                        'data_source': 'stale_cache',
                        'email_alert_sent': False,
                        'cache_status': 'stale',
                        'ml_status': 'unavailable'
                    }
                return 0, 0, 0, False
            else:
                logger.error("No cache available and sensor failed")
                with self.lock:
                    self.latest_state = {
                        'timestamp': datetime.now().isoformat(),
                        'voltage': 0.0,
                        'current': 0.0,
                        'power': 0.0,
                        'prediction': 'Unknown',
                        'anomaly_score': 0.0,
                        'severity': 'UNKNOWN',
                        'reason': 'Sensor data unavailable and no cache',
                        'is_live': False,
                        'data_source': 'unavailable',
                        'email_alert_sent': False,
                        'cache_status': 'unavailable',
                        'ml_status': 'unavailable'
                    }
                return 0, 0, 0, False
    
    def _run_ml(self, voltage: float, current: float) -> tuple:
        """
        Run ML anomaly detection.
        
        Returns:
            Tuple of (prediction, anomaly_score, is_ok)
        """
        try:
            model = get_model()
            prediction, anomaly_score = model.predict(voltage, current)
            return prediction, anomaly_score, True
        except Exception as e:
            logger.error(f"ML prediction failed: {str(e)}")
            return 'Unknown', 0.0, False
    
    def _analyze_severity(self, voltage: float, current: float, power: float,
                         anomaly_score: float, prediction: str) -> tuple:
        """
        Run early-warning analysis to determine severity.
        
        Returns:
            Tuple of (severity, reason)
        """
        try:
            is_anomaly = prediction == 'Anomaly Detected'
            severity, reason = self.early_warning.analyze(
                voltage, current, power, anomaly_score, is_anomaly
            )
            return severity, reason
        except Exception as e:
            logger.error(f"Early-warning analysis failed: {str(e)}")
            return 'UNKNOWN', f'Analysis error: {str(e)}'
    
    def _update_cache(self, voltage: float, current: float, power: float,
                     prediction: str, anomaly_score: float, severity: str):
        """Update persistent cache with latest reading."""
        try:
            self.cache_manager.save_reading(
                timestamp=datetime.now().isoformat(),
                voltage=voltage,
                current=current,
                power=power,
                prediction=prediction,
                anomaly_score=anomaly_score,
                severity=severity
            )
        except Exception as e:
            logger.error(f"Failed to update cache: {str(e)}")
    
    def _send_alert(self, severity: str, voltage: float, current: float,
                   power: float, anomaly_score: float, reason: str) -> bool:
        """
        Send email alert if configured and cooldown permits.
        
        Returns:
            True if email was sent, False otherwise
        """
        try:
            return self.email_system.send_alert(
                severity=severity,
                timestamp=datetime.now().isoformat(),
                voltage=voltage,
                current=current,
                power=power,
                anomaly_score=anomaly_score,
                reason=reason
            )
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
            return False
    
    def _log_reading(self, voltage: float, current: float, power: float,
                    prediction: str, anomaly_score: float, severity: str,
                    email_sent: bool, data_source: str):
        """Log sensor reading to CSV."""
        try:
            LoggerSetup.log_sensor_reading(
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                voltage=voltage,
                current=current,
                power=power,
                prediction=prediction,
                anomaly_score=anomaly_score,
                severity=severity,
                email_sent='Yes' if email_sent else 'No',
                data_source=data_source
            )
        except Exception as e:
            logger.error(f"Failed to log reading: {str(e)}")
    
    def _handle_monitoring_error(self):
        """Handle errors in monitoring loop."""
        # Try to load cached state
        cache = self.cache_manager.load_cache()
        if cache:
            with self.lock:
                self.latest_state = {
                    'timestamp': cache.get('timestamp'),
                    'voltage': cache.get('voltage', 0.0),
                    'current': cache.get('current', 0.0),
                    'power': cache.get('power', 0.0),
                    'prediction': cache.get('prediction'),
                    'anomaly_score': cache.get('anomaly_score', 0.0),
                    'severity': cache.get('severity'),
                    'reason': 'Error in monitoring loop - using cache',
                    'is_live': False,
                    'data_source': 'error_cache',
                    'email_alert_sent': False,
                    'cache_status': 'fallback',
                    'ml_status': 'error'
                }
    
    def get_latest_state(self) -> Dict[str, Any]:
        """
        Get latest monitoring state (thread-safe).
        
        Returns:
            Dictionary with latest sensor and analysis state
        """
        with self.lock:
            return self.latest_state.copy()
    
    def get_status(self) -> dict:
        """Get monitoring service status."""
        return {
            'running': self.running,
            'sampling_interval': self.sampling_interval,
            'latest_state': self.get_latest_state(),
            'cache_status': self.cache_manager.get_cache_status(),
            'email_cooldown': self.email_system.get_cooldown_status(),
            'early_warning': self.early_warning.get_status()
        }


# Global monitoring service instance
_monitor = None


def get_monitor() -> MonitoringService:
    """Get or create global monitoring service instance."""
    global _monitor
    if _monitor is None:
        _monitor = MonitoringService()
    return _monitor


if __name__ == '__main__':
    # Example usage
    Config.ensure_directories()
    
    monitor = get_monitor()
    monitor.start()
    
    try:
        logger.info("Monitoring service running. Press Ctrl+C to stop.")
        while True:
            time.sleep(5)
            status = monitor.get_status()
            print(f"\nLatest state: {status['latest_state']}")
    except KeyboardInterrupt:
        logger.info("Stopping monitoring service...")
        monitor.stop()
