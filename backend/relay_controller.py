import logging
from .hardware.gpio import RelayGPIO

log = logging.getLogger(__name__)

class RelayController:
    def __init__(self, pin, active_high, hardware):
        self.gpio = RelayGPIO(pin, active_high, hardware)
        self.off()
        log.info(
            "Relay initialized: GPIO=%s active_high=%s hardware=%s",
            pin, active_high, hardware
        )

    def on(self):
        self.gpio.on()
        log.info("RELAY ON command; reported state=%s", self.active)

    def off(self):
        self.gpio.off()
        log.info("RELAY OFF command; reported state=%s", self.active)

    @property
    def active(self):
        return self.gpio.state

    def close(self):
        self.gpio.close()
        log.info("Relay closed")
