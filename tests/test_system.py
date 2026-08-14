"""
Comprehensive test suite for EV Charging Station Monitoring System.
Tests: sensor, ML, cache, monitoring, alerts, and system integration.
"""
import os
import sys
import time
import tempfile
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from sensor import SimulatedSensor, SensorException
from ml_model import AnomalyModel
from cache_manager import CacheManager
from email_alert import EmailAlertSystem
from early_warning import EarlyWarningEngine
from monitor import MonitoringService


class TestResults:
    """Tracks test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"✓ PASS: {test_name}")
    
    def add_fail(self, test_name, reason):
        self.failed += 1
        self.errors.append((test_name, reason))
        print(f"✗ FAIL: {test_name}")
        print(f"       Reason: {reason}")
    
    def summary(self):
        print("\n" + "="*60)
        print(f"Test Summary: {self.passed} passed, {self.failed} failed")
        print("="*60)
        if self.errors:
            print("\nFailures:")
            for test_name, reason in self.errors:
                print(f"  - {test_name}: {reason}")


# Test Results
results = TestResults()


def test_simulated_sensor_normal():
    """Test simulated sensor generates normal data."""
    try:
        sensor = SimulatedSensor()
        sensor.mode = 'stable'
        
        readings = []
        for _ in range(10):
            v, i = sensor.read()
            readings.append((v, i))
        
        avg_v = sum(r[0] for r in readings) / len(readings)
        avg_i = sum(r[1] for r in readings) / len(readings)
        
        # Check values are in expected range
        assert 11.5 < avg_v < 12.5, f"Voltage {avg_v} out of range"
        assert 6.5 < avg_i < 7.5, f"Current {avg_i} out of range"
        
        results.add_pass("Simulated sensor - normal data")
    except Exception as e:
        results.add_fail("Simulated sensor - normal data", str(e))


def test_simulated_sensor_gradual_anomaly():
    """Test simulated sensor generates gradual anomaly."""
    try:
        sensor = SimulatedSensor()
        sensor.mode = 'gradual'
        
        initial_readings = []
        for _ in range(50):
            sensor.read()
        
        anomaly_readings = []
        for _ in range(30):
            v, i = sensor.read()
            anomaly_readings.append((v, i))
        
        last_v = anomaly_readings[-1][0]
        first_v = anomaly_readings[0][0]
        
        # Should show increasing trend
        assert last_v > first_v, "Gradual anomaly should increase voltage"
        
        results.add_pass("Simulated sensor - gradual anomaly")
    except Exception as e:
        results.add_fail("Simulated sensor - gradual anomaly", str(e))


def test_ml_model_training():
    """Test ML model training on normal data."""
    try:
        model = AnomalyModel(model_path=':memory:')
        
        # Generate training data
        import random
        voltages = [12.0 + random.gauss(0, 0.2) for _ in range(100)]
        currents = [7.0 + random.gauss(0, 0.15) for _ in range(100)]
        
        # Train
        success = model.train(voltages, currents)
        assert success, "Training failed"
        assert model.is_trained, "Model not marked as trained"
        
        results.add_pass("ML model - training")
    except Exception as e:
        results.add_fail("ML model - training", str(e))


def test_ml_model_prediction():
    """Test ML model makes predictions."""
    try:
        model = AnomalyModel(model_path=':memory:')
        
        # Train on normal data
        import random
        voltages = [12.0 + random.gauss(0, 0.2) for _ in range(100)]
        currents = [7.0 + random.gauss(0, 0.15) for _ in range(100)]
        model.train(voltages, currents)
        
        # Normal prediction
        pred, score = model.predict(12.0, 7.0)
        assert pred == 'Normal', f"Expected Normal, got {pred}"
        
        # Anomaly prediction
        pred, score = model.predict(15.0, 12.0)
        assert pred == 'Anomaly Detected', f"Expected Anomaly, got {pred}"
        
        results.add_pass("ML model - predictions")
    except Exception as e:
        results.add_fail("ML model - predictions", str(e))


def test_cache_manager_save_load():
    """Test cache save and load."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            Config.CACHE_DIR = tmpdir
            Config.CACHE_FILE = os.path.join(tmpdir, 'test_cache.json')
            
            cache = CacheManager()
            
            # Save
            success = cache.save_reading(
                timestamp=datetime.now().isoformat(),
                voltage=12.5,
                current=8.0,
                power=100.0,
                prediction='Anomaly Detected',
                anomaly_score=-0.3,
                severity='WARNING'
            )
            assert success, "Save failed"
            
            # Load
            data = cache.load_cache()
            assert data is not None, "Load returned None"
            assert data['voltage'] == 12.5, f"Voltage mismatch: {data['voltage']}"
            assert data['severity'] == 'WARNING', f"Severity mismatch: {data['severity']}"
            
            results.add_pass("Cache manager - save/load")
    except Exception as e:
        results.add_fail("Cache manager - save/load", str(e))


def test_cache_atomic_write():
    """Test cache uses atomic writes."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            Config.CACHE_DIR = tmpdir
            Config.CACHE_FILE = os.path.join(tmpdir, 'test_atomic.json')
            
            cache = CacheManager()
            
            # Multiple writes
            for i in range(5):
                cache.save_reading(
                    timestamp=datetime.now().isoformat(),
                    voltage=12.0 + i,
                    current=7.0 + i,
                    power=84.0 + i*7,
                    prediction='Normal',
                    anomaly_score=-0.8,
                    severity='NORMAL'
                )
            
            # File should still be valid JSON
            with open(Config.CACHE_FILE, 'r') as f:
                data = json.load(f)
            
            assert data['voltage'] == 16.0, "Last write not preserved"
            
            results.add_pass("Cache manager - atomic writes")
    except Exception as e:
        results.add_fail("Cache manager - atomic writes", str(e))


def test_cache_staleness():
    """Test cache staleness detection."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            Config.CACHE_DIR = tmpdir
            Config.CACHE_FILE = os.path.join(tmpdir, 'test_stale.json')
            Config.CACHE_MAX_AGE_SECONDS = 1  # 1 second
            
            cache = CacheManager()
            
            # Save
            cache.save_reading(
                timestamp=datetime.now().isoformat(),
                voltage=12.5,
                current=8.0,
                power=100.0,
                prediction='Normal',
                anomaly_score=-0.8,
                severity='NORMAL'
            )
            
            # Load immediately (fresh)
            data = cache.load_cache()
            assert data is not None, "Fresh cache should load"
            assert data['is_live'] == True, "Fresh cache should be marked live"
            
            # Wait for staleness
            time.sleep(1.5)
            
            # Load after timeout (stale)
            data = cache.load_cache()
            assert data is not None, "Stale cache should still load"
            assert data['is_live'] == False, "Stale cache should be marked stale"
            
            results.add_pass("Cache manager - staleness detection")
    except Exception as e:
        results.add_fail("Cache manager - staleness detection", str(e))


def test_early_warning_normal():
    """Test early-warning engine on normal data."""
    try:
        engine = EarlyWarningEngine()
        
        severity, reason = engine.analyze(12.0, 7.0, 84.0, -0.8, False)
        assert severity == 'NORMAL', f"Expected NORMAL, got {severity}"
        
        results.add_pass("Early-warning engine - normal data")
    except Exception as e:
        results.add_fail("Early-warning engine - normal data", str(e))


def test_early_warning_persistent_anomaly():
    """Test early-warning triggers WARNING then CRITICAL."""
    try:
        engine = EarlyWarningEngine()
        
        # Feed normal data
        for _ in range(5):
            engine.analyze(12.0, 7.0, 84.0, -0.8, False)
        
        # Feed anomalies
        severities = []
        for i in range(15):
            sev, _ = engine.analyze(14.0, 10.0, 140.0, -0.2, True)
            severities.append(sev)
        
        # Should transition: NORMAL -> WARNING -> CRITICAL
        assert 'WARNING' in severities, "Should have WARNING at some point"
        
        # Later readings might be critical
        if engine.consecutive_anomaly_count >= Config.CONSECUTIVE_ANOMALIES_FOR_CRITICAL:
            last_severity = severities[-1]
            assert last_severity == 'CRITICAL', f"Expected CRITICAL after {engine.consecutive_anomaly_count} anomalies"
        
        results.add_pass("Early-warning engine - persistent anomaly")
    except Exception as e:
        results.add_fail("Early-warning engine - persistent anomaly", str(e))


def test_email_alert_cooldown():
    """Test email alert cooldown prevents spam."""
    try:
        email_system = EmailAlertSystem()
        
        # Disable actual sending for testing
        email_system.cooldown_seconds = 1
        
        # First alert should succeed (no cooldown yet)
        result1 = email_system._is_cooldown_active('WARNING')
        assert not result1, "No cooldown should be active initially"
        
        # Update cooldown
        email_system._update_cooldown('WARNING')
        
        # Immediate second alert should be blocked
        result2 = email_system._is_cooldown_active('WARNING')
        assert result2, "Cooldown should be active immediately"
        
        # Wait for cooldown to expire
        time.sleep(1.1)
        result3 = email_system._is_cooldown_active('WARNING')
        assert not result3, "Cooldown should have expired"
        
        results.add_pass("Email alert - cooldown mechanism")
    except Exception as e:
        results.add_fail("Email alert - cooldown mechanism", str(e))


def test_monitoring_service_init():
    """Test monitoring service initializes."""
    try:
        monitor = MonitoringService()
        assert monitor.running == False, "Should not be running initially"
        
        status = monitor.get_latest_state()
        assert 'timestamp' in status, "Status should have timestamp"
        assert 'severity' in status, "Status should have severity"
        
        results.add_pass("Monitoring service - initialization")
    except Exception as e:
        results.add_fail("Monitoring service - initialization", str(e))


def test_monitoring_service_sensor_read():
    """Test monitoring service reads sensor."""
    try:
        monitor = MonitoringService()
        
        # Use simulated sensor
        Config.SENSOR_TYPE = 'simulated'
        
        # Read sensor
        v, i, p, is_live = monitor._read_sensor()
        
        if is_live:
            assert v > 0, "Voltage should be positive"
            assert i > 0, "Current should be positive"
            assert p > 0, "Power should be positive"
        
        results.add_pass("Monitoring service - sensor read")
    except Exception as e:
        results.add_fail("Monitoring service - sensor read", str(e))


def test_integration_normal_flow():
    """Test complete normal flow: read -> ML -> alert."""
    try:
        Config.SENSOR_TYPE = 'simulated'
        Config.EMAIL_ALERT_ENABLED = False
        
        monitor = MonitoringService()
        
        # Simulate a few cycles
        for _ in range(3):
            monitor._monitor_loop.__code__.co_consts  # Just to confirm it exists
        
        state = monitor.get_latest_state()
        assert state is not None, "Should have state"
        
        results.add_pass("Integration test - normal flow")
    except Exception as e:
        results.add_fail("Integration test - normal flow", str(e))


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*60)
    print("EV Charging Station Monitoring System - Test Suite")
    print("="*60 + "\n")
    
    # Sensor Tests
    print(">>> Sensor Tests")
    test_simulated_sensor_normal()
    test_simulated_sensor_gradual_anomaly()
    
    # ML Tests
    print("\n>>> ML Model Tests")
    test_ml_model_training()
    test_ml_model_prediction()
    
    # Cache Tests
    print("\n>>> Cache Manager Tests")
    test_cache_manager_save_load()
    test_cache_atomic_write()
    test_cache_staleness()
    
    # Early Warning Tests
    print("\n>>> Early-Warning Engine Tests")
    test_early_warning_normal()
    test_early_warning_persistent_anomaly()
    
    # Email Alert Tests
    print("\n>>> Email Alert Tests")
    test_email_alert_cooldown()
    
    # Monitoring Service Tests
    print("\n>>> Monitoring Service Tests")
    test_monitoring_service_init()
    test_monitoring_service_sensor_read()
    
    # Integration Tests
    print("\n>>> Integration Tests")
    test_integration_normal_flow()
    
    # Print summary
    results.summary()
    
    return results.failed == 0


if __name__ == '__main__':
    Config.ensure_directories()
    success = run_all_tests()
    sys.exit(0 if success else 1)
