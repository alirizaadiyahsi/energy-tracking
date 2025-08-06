import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.integration
class TestDataFlow:
    @pytest.mark.asyncio
    async def test_iot_to_dashboard_flow(self):
        # Simulate sending data to ingestion
        energy_reading = {
            "deviceId": "integration-device",
            "power": 1200.0,
            "voltage": 230.0,
            "current": 5.22
        }
        async with AsyncClient(base_url="http://localhost:8001") as client:
            response = await client.post("/ingest", json=energy_reading)
            assert response.status_code == 200
        await asyncio.sleep(2)
        async with AsyncClient(base_url="http://localhost:8003") as client:
            response = await client.get("/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert "totalEnergyToday" in data
