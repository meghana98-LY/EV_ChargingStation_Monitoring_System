class ProtectionController:
    def __init__(self,relay,email,db,requires_current=True):
        self.relay,self.email,self.db=relay,email,db; self.requires_current=requires_current; self.lockout=False
    def reset(self):
        self.lockout=False; self.relay.off()
    def evaluate(self,s,anomaly):
        if self.lockout: self.relay.off(); return ("PROTECTION_TRIPPED",False,"PROTECTION_LOCKOUT")
        if not s.vehicle_present: self.relay.off(); return ("IDLE",False,"NO_VEHICLE")
        if self.requires_current and not s.current_available: self.relay.off(); return ("SENSOR_ERROR",False,"CURRENT_SENSOR_NOT_AVAILABLE")
        if anomaly and anomaly["is_anomaly"]:
            self.relay.off(); self.lockout=True
            e={"timestamp":s.timestamp,"vehicle_present":s.vehicle_present,"voltage":s.voltage,"current":s.current,"power":s.power,"anomaly_score":anomaly["anomaly_score"],"reason":"ANOMALY_DETECTED"}
            sent=False
            try: sent=self.email.send_anomaly_alert(e)
            except Exception as ex: e["email_error"]=str(ex)
            self.db.record_anomaly(e,sent); self.db.record_protection(e)
            return ("PROTECTION_TRIPPED",False,"ANOMALY_DETECTED")
        self.relay.on(); return ("CHARGING",True,"NORMAL_CHARGING")
