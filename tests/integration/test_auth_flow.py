import pytest
import requests

BASE_URL = "http://localhost:8000"  # Adjust as needed

def test_register_and_login():
    """Test user registration and login flow."""
    register_payload = {"username": "testuser", "password": "testpass"}
    login_payload = {"username": "testuser", "password": "testpass"}

    # Register user
    resp = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
    assert resp.status_code in (200, 201)

    # Login user
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
