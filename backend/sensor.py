import time
from dataclasses import dataclass
from .config import *
from .hardware.mcp3008 import MCP3008
from .hardware.voltage_sensor import VoltageSensor
from .hardware.current_sensor import CurrentSensor
from .hardware.ultrasonic import HCSR04

@dataclass
class SensorSnapshot:
    timestamp:float; voltage:float|None; current:float|None; power:float|None
    vehicle_present:bool; distance_cm:float|None; current_available:bool
    sensor_error:str|None=None

class SensorManager:
    def __init__(self):
        self.adc=MCP3008(0,0,ADC_VREF,HARDWARE_MODE)
        self.voltage=VoltageSensor(self.adc,ADC_VOLTAGE_CHANNEL,VOLTAGE_CALIBRATION_FACTOR)
        self.current=CurrentSensor(self.adc,ADC_CURRENT_CHANNEL,ACS712_SENSITIVITY,ACS712_ZERO_OFFSET) if CURRENT_SENSOR_ENABLED else None
        self.ultrasonic=HCSR04(HC_SR04_TRIGGER_GPIO,HC_SR04_ECHO_GPIO,HARDWARE_MODE)
    def read(self):
        v=self.voltage.read()
        vehicle,distance=self.ultrasonic.vehicle_present(VEHICLE_DISTANCE_THRESHOLD_CM,ULTRASONIC_SAMPLES)
        current=power=None
        if self.current:
            current=self.current.read().current
            power=v.voltage*current
        return SensorSnapshot(time.time(),v.voltage,current,power,vehicle,distance,self.current is not None)
    def close(self):
        self.ultrasonic.close(); self.adc.close()
