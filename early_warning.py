"""
Early-warning engine combining Isolation Forest with trend and persistence analysis.
Determines severity level: NORMAL, WARNING, or CRITICAL.
"""
from collections import deque
from typing import Tuple, List
from datetime import datetime
from config import Config
from logger import get_logger

logger = get_logger('early_warning')


class EarlyWarningEngine:
    """
    Combines ML anomaly detection with trend and persistence analysis
    to provide early warnings before critical failures.
    """
    
    def __init__(self):
        """Initialize early-warning engine."""
        self.history_size = Config.TREND_WINDOW_SIZE
        
        # Store history of readings
        self.voltage_history = deque(maxlen=self.history_size)
        self.current_history = deque(maxlen=self.history_size)
        self.power_history = deque(maxlen=self.history_size)
        self.anomaly_score_history = deque(maxlen=self.history_size)
        self.is_anomaly_history = deque(maxlen=self.history_size)
        
        # Thresholds
        self.consecutive_anomalies_warning = Config.CONSECUTIVE_ANOMALIES_FOR_WARNING
        self.consecutive_anomalies_critical = Config.CONSECUTIVE_ANOMALIES_FOR_CRITICAL
        
        # State tracking
        self.consecutive_anomaly_count = 0
        self.current_severity = 'NORMAL'
    
    def analyze(self, voltage: float, current: float, power: float,
                anomaly_score: float, is_anomaly: bool) -> Tuple[str, str]:
        """
        Analyze sensor data and determine severity level.
        
        Args:
            voltage: Voltage reading in volts
            current: Current reading in amps
            power: Power reading in watts
            anomaly_score: Anomaly score from ML model (-1.0 to 1.0)
            is_anomaly: Boolean indicating if ML detected anomaly
        
        Returns:
            Tuple of (severity, reason)
            severity: 'NORMAL', 'WARNING', or 'CRITICAL'
            reason: Explanation of the severity determination
        """
        # Update history
        self.voltage_history.append(voltage)
        self.current_history.append(current)
        self.power_history.append(power)
        self.anomaly_score_history.append(anomaly_score)
        self.is_anomaly_history.append(is_anomaly)
        
        # Track consecutive anomalies
        if is_anomaly:
            self.consecutive_anomaly_count += 1
        else:
            self.consecutive_anomaly_count = 0
        
        # Determine severity
        severity, reason = self._determine_severity()
        self.current_severity = severity
        
        return severity, reason
    
    def _determine_severity(self) -> Tuple[str, str]:
        """
        Determine severity based on multiple factors.
        
        Returns:
            Tuple of (severity, reason)
        """
        # Insufficient data
        if len(self.voltage_history) < 2:
            return 'NORMAL', 'Insufficient data for trend analysis'
        
        # Check for critical conditions
        if self.consecutive_anomaly_count >= self.consecutive_anomalies_critical:
            reason = (
                f'Critical: {self.consecutive_anomaly_count} consecutive anomalies detected. '
                f'Threshold: {self.consecutive_anomalies_critical}'
            )
            return 'CRITICAL', reason
        
        # Check for warning conditions
        if self.consecutive_anomaly_count >= self.consecutive_anomalies_warning:
            # Additional trend check
            trend_severity, trend_reason = self._analyze_trend()
            if trend_severity != 'NORMAL':
                reason = f'Warning: {trend_reason}. Anomaly count: {self.consecutive_anomaly_count}/{self.consecutive_anomalies_warning}'
                return 'WARNING', reason
            else:
                reason = (
                    f'Warning: {self.consecutive_anomaly_count} consecutive anomalies. '
                    f'Threshold: {self.consecutive_anomalies_warning}'
                )
                return 'WARNING', reason
        
        # Check for trend-based warnings
        trend_severity, trend_reason = self._analyze_trend()
        if trend_severity == 'WARNING':
            return 'WARNING', trend_reason
        
        # Normal condition
        return 'NORMAL', 'All parameters within normal range'
    
    def _analyze_trend(self) -> Tuple[str, str]:
        """
        Analyze voltage, current, and power trends.
        
        Returns:
            Tuple of (severity, reason)
        """
        if len(self.voltage_history) < 3:
            return 'NORMAL', 'Insufficient data for trend'
        
        # Calculate statistics
        voltage_trend = self._calculate_trend(list(self.voltage_history))
        current_trend = self._calculate_trend(list(self.current_history))
        power_trend = self._calculate_trend(list(self.power_history))
        
        # Calculate moving statistics
        voltage_mv_avg = self._moving_average(list(self.voltage_history))
        current_mv_avg = self._moving_average(list(self.current_history))
        voltage_mv_std = self._moving_std(list(self.voltage_history))
        current_mv_std = self._moving_std(list(self.current_history))
        
        # Analyze rate of change
        voltage_rate = self._rate_of_change(list(self.voltage_history))
        current_rate = self._rate_of_change(list(self.current_history))
        power_rate = self._rate_of_change(list(self.power_history))
        
        # Criteria for warning
        severity_factors = []
        
        # Strong positive trends
        if voltage_trend > 0.02 and len(self.voltage_history) > 5:
            severity_factors.append(f'Voltage increasing: {voltage_trend:.4f}')
        
        if current_trend > 0.02 and len(self.current_history) > 5:
            severity_factors.append(f'Current increasing: {current_trend:.4f}')
        
        if power_trend > 0.03 and len(self.power_history) > 5:
            severity_factors.append(f'Power increasing: {power_trend:.4f}')
        
        # High variability (suggests instability)
        if voltage_mv_std > 1.0:
            severity_factors.append(f'High voltage variability (σ={voltage_mv_std:.2f}V)')
        
        if current_mv_std > 0.8:
            severity_factors.append(f'High current variability (σ={current_mv_std:.2f}A)')
        
        # Rapid rate of change
        if abs(voltage_rate) > 0.15:
            severity_factors.append(f'Rapid voltage change: {voltage_rate:.3f}V/reading')
        
        if abs(current_rate) > 0.2:
            severity_factors.append(f'Rapid current change: {current_rate:.3f}A/reading')
        
        if abs(power_rate) > 2.0:
            severity_factors.append(f'Rapid power change: {power_rate:.3f}W/reading')
        
        # Extreme values
        latest_voltage = self.voltage_history[-1]
        latest_current = self.current_history[-1]
        
        if latest_voltage > 15.0:
            severity_factors.append(f'High voltage: {latest_voltage:.2f}V')
        
        if latest_current > 12.0:
            severity_factors.append(f'High current: {latest_current:.2f}A')
        
        # Determine if warning conditions are met
        if len(severity_factors) >= 2:
            reason = 'Multiple warning factors: ' + '; '.join(severity_factors[:2])
            return 'WARNING', reason
        
        if len(severity_factors) >= 1 and self.consecutive_anomaly_count > 0:
            reason = severity_factors[0]
            return 'WARNING', reason
        
        return 'NORMAL', ''
    
    @staticmethod
    def _calculate_trend(values: List[float]) -> float:
        """
        Calculate linear trend (slope) of values.
        Positive = increasing, Negative = decreasing.
        """
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope
    
    @staticmethod
    def _moving_average(values: List[float]) -> float:
        """Calculate simple moving average."""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    @staticmethod
    def _moving_std(values: List[float]) -> float:
        """Calculate moving standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    @staticmethod
    def _rate_of_change(values: List[float]) -> float:
        """Calculate average rate of change between consecutive readings."""
        if len(values) < 2:
            return 0.0
        
        # Average delta between consecutive readings
        deltas = [values[i] - values[i-1] for i in range(1, len(values))]
        return sum(deltas) / len(deltas)
    
    def get_status(self) -> dict:
        """Get early-warning engine status."""
        return {
            'current_severity': self.current_severity,
            'consecutive_anomalies': self.consecutive_anomaly_count,
            'warning_threshold': self.consecutive_anomalies_warning,
            'critical_threshold': self.consecutive_anomalies_critical,
            'history_size': len(self.voltage_history),
            'max_history_size': self.history_size
        }
    
    def reset(self):
        """Reset engine state."""
        self.voltage_history.clear()
        self.current_history.clear()
        self.power_history.clear()
        self.anomaly_score_history.clear()
        self.is_anomaly_history.clear()
        self.consecutive_anomaly_count = 0
        self.current_severity = 'NORMAL'
        logger.info("Early-warning engine reset")


# Global instance
_engine = None


def get_early_warning_engine() -> EarlyWarningEngine:
    """Get or create global early-warning engine instance."""
    global _engine
    if _engine is None:
        _engine = EarlyWarningEngine()
    return _engine


if __name__ == '__main__':
    engine = get_early_warning_engine()
    
    # Simulate gradual anomaly
    print("Simulating normal readings...")
    for i in range(5):
        severity, reason = engine.analyze(12.0, 7.0, 84.0, -0.8, False)
        print(f"  Reading {i+1}: {severity} - {reason}")
    
    print("\nSimulating anomaly onset...")
    for i in range(15):
        severity, reason = engine.analyze(13.5, 9.0, 121.5, -0.3, True)
        print(f"  Reading {i+1}: {severity} - {reason}")
    
    print(f"\nEngine status: {engine.get_status()}")
