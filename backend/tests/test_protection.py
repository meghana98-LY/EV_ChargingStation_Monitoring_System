from types import SimpleNamespace
from backend.services.protection import ProtectionController
class R:
    def __init__(self): self.state=False
    def on(self): self.state=True
    def off(self): self.state=False
class E:
    def send_anomaly_alert(self,e): return True
class D:
    def record_anomaly(self,*a): pass
    def record_protection(self,*a): pass
def s(vehicle=True,current=True): return SimpleNamespace(timestamp=1,voltage=9,current=.9 if current else None,power=8.1 if current else None,vehicle_present=vehicle,current_available=current,sensor_error=None)
def test_no_vehicle(): assert not ProtectionController(R(),E(),D()).evaluate(s(False),None)[1]
def test_current_missing(): assert ProtectionController(R(),E(),D()).evaluate(s(True,False),None)[2]=='CURRENT_SENSOR_NOT_AVAILABLE'
def test_anomaly(): assert ProtectionController(R(),E(),D()).evaluate(s(),{'is_anomaly':True,'anomaly_score':-.2})[0]=='PROTECTION_TRIPPED'
