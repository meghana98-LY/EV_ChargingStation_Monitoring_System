from backend.services.email_alert import EmailAlertService
def test_disabled(monkeypatch):
    monkeypatch.setattr('backend.services.email_alert.EMAIL_ENABLED',False)
    assert EmailAlertService().send_anomaly_alert({}) is False
