import threading,logging
from .config import *
from .sensor import SensorManager
from .relay_controller import RelayController
from .ml.anomaly_detector import AnomalyDetector
from .services.email_alert import EmailAlertService
from .services.protection import ProtectionController
from .database.db import Database
class ChargingMonitor:
    def __init__(self):
        self.db=Database(DATABASE_PATH); self.relay=RelayController(RELAY_GPIO,RELAY_ACTIVE_HIGH,HARDWARE_MODE)
        self.sensors=SensorManager(); self.detector=AnomalyDetector(ML_MODEL_PATH); self.email=EmailAlertService()
        self.protection=ProtectionController(self.relay,self.email,self.db,ML_REQUIRES_CURRENT)
        self.latest={"state":"IDLE","relay_on":False,"reason":"STARTUP","vehicle_present":False,"voltage":None,"current":None,"power":None,"anomaly_score":None}
        self.stop_event=threading.Event()
    def start(self):
        self.relay.off(); threading.Thread(target=self.loop,daemon=True).start()
    def loop(self):
        while not self.stop_event.is_set():
            try:
                s=self.sensors.read(); anomaly=None
                if s.current is not None:
                    if not self.detector.available: raise RuntimeError("Isolation Forest model is missing")
                    anomaly=self.detector.predict(s.voltage,s.current,s.power)
                state,on,reason=self.protection.evaluate(s,anomaly)
                self.latest={"timestamp":s.timestamp,"state":state,"relay_on":on,"reason":reason,"vehicle_present":s.vehicle_present,"distance_cm":s.distance_cm,"voltage":s.voltage,"current":s.current,"power":s.power,"anomaly_score":anomaly["anomaly_score"] if anomaly else None,"anomaly":anomaly,"current_available":s.current_available}
                self.db.record_sensor(s,self.latest["anomaly_score"],on,state)
            except Exception as e:
                logging.exception("monitoring error"); self.relay.off(); self.latest.update({"state":"SENSOR_ERROR","relay_on":False,"reason":str(e)})
            self.stop_event.wait(SAMPLE_INTERVAL_SECONDS)
    def reset_protection(self):
        self.protection.reset(); self.latest.update({"state":"IDLE","relay_on":False,"reason":"PROTECTION_RESET"})
    def stop(self):
        self.stop_event.set(); self.relay.off()
        try: self.sensors.close()
        finally: self.relay.close()
