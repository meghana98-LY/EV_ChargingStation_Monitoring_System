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
        # Sanitize password (remove spaces if user pasted 'xxxx xxxx xxxx xxxx')
        if self.smtp_password:
            self.smtp_password = self.smtp_password.replace(" ", "").strip()
            
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
        
        if severity == 'TEST':
            subject = '🧪 EV Charging System - Diagnostic Test Email'
            emoji = '🧪'
        elif severity == 'WARNING':
            subject = '⚠️ EV Charging Early Warning'
            emoji = '⚠️'
        else:  # CRITICAL
            subject = '🚨 EV Charging Critical Alert'
            emoji = '🚨'
        
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        
        header_color = '#3b82f6' if severity == 'TEST' else ('#ef4444' if severity == 'CRITICAL' else '#f59e0b')
        
        # HTML content
        html = f"""\
        <html>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; padding: 30px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                    <div style="border-bottom: 2px solid {header_color}; padding-bottom: 15px; margin-bottom: 20px;">
                        <h2 style="color: {header_color}; margin: 0; font-size: 24px; display: flex; align-items: center; gap: 10px;">
                            {emoji} {severity} NOTIFICATION
                        </h2>
                        <p style="color: #94a3b8; font-size: 13px; margin-top: 5px;">EV Charging Station Monitoring & Anomaly Detection System</p>
                    </div>
                    
                    <p style="color: #e2e8f0;"><strong>Timestamp:</strong> {timestamp}</p>
                    <p style="color: #e2e8f0;"><strong>Severity Level:</strong> <span style="color: {header_color}; font-weight: bold; padding: 3px 8px; background: rgba(255,255,255,0.05); border-radius: 4px;">{severity}</span></p>
                    
                    <h3 style="color: #38bdf8; margin-top: 25px; border-bottom: 1px solid #334155; padding-bottom: 8px;">Telemetry Readings:</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px; color: #f8fafc;">
                        <tr style="background-color: #0f172a;">
                            <td style="padding: 12px; border: 1px solid #334155; color: #94a3b8;"><strong>Voltage (V)</strong></td>
                            <td style="padding: 12px; border: 1px solid #334155; color: #38bdf8; font-weight: bold;">{voltage:.2f} V</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #334155; color: #94a3b8;"><strong>Current (A)</strong></td>
                            <td style="padding: 12px; border: 1px solid #334155; color: #f59e0b; font-weight: bold;">{current:.2f} A</td>
                        </tr>
                        <tr style="background-color: #0f172a;">
                            <td style="padding: 12px; border: 1px solid #334155; color: #94a3b8;"><strong>Power (W)</strong></td>
                            <td style="padding: 12px; border: 1px solid #334155; color: #10b981; font-weight: bold;">{power:.2f} W</td>
                        </tr>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #334155; color: #94a3b8;"><strong>ML Anomaly Score</strong></td>
                            <td style="padding: 12px; border: 1px solid #334155; color: #cbd5e1;">{anomaly_score:.4f}</td>
                        </tr>
                    </table>
                    
                    <h3 style="color: #38bdf8; margin-top: 25px; border-bottom: 1px solid #334155; padding-bottom: 8px;">Analysis & Reason:</h3>
                    <div style="background-color: #0f172a; padding: 15px; border-left: 4px solid {header_color}; border-radius: 4px; color: #e2e8f0;">
                        {reason}
                    </div>
                    
                    <h3 style="color: #38bdf8; margin-top: 25px; border-bottom: 1px solid #334155; padding-bottom: 8px;">Recommended Operational Protocol:</h3>
                    <ul style="color: #cbd5e1; padding-left: 20px; line-height: 1.8;">
                        <li>Verify physical cable connection and connector thermal status.</li>
                        <li>Check telemetry sensors and MCP3008 ADC SPI communication.</li>
                        <li>Monitor voltage & current trends on real-time web dashboard.</li>
                        <li>If severity persists in CRITICAL, initiate manual session termination.</li>
                    </ul>
                    
                    <hr style="margin-top: 30px; border: none; border-top: 1px solid #334155;">
                    <p style="font-size: 12px; color: #64748b; text-align: center;">
                        Automated Early-Warning System | Isolation Forest + Trend Analysis
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
            
            # Clean password
            password = self.smtp_password.replace(" ", "") if self.smtp_password else ""

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, password)
                server.send_message(msg)
            
            # Update cooldown
            self._update_cooldown(severity)
            logger.info(f"Email alert sent ({severity}): {self.to_email}")
            return True
        
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed for user {self.smtp_user}: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False

    def send_test_email(self) -> tuple[bool, str]:
        """
        Send a manual diagnostic test email bypassing cooldown.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.smtp_host or not self.smtp_user or not self.smtp_password or not self.to_email:
            return False, "Incomplete SMTP configuration in .env (Check SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO)"
        
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            msg = self._build_email(
                severity='TEST',
                timestamp=timestamp,
                voltage=12.10,
                current=7.05,
                power=85.31,
                anomaly_score=-0.7500,
                reason='Manual diagnostic trigger from dashboard'
            )
            
            password = self.smtp_password.replace(" ", "") if self.smtp_password else ""

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, password)
                server.send_message(msg)
            
            logger.info(f"Test email successfully sent to {self.to_email}")
            return True, f"Test email successfully sent to {self.to_email}"
        
        except Exception as e:
            err_msg = f"Failed to send test email: {str(e)}"
            logger.error(err_msg)
            return False, err_msg
    
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
