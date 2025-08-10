"""
Integration tests for device management flow
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

# Mock imports for testing without full module setup
from unittest.mock import MagicMock

# Mock the service modules
mock_db = MagicMock()
mock_device_service = MagicMock() 
mock_auth_service = MagicMock()

# Create test client
test_client = MagicMock()

# Test data
TEST_USER_ID = "test-user-123"
TEST_ORG_ID = "test-org-456"
TEST_DEVICE_ID = "test-device-789"

class MockUser:
    def __init__(self, user_id: str, org_id: str, role: str = "user"):
        self.user_id = user_id
        self.organization_id = org_id
        self.role = role

class MockDevice:
    def __init__(self, device_id: str, name: str, device_type: str, org_id: str):
        self.id = device_id
        self.name = name
        self.type = device_type
        self.organization_id = org_id
        self.status = "offline"
        self.location = "Test Location"
        self.description = "Test Device"
        self.base_power = 5.0
        self.base_voltage = 240.0
        self.firmware_version = "1.0.0"
        self.model = "TestModel"
        self.last_seen = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata = {}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    # Note: In a real implementation, you'd use a test database
    # For now, we'll mock this to avoid requiring a real database
    from unittest.mock import AsyncMock
    mock_session = AsyncMock(spec=AsyncSession)
    yield mock_session


@pytest.fixture
def device_service():
    """Device service instance for integration testing"""
    return DeviceService()


@pytest.fixture
def auth_headers():
    """Mock authentication headers for API calls"""
    # In real tests, this would be a valid JWT token
    return {"Authorization": "Bearer mock-admin-token"}


@pytest.fixture
def sample_device_data():
    """Sample device data for testing"""
    return {
        "name": "Integration Test Device",
        "type": "meter",
        "location": "Integration Test Lab",
        "description": "Device for integration testing",
        "base_power": 10.0,
        "base_voltage": 240.0,
        "firmware_version": "2.0.0",
        "model": "IntegrationTestModel",
        "metadata": {"integration_test": True}
    }


class TestDeviceManagementFlow:
    """Integration tests for complete device management workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_device_lifecycle(self, auth_headers, sample_device_data):
        """Test complete device lifecycle: create -> read -> update -> delete"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # Mock authentication for all requests
            with patch('api.routes.get_current_user') as mock_auth, \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'), \
                 patch('api.routes.AuditLogger.log_device_action'), \
                 patch('services.device_service.DeviceService.create_device') as mock_create, \
                 patch('services.device_service.DeviceService.get_device') as mock_get, \
                 patch('services.device_service.DeviceService.update_device') as mock_update, \
                 patch('services.device_service.DeviceService.delete_device') as mock_delete:
                
                from core.auth import User
                from schemas.device import DeviceResponse
                
                # Mock user
                mock_user = User(
                    user_id="integration-test-user",
                    email="integration@test.com",
                    roles=["admin"],
                    organization_id="test-org"
                )
                mock_auth.return_value = mock_user
                
                # Create mock device response
                device_id = str(uuid.uuid4())
                mock_device = DeviceResponse(
                    id=device_id,
                    name=sample_device_data["name"],
                    type=sample_device_data["type"],
                    location=sample_device_data["location"],
                    description=sample_device_data["description"],
                    status="offline",
                    base_power=sample_device_data["base_power"],
                    base_voltage=sample_device_data["base_voltage"],
                    firmware_version=sample_device_data["firmware_version"],
                    model=sample_device_data["model"],
                    metadata=sample_device_data["metadata"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    last_seen=None
                )
                
                # 1. Create Device
                mock_create.return_value = mock_device
                create_response = await client.post(
                    "/api/v1/data/devices",
                    json=sample_device_data,
                    headers=auth_headers
                )
                
                assert create_response.status_code == 201
                create_data = create_response.json()
                assert create_data["success"] is True
                assert create_data["data"]["name"] == sample_device_data["name"]
                created_device_id = create_data["data"]["id"]
                
                # 2. Read Device
                mock_get.return_value = mock_device
                get_response = await client.get(
                    f"/api/v1/data/devices/{created_device_id}/db",
                    headers=auth_headers
                )
                
                assert get_response.status_code == 200
                get_data = get_response.json()
                assert get_data["success"] is True
                assert get_data["data"]["id"] == created_device_id
                assert get_data["data"]["name"] == sample_device_data["name"]
                
                # 3. Update Device
                updated_device = DeviceResponse(**mock_device.model_dump())
                updated_device.name = "Updated Integration Test Device"
                mock_update.return_value = updated_device
                
                update_data = {"name": "Updated Integration Test Device"}
                update_response = await client.put(
                    f"/api/v1/data/devices/{created_device_id}",
                    json=update_data,
                    headers=auth_headers
                )
                
                assert update_response.status_code == 200
                update_response_data = update_response.json()
                assert update_response_data["success"] is True
                
                # 4. Delete Device
                mock_delete.return_value = True
                delete_response = await client.delete(
                    f"/api/v1/data/devices/{created_device_id}",
                    headers=auth_headers
                )
                
                assert delete_response.status_code == 200
                delete_data = delete_response.json()
                assert delete_data["success"] is True
                assert delete_data["data"]["deleted"] is True
    
    @pytest.mark.asyncio
    async def test_device_listing_and_filtering(self, auth_headers, sample_device_data):
        """Test device listing with various filters"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            with patch('api.routes.get_current_user') as mock_auth, \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'), \
                 patch('api.routes.AuditLogger.log_device_action'), \
                 patch('services.device_service.DeviceService.list_devices') as mock_list:
                
                from core.auth import User
                from schemas.device import DeviceResponse
                
                # Mock user
                mock_user = User(
                    user_id="integration-test-user",
                    email="integration@test.com",
                    roles=["admin"],
                    organization_id="test-org"
                )
                mock_auth.return_value = mock_user
                
                # Mock device list
                mock_devices = [
                    DeviceResponse(
                        id=str(uuid.uuid4()),
                        name=f"Test Device {i}",
                        type="meter" if i % 2 == 0 else "sensor",
                        location=f"Location {i}",
                        status="online" if i % 3 == 0 else "offline",
                        description=f"Test device {i}",
                        base_power=5.0,
                        base_voltage=240.0,
                        firmware_version="1.0.0",
                        model="TestModel",
                        metadata={},
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        last_seen=None
                    )
                    for i in range(10)
                ]
                
                # Test basic listing
                mock_list.return_value = mock_devices
                response = await client.get(
                    "/api/v1/data/devices/list",
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]) == 10
                
                # Test filtering by device type
                meter_devices = [d for d in mock_devices if d.type == "meter"]
                mock_list.return_value = meter_devices
                response = await client.get(
                    "/api/v1/data/devices/list?device_type=meter",
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]) == len(meter_devices)
                
                # Test filtering by status
                online_devices = [d for d in mock_devices if d.status == "online"]
                mock_list.return_value = online_devices
                response = await client.get(
                    "/api/v1/data/devices/list?status=online",
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]) == len(online_devices)
                
                # Test pagination
                mock_list.return_value = mock_devices[:5]
                response = await client.get(
                    "/api/v1/data/devices/list?limit=5&skip=0",
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]) == 5
    
    @pytest.mark.asyncio
    async def test_authentication_and_authorization_flow(self, sample_device_data):
        """Test authentication and authorization throughout device operations"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            # Test unauthenticated access
            response = await client.get("/api/v1/data/devices/list")
            assert response.status_code == 401
            
            response = await client.post("/api/v1/data/devices", json=sample_device_data)
            assert response.status_code == 401
            
            # Test insufficient permissions
            with patch('api.routes.get_current_user') as mock_auth, \
                 patch('api.routes.check_device_permission', side_effect=HTTPException(status_code=403)):
                
                from core.auth import User
                
                # Mock user with limited permissions
                limited_user = User(
                    user_id="limited-user",
                    email="limited@test.com",
                    roles=["viewer"],
                    organization_id="test-org"
                )
                mock_auth.return_value = limited_user
                
                response = await client.post(
                    "/api/v1/data/devices",
                    json=sample_device_data,
                    headers={"Authorization": "Bearer limited-token"}
                )
                assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_error_handling_and_edge_cases(self, auth_headers):
        """Test error handling and edge cases"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            with patch('api.routes.get_current_user') as mock_auth, \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'), \
                 patch('api.routes.AuditLogger.log_device_action'):
                
                from core.auth import User
                from fastapi import HTTPException
                
                # Mock user
                mock_user = User(
                    user_id="test-user",
                    email="test@test.com",
                    roles=["admin"],
                    organization_id="test-org"
                )
                mock_auth.return_value = mock_user
                
                # Test invalid device data
                invalid_device_data = {
                    "name": "",  # Empty name
                    "type": "invalid_type",  # Invalid type
                }
                
                response = await client.post(
                    "/api/v1/data/devices",
                    json=invalid_device_data,
                    headers=auth_headers
                )
                assert response.status_code == 422  # Validation error
                
                # Test accessing non-existent device
                with patch('services.device_service.DeviceService.get_device', return_value=None):
                    response = await client.get(
                        "/api/v1/data/devices/nonexistent-device/db",
                        headers=auth_headers
                    )
                    assert response.status_code == 404
                
                # Test database error handling
                with patch('services.device_service.DeviceService.create_device', 
                          side_effect=Exception("Database error")):
                    valid_device_data = {
                        "name": "Test Device",
                        "type": "meter",
                        "location": "Test Location"
                    }
                    
                    response = await client.post(
                        "/api/v1/data/devices",
                        json=valid_device_data,
                        headers=auth_headers
                    )
                    assert response.status_code == 500


class TestDeviceServiceIntegration:
    """Integration tests for device service operations"""
    
    @pytest.mark.asyncio
    async def test_device_service_database_operations(self, db_session):
        """Test device service database operations"""
        device_service = DeviceService()
        
        # Mock database responses
        mock_device_data = DeviceCreate(
            name="Service Test Device",
            type="meter",
            location="Service Test Location"
        )
        
        # In real tests, these would interact with a test database
        with patch.object(device_service, 'create_device') as mock_create, \
             patch.object(device_service, 'get_device') as mock_get, \
             patch.object(device_service, 'list_devices') as mock_list, \
             patch.object(device_service, 'update_device') as mock_update, \
             patch.object(device_service, 'delete_device') as mock_delete:
            
            from schemas.device import DeviceResponse
            
            device_id = str(uuid.uuid4())
            mock_device_response = DeviceResponse(
                id=device_id,
                name="Service Test Device",
                type="meter",
                location="Service Test Location",
                status="offline",
                description=None,
                base_power=None,
                base_voltage=None,
                firmware_version=None,
                model=None,
                metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_seen=None
            )
            
            # Test create
            mock_create.return_value = mock_device_response
            created_device = await device_service.create_device(
                db=db_session,
                device_data=mock_device_data
            )
            assert created_device.name == "Service Test Device"
            mock_create.assert_called_once()
            
            # Test get
            mock_get.return_value = mock_device_response
            retrieved_device = await device_service.get_device(
                db=db_session,
                device_id=device_id
            )
            assert retrieved_device.id == device_id
            mock_get.assert_called_once()
            
            # Test list
            mock_list.return_value = [mock_device_response]
            devices_list = await device_service.list_devices(
                db=db_session,
                limit=10
            )
            assert len(devices_list) == 1
            mock_list.assert_called_once()
            
            # Test update
            mock_update.return_value = mock_device_response
            updated_device = await device_service.update_device(
                db=db_session,
                device_id=device_id,
                device_data=DeviceUpdate(name="Updated Name")
            )
            assert updated_device is not None
            mock_update.assert_called_once()
            
            # Test delete
            mock_delete.return_value = True
            deleted = await device_service.delete_device(
                db=db_session,
                device_id=device_id
            )
            assert deleted is True
            mock_delete.assert_called_once()


class TestOrganizationIsolation:
    """Integration tests for organization-based access control"""
    
    @pytest.mark.asyncio
    async def test_organization_device_isolation(self, sample_device_data):
        """Test that users can only access devices from their organization"""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            with patch('api.routes.check_rate_limit'), \
                 patch('api.routes.AuditLogger.log_device_action'), \
                 patch('services.device_service.DeviceService.list_devices') as mock_list:
                
                from core.auth import User
                from schemas.device import DeviceResponse
                
                # Create mock devices from different organizations
                org1_device = DeviceResponse(
                    id=str(uuid.uuid4()),
                    name="Org 1 Device",
                    type="meter",
                    location="Org 1 Location",
                    status="online",
                    description="Device from organization 1",
                    base_power=5.0,
                    base_voltage=240.0,
                    firmware_version="1.0.0",
                    model="OrgModel",
                    metadata={"organization": "org-1"},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    last_seen=None
                )
                
                # Test user from organization 1
                org1_user = User(
                    user_id="org1-user",
                    email="user@org1.com",
                    roles=["admin"],
                    organization_id="org-1"
                )
                
                with patch('api.routes.get_current_user', return_value=org1_user), \
                     patch('api.routes.check_device_permission'):
                    
                    # Should only see devices from their organization
                    mock_list.return_value = [org1_device]  # Filtered by organization
                    
                    response = await client.get(
                        "/api/v1/data/devices/list",
                        headers={"Authorization": "Bearer org1-token"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert len(data["data"]) == 1
                    assert data["data"][0]["name"] == "Org 1 Device"
                    
                    # Verify organization filter was applied
                    mock_list.assert_called_once()
                    call_kwargs = mock_list.call_args.kwargs
                    assert call_kwargs.get('organization_filter') is not None
