try:
    import spidev
except Exception:
    spidev = None

class MCP3008:
    def __init__(self, bus=0, device=0, vref=3.3, hardware=True):
        self.vref, self.spi = vref, None
        if hardware:
            if spidev is None: raise RuntimeError("spidev is required in hardware mode")
            self.spi = spidev.SpiDev()
            self.spi.open(bus, device)
            self.spi.max_speed_hz = 1000000
            self.spi.mode = 0
    def read_raw(self, channel):
        if not 0 <= channel <= 7: raise ValueError("channel must be 0..7")
        if not self.spi: raise RuntimeError("ADC unavailable")
        r = self.spi.xfer2([1, (8+channel)<<4, 0])
        return ((r[1]&3)<<8) | r[2]
    def read_voltage(self, channel):
        return self.read_raw(channel)*self.vref/1023.0
    def close(self):
        if self.spi: self.spi.close()
