import pytest
from services.data_processing.core.processing import process_energy_data

@pytest.mark.unit
def test_process_energy_data():
    data = {"device_id": "dev1", "power": 100, "voltage": 220, "current": 0.45}
    result = process_energy_data(data)
    assert result["processed"] is True
    assert result["device_id"] == "dev1"
