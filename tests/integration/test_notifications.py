import pytest
import requests

BASE_URL = "http://localhost:8000"  # Adjust as needed

def test_send_notification():
    """Test sending a notification via the API."""
    payload = {"user_id": 1, "message": "Test notification"}
    resp = requests.post(f"{BASE_URL}/notifications/send", json=payload)
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data.get("status") == "sent"
