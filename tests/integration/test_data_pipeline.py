import pytest
import requests

BASE_URL = "http://localhost:8000"  # Adjust as needed

def test_data_pipeline_ingest():
    """Test data ingestion endpoint."""
    payload = {"device_id": "dev123", "data": {"energy": 42}}
    resp = requests.post(f"{BASE_URL}/data-ingestion/ingest", json=payload)
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data.get("status") == "success"
