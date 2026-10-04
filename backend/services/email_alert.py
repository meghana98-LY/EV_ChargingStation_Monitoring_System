import smtplib,time
from email.message import EmailMessage
from ..config import *
class EmailAlertService:
    def __init__(self): self.last_sent=0
    def send_anomaly_alert(self,event):
        if not EMAIL_ENABLED: return False
        if not all([SENDER_EMAIL,SENDER_PASSWORD,ALERT_EMAIL]): raise RuntimeError("Email configuration incomplete")
        if time.time()-self.last_sent < ANOMALY_EMAIL_COOLDOWN_SECONDS: return False
        msg=EmailMessage()
        msg["Subject"]="EV Charging Station - ANOMALY DETECTED"
        msg["From"]=SENDER_EMAIL; msg["To"]=ALERT_EMAIL
        msg.set_content(
            "EV Charging Station Anomaly Alert\n\n"
            f"Timestamp: {event['timestamp']}\n"
            f"Vehicle detected: {event['vehicle_present']}\n"
            f"Voltage: {event['voltage']} V\n"
            f"Current: {event['current']} A\n"
            f"Power: {event['power']} W\n"
            f"Anomaly score: {event['anomaly_score']}\n"
            f"Protection reason: {event['reason']}\n"
            "Action: Charging automatically switched OFF.\n")
        with smtplib.SMTP(SMTP_SERVER,SMTP_PORT,timeout=20) as s:
            s.starttls(); s.login(SENDER_EMAIL,SENDER_PASSWORD); s.send_message(msg)
        self.last_sent=time.time(); return True
