import pytest
from services.data_ingestion.core import ingest

@pytest.mark.unit
def test_ingest_valid_data():
    payload = {"device_id": "dev1", "data": {"energy": 10}}
    result = ingest.process(payload)
    assert result['status'] == 'success'
