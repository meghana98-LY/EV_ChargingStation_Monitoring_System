from .hardware.gpio import RelayGPIO
class RelayController:
    def __init__(self,pin,active_high,hardware):
        self.gpio=RelayGPIO(pin,active_high,hardware); self.off()
    def on(self): self.gpio.on()
    def off(self): self.gpio.off()
    @property
    def active(self): return self.gpio.state
    def close(self): self.gpio.close()
