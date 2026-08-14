"""
Email alert system with cooldown mechanism.
Sends warning and critical alerts via SMTP.
"""
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import Config
from logger import get_logger

logger = get_logger('email_alert')


class EmailAlertSystem:
    """Manages sending email alerts with cooldown to prevent spam."""
    
    def __init__(self):
        """Initialize email alert system."""
        self.smtp_host = Config.SMTP_HOST
        self.smtp_port = Config.SMTP_PORT
        self.smtp_user = Config.SMTP_USER
        self.smtp_password = Config.SMTP_PASSWORD
        self.from_email = Config.ALERT_EMAIL_FROM or Config.SMTP_USER
        self.to_email = Config.ALERT_EMAIL_TO
        self.enabled = Config.EMAIL_ALERT_ENABLED
        
        self.last_warning_time = None
        self.last_critical_time = None
        self.cooldown_seconds = Config.EMAIL_ALERT_COOLDOWN
        
        if self.enabled:
            self._validate_config()
    
    def _validate_config(self):
        """Validate email configuration."""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.to_email]):
            logger.warning(
                "Email alert enabled but configuration incomplete. "
                "Check SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO"
            )
            self.enabled = False
    
    def _is_cooldown_active(self, severity: str) -> bool:
        """
        Check if alert cooldown is active.
        
        Args:
            severity: 'WARNING' or 'CRITICAL'
        
        Returns:
            True if cooldown is active, False otherwise
        """
        if severity == 'WARNING':
            if self.last_warning_time is None:
                return False
            elapsed = time.time() - self.last_warning_time
            return elapsed < self.cooldown_seconds
        
        elif severity == 'CRITICAL':
            if self.last_critical_time is None:
                return False
            elapsed = time.time() - self.last_critical_time
            return elapsed < self.cooldown_seconds
        
        return False
    
    def _update_cooldown(self, severity: str):
        """Update last alert time for cooldown."""
        if severity == 'WARNING':
            self.last_warning_time = time.time()
        elif severity == 'CRITICAL':
            self.last_critical_time = time.time()
    
    def _build_email(self, severity: str, timestamp: str, voltage: float,
                     current: float, power: float, anomaly_score: float,
                     reason: str) -> MIMEMultipart:
        """
        Build email message.
        
        Args:
            severity: 'WARNING' or 'CRITICAL'
            timestamp: Reading timestamp
            voltage: Voltage value
            current: Current value
            power: Power value
            anomaly_score: ML anomaly score
            reason: Reason for alert
        
        Returns:
            MIMEMultipart message object
        """
        msg = MIMEMultipart('alternative')
        
        if severity == 'WARNING':
            subject = '⚠️ EV Charging Early Warning'
            emoji = '⚠️'
        else:  # CRITICAL
            subject = '🚨 EV Charging Critical Alert'
            emoji = '🚨'
        
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        
        # HTML content
        html = f"""\
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 20px auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: {'#ff6b6b' if severity == 'CRITICAL' else '#ffa500'};">
                        {emoji} {severity} ALERT
                    </h2>
                    
                    <p><strong>Time:</strong> {timestamp}</p>
                    <p><strong>Severity:</strong> <span style="color: {'#ff6b6b' if severity == 'CRITICAL' else '#ffa500'}; font-weight: bold;">{severity}</span></p>
                    
                    <h3 style="color: #333; margin-top: 20px;">Sensor Readings:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #f9f9f9;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Voltage</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{voltage:.2f} V</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Current</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{current:.2f} A</td>
                        </tr>
                        <tr style="background-color: #f9f9f9;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Power</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{power:.2f} W</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Anomaly Score</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{anomaly_score:.4f}</td>
                        </tr>
                    </table>
                    
                    <h3 style="color: #333; margin-top: 20px;">Alert Reason:</h3>
                    <p style="background-color: #fffbeb; padding: 10px; border-left: 4px solid #fbbf24;">{reason}</p>
                    
                    <h3 style="color: #333; margin-top: 20px;">Recommended Actions:</h3>
                    <ul>
                        <li>Check the charging station for physical anomalies</li>
                        <li>Verify sensor calibration and connections</li>
                        <li>Monitor the charging session closely</li>
                        <li>Consider stopping the charge if the condition persists</li>
                        <li>Contact technical support if the issue continues</li>
                    </ul>
                    
                    <hr style="margin-top: 20px; border: none; border-top: 1px solid #ddd;">
                    <p style="font-size: 12px; color: #999;">
                        This is an automated alert from the EV Charging Station Monitoring System.
                        Do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        return msg
    
    def send_alert(self, severity: str, timestamp: str, voltage: float,
                   current: float, power: float, anomaly_score: float,
                   reason: str) -> bool:
        """
        Send email alert if cooldown permits.
        
        Args:
            severity: 'WARNING' or 'CRITICAL'
            timestamp: Reading timestamp
            voltage: Voltage value in volts
            current: Current value in amps
            power: Power value in watts
            anomaly_score: ML anomaly score
            reason: Reason for alert
        
        Returns:
            True if email was sent, False otherwise
        """
        if not self.enabled:
            logger.debug(f"Email alerts disabled. Alert suppressed: {severity}")
            return False
        
        # Check cooldown
        if self._is_cooldown_active(severity):
            elapsed = time.time() - (self.last_warning_time if severity == 'WARNING' else self.last_critical_time)
            logger.debug(f"{severity} alert cooldown active ({elapsed:.0f}s/{self.cooldown_seconds}s)")
            return False
        
        try:
            # Build message
            msg = self._build_email(
                severity, timestamp, voltage, current, power,
                anomaly_score, reason
            )
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            # Update cooldown
            self._update_cooldown(severity)
            logger.info(f"Email alert sent ({severity}): {self.to_email}")
            return True
        
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False
    
    def get_cooldown_status(self) -> dict:
        """Get current cooldown status."""
        return {
            'warning_cooldown_active': self._is_cooldown_active('WARNING'),
            'critical_cooldown_active': self._is_cooldown_active('CRITICAL'),
            'last_warning_time': self.last_warning_time,
            'last_critical_time': self.last_critical_time,
            'cooldown_seconds': self.cooldown_seconds,
            'enabled': self.enabled
        }


# Global email alert system instance
_email_system = None


def get_email_system() -> EmailAlertSystem:
    """Get or create global email alert system instance."""
    global _email_system
    if _email_system is None:
        _email_system = EmailAlertSystem()
    return _email_system


if __name__ == '__main__':
    email_system = get_email_system()
    print(f"Email system enabled: {email_system.enabled}")
    print(f"Cooldown status: {email_system.get_cooldown_status()}")
    
    # Test alert building (won't actually send without proper config)
    if email_system.enabled:
        result = email_system.send_alert(
            severity='WARNING',
            timestamp=datetime.now().isoformat(),
            voltage=14.2,
            current=9.5,
            power=134.9,
            anomaly_score=-0.25,
            reason='Persistent voltage elevation detected over 5 consecutive readings'
        )
        print(f"Alert send result: {result}")
    else:
        print("Email alerts not enabled (check .env configuration)")
