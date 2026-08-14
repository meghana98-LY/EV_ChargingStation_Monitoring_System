"""
Sensor abstraction layer.
Supports both simulated sensor data and real MCP3008 ADC sensor data.
"""
import random
import time
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from config import Config
from logger import get_logger

logger = get_logger('sensor')


class SensorInterface(ABC):
    """Abstract base class for sensor implementations."""
    
    @abstractmethod
    def read(self) -> Tuple[float, float]:
        """
        Read sensor values.
        
        Returns:
            Tuple of (voltage, current) in volts and amps respectively
        
        Raises:
            SensorException on read failure
        """
        pass
    
    @abstractmethod
    def get_status(self) -> str:
        """Get sensor status."""
        pass


class SensorException(Exception):
    """Exception raised by sensor operations."""
    pass


class SimulatedSensor(SensorInterface):
    """
    Simulated sensor for testing without hardware.
    Can generate normal, gradually abnormal, or abruptly abnormal patterns.
    """
    
    def __init__(self):
        """Initialize simulated sensor."""
        self.base_voltage = Config.SIMULATION_VOLTAGE_BASE
        self.base_current = Config.SIMULATION_CURRENT_BASE
        self.noise_level = Config.SIMULATION_NOISE_LEVEL
        self.mode = Config.SIMULATION_MODE_NORMAL  # 'stable', 'gradual', 'abrupt'
        self.read_count = 0
        self.anomaly_start_count = 50  # Start anomaly after 50 reads
        logger.info(f"Simulated sensor initialized (mode: {self.mode})")
    
    def read(self) -> Tuple[float, float]:
        """
        Read simulated sensor data.
        
        Returns:
            Tuple of (voltage, current)
        """
        try:
            self.read_count += 1
            
            # Base values with noise
            noise_v = random.gauss(0, self.noise_level)
            noise_i = random.gauss(0, self.noise_level * 0.5)
            
            voltage = self.base_voltage + noise_v
            current = self.base_current + noise_i
            
            # Apply anomaly patterns based on mode
            if self.mode == 'fail':
                raise SensorException("Simulated hardware failure triggered for testing cache fallback")
            
            elif self.mode == 'gradual':
                if self.read_count > self.anomaly_start_count:
                    progression = min((self.read_count - self.anomaly_start_count) / 40.0, 1.0)
                    voltage += progression * 3.5  # Up to +3.5V
                    current += progression * 5.5  # Up to +5.5A
            
            elif self.mode == 'abrupt':
                if self.read_count >= self.anomaly_start_count:
                    voltage += 3.8
                    current += 6.5
            
            # Clamp to realistic ranges
            voltage = max(10.0, min(18.0, voltage))
            current = max(0.0, min(25.0, current))
            
            return (voltage, current)
        
        except SensorException:
            raise
        except Exception as e:
            logger.error(f"Simulated sensor read failed: {str(e)}")
            raise SensorException(f"Simulated sensor error: {str(e)}")
    
    def get_status(self) -> str:
        """Get sensor status."""
        return f"SIMULATED ({self.mode})"
    
    def set_mode(self, mode: str):
        """
        Set simulation mode.
        
        Args:
            mode: 'stable', 'gradual', 'abrupt', or 'fail'
        """
        valid_modes = ['stable', 'gradual', 'abrupt', 'fail']
        if mode in valid_modes:
            self.mode = mode
            self.read_count = 0  # Reset counter so mode takes immediate effect
            self.anomaly_start_count = 2  # Trigger early when mode set via UI/API
            logger.info(f"Simulation mode changed to: {mode}")
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {valid_modes}")


class RealSensor(SensorInterface):
    """
    Real MCP3008 ADC sensor for Raspberry Pi.
    """
    
    def __init__(self):
        """Initialize real MCP3008 sensor."""
        self.channel_voltage = Config.MCP3008_CHANNEL_VOLTAGE
        self.channel_current = Config.MCP3008_CHANNEL_CURRENT
        self.adc_ref = Config.ADC_REFERENCE_VOLTAGE
        self.voltage_factor = Config.VOLTAGE_CALIBRATION_FACTOR
        self.current_offset = Config.CURRENT_ZERO_OFFSET
        self.current_sensitivity = Config.CURRENT_SENSITIVITY
        
        try:
            import Adafruit_MCP3008
            self.mcp = Adafruit_MCP3008.MCP3008()
            logger.info("Real MCP3008 sensor initialized")
        except ImportError:
            logger.warning("Adafruit_MCP3008 not installed - sensor will fail")
            self.mcp = None
        except Exception as e:
            logger.error(f"Failed to initialize MCP3008: {str(e)}")
            self.mcp = None
    
    def read(self) -> Tuple[float, float]:
        """
        Read real sensor data from MCP3008.
        
        Returns:
            Tuple of (voltage, current)
        
        Raises:
            SensorException if read fails
        """
        if self.mcp is None:
            raise SensorException("MCP3008 not initialized")
        
        try:
            # Read raw ADC values (0-1023)
            voltage_raw = self.mcp.read_adc(self.channel_voltage)
            current_raw = self.mcp.read_adc(self.channel_current)
            
            # Convert to voltage (0-3.3V typically)
            adc_voltage = (voltage_raw / 1023.0) * self.adc_ref
            
            # Apply calibration factors
            voltage = adc_voltage * self.voltage_factor
            
            # Current sensor (typically Hall effect or similar)
            current_adc_voltage = (current_raw / 1023.0) * self.adc_ref
            current = (current_adc_voltage * self.current_sensitivity) - self.current_offset
            
            # Ensure reasonable ranges
            voltage = max(0.0, min(20.0, voltage))
            current = max(0.0, min(25.0, current))
            
            return (voltage, current)
        
        except Exception as e:
            logger.error(f"Real sensor read failed: {str(e)}")
            raise SensorException(f"MCP3008 read error: {str(e)}")
    
    def get_status(self) -> str:
        """Get sensor status."""
        if self.mcp is None:
            return "DISCONNECTED"
        return "LIVE"


class SensorFactory:
    """Factory to create appropriate sensor instance."""
    
    @staticmethod
    def create_sensor() -> SensorInterface:
        """
        Create sensor based on configuration.
        
        Returns:
            SensorInterface instance (Simulated or Real)
        """
        sensor_type = Config.SENSOR_TYPE.lower()
        
        if sensor_type == 'simulated':
            logger.info("Using SIMULATED sensor")
            return SimulatedSensor()
        elif sensor_type == 'mcp3008' or sensor_type == 'real':
            logger.info("Using REAL MCP3008 sensor")
            return RealSensor()
        else:
            logger.warning(f"Unknown sensor type: {sensor_type}, defaulting to SIMULATED")
            return SimulatedSensor()


# Global sensor instance
_sensor = None


def get_sensor() -> SensorInterface:
    """Get or create global sensor instance."""
    global _sensor
    if _sensor is None:
        _sensor = SensorFactory.create_sensor()
    return _sensor


def switch_sensor(sensor_type: str):
    """
    Switch to a different sensor type (for testing).
    
    Args:
        sensor_type: 'simulated' or 'mcp3008'
    """
    global _sensor
    if sensor_type.lower() in ['simulated', 'mcp3008', 'real']:
        Config.SENSOR_TYPE = sensor_type
        _sensor = SensorFactory.create_sensor()
        logger.info(f"Switched to {sensor_type} sensor")
    else:
        raise ValueError(f"Invalid sensor type: {sensor_type}")


if __name__ == '__main__':
    sensor = get_sensor()
    print(f"Sensor status: {sensor.get_status()}")
    
    for i in range(5):
        try:
            voltage, current = sensor.read()
            print(f"Reading {i+1}: {voltage:.2f}V, {current:.2f}A, Power: {voltage*current:.2f}W")
            time.sleep(1)
        except SensorException as e:
            print(f"Sensor error: {e}")
