from dataclasses import dataclass
@dataclass
class VoltageReading:
    raw:int
    adc_voltage:float
    voltage:float

class VoltageSensor:
    def __init__(self, adc, channel, factor):
        self.adc, self.channel, self.factor = adc, channel, factor
    def read(self):
        raw = self.adc.read_raw(self.channel)
        av = raw*self.adc.vref/1023.0
        return VoltageReading(raw, av, av*self.factor)
