try:
    from gpiozero import DigitalOutputDevice
except Exception:
    DigitalOutputDevice = None

class RelayGPIO:
    def __init__(self, pin, active_high=True, hardware=True):
        self.hardware = hardware
        self.device = None
        self.state = False
        if hardware:
            if DigitalOutputDevice is None:
                raise RuntimeError("gpiozero is required in hardware mode")
            self.device = DigitalOutputDevice(pin, active_high=active_high, initial_value=False)
    def on(self):
        if self.device: self.device.on()
        self.state = True
    def off(self):
        if self.device: self.device.off()
        self.state = False
    def close(self):
        self.off()
        if self.device: self.device.close()
