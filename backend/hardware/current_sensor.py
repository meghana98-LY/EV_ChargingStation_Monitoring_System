from dataclasses import dataclass
@dataclass
class CurrentReading:
    raw:int
    sensor_voltage:float
    current:float

class CurrentSensor:
    def __init__(self, adc, channel, sensitivity, zero_offset):
        self.adc, self.channel = adc, channel
        self.sensitivity, self.zero_offset = sensitivity, zero_offset
    def read(self):
        raw = self.adc.read_raw(self.channel)
        v = raw*self.adc.vref/1023.0
        return CurrentReading(raw, v, (v-self.zero_offset)/self.sensitivity)
    def calibrate_zero(self, samples=100):
        vals=[self.adc.read_voltage(self.channel) for _ in range(samples)]
        self.zero_offset=sum(vals)/len(vals)
        return self.zero_offset
