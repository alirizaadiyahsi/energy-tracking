import pytest
from services.notification.core import notification_service

@pytest.mark.unit
def test_send_notification():
    result = notification_service.send(user_id=1, message="Test")
    assert result['status'] == 'sent'
