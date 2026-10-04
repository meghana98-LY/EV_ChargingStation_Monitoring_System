import time, statistics
try:
    from gpiozero import DigitalOutputDevice, DigitalInputDevice
except Exception:
    DigitalOutputDevice = DigitalInputDevice = None

class HCSR04:
    def __init__(self, trigger_pin, echo_pin, hardware=True):
        self.hardware=hardware
        self.trigger=self.echo=None
        if hardware:
            if DigitalOutputDevice is None: raise RuntimeError("gpiozero is required")
            self.trigger=DigitalOutputDevice(trigger_pin, initial_value=False)
            self.echo=DigitalInputDevice(echo_pin, pull_up=False)
    def distance_cm_once(self):
        self.trigger.off(); time.sleep(2e-6); self.trigger.on(); time.sleep(10e-6); self.trigger.off()
        deadline=time.monotonic()+0.05
        while not self.echo.is_active and time.monotonic()<deadline: pass
        start=time.monotonic()
        deadline=time.monotonic()+0.05
        while self.echo.is_active and time.monotonic()<deadline: pass
        duration=time.monotonic()-start
        if duration<=0 or duration>=0.05: raise TimeoutError("HC-SR04 timeout")
        return duration*34300/2
    def vehicle_present(self, threshold, samples=3):
        d=statistics.median(self.distance_cm_once() for _ in range(samples))
        return d<=threshold, d
    def close(self):
        if self.trigger: self.trigger.close()
        if self.echo: self.echo.close()
