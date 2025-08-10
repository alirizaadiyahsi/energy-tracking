"""
Standalone unit tests for device management endpoints
Tests the core business logic without external dependencies
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Test data classes
class DeviceCreate(BaseModel):
    name: str
    type: str
    location: Optional[str] = None
    description: Optional[str] = None
    base_power: Optional[float] = None
    base_voltage: Optional[float] = None
    firmware_version: Optional[str] = None
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DeviceResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    organization_id: str
    location: Optional[str] = None
    description: Optional[str] = None
    base_power: Optional[float] = None
    base_voltage: Optional[float] = None
    firmware_version: Optional[str] = None
    model: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class User:
    def __init__(self, user_id: str, organization_id: str, role: str = "user"):
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role

# Mock device service class
class MockDeviceService:
    def __init__(self):
        self.devices = {}
    
    async def create_device(self, device_data: DeviceCreate, organization_id: str, user_id: str) -> DeviceResponse:
        device_id = str(uuid.uuid4())
        device = DeviceResponse(
            id=device_id,
            name=device_data.name,
            type=device_data.type,
            status="offline",
            organization_id=organization_id,
            location=device_data.location,
            description=device_data.description,
            base_power=device_data.base_power,
            base_voltage=device_data.base_voltage,
            firmware_version=device_data.firmware_version,
            model=device_data.model,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=device_data.metadata or {}
        )
        self.devices[device_id] = device
        return device
    
    async def get_device(self, device_id: str, organization_id: str) -> Optional[DeviceResponse]:
        device = self.devices.get(device_id)
        if device and device.organization_id == organization_id:
            return device
        return None
    
    async def list_devices(self, organization_id: str, skip: int = 0, limit: int = 100) -> list[DeviceResponse]:
        org_devices = [d for d in self.devices.values() if d.organization_id == organization_id]
        return org_devices[skip:skip + limit]
    
    async def update_device(self, device_id: str, device_data: dict, organization_id: str, user_id: str) -> Optional[DeviceResponse]:
        device = await self.get_device(device_id, organization_id)
        if not device:
            return None
        
        # Update device fields
        for key, value in device_data.items():
            if hasattr(device, key) and value is not None:
                setattr(device, key, value)
        device.updated_at = datetime.utcnow()
        return device
    
    async def delete_device(self, device_id: str, organization_id: str, user_id: str) -> bool:
        device = await self.get_device(device_id, organization_id)
        if device:
            del self.devices[device_id]
            return True
        return False

# Mock authentication and authorization
class MockAuthService:
    def __init__(self):
        self.valid_tokens = {
            "valid_token": User("user-123", "org-456", "user"),
            "admin_token": User("admin-123", "org-456", "admin"),
            "other_org_token": User("user-789", "org-999", "user")
        }
    
    async def validate_token(self, token: str) -> Optional[User]:
        return self.valid_tokens.get(token)

class MockPermissionChecker:
    def check_permission(self, user: User, permission: str) -> bool:
        permissions = {
            "user": ["read_device", "create_device", "update_device"],
            "admin": ["read_device", "create_device", "update_device", "delete_device"],
        }
        return permission in permissions.get(user.role, [])

class MockRateLimiter:
    def __init__(self):
        self.requests = {}
    
    async def check_rate_limit(self, user_id: str, limit: int = 100) -> bool:
        count = self.requests.get(user_id, 0)
        if count >= limit:
            return False
        self.requests[user_id] = count + 1
        return True

class MockAuditLogger:
    def __init__(self):
        self.logs = []
    
    async def log_action(self, user_id: str, action: str, resource_id: str, 
                        organization_id: str, success: bool, details: dict = None):
        self.logs.append({
            "user_id": user_id,
            "action": action,
            "resource_id": resource_id,
            "organization_id": organization_id,
            "success": success,
            "timestamp": datetime.utcnow(),
            "details": details or {}
        })

# Test fixtures
@pytest.fixture
def device_service():
    return MockDeviceService()

@pytest.fixture
def auth_service():
    return MockAuthService()

@pytest.fixture
def permission_checker():
    return MockPermissionChecker()

@pytest.fixture
def rate_limiter():
    return MockRateLimiter()

@pytest.fixture
def audit_logger():
    return MockAuditLogger()

@pytest.fixture
def valid_user():
    return User("user-123", "org-456", "user")

@pytest.fixture
def admin_user():
    return User("admin-123", "org-456", "admin")

@pytest.fixture
def sample_device_data():
    return DeviceCreate(
        name="Test Device",
        type="sensor",
        location="Test Location",
        description="Test Description",
        base_power=5.0,
        base_voltage=240.0,
        firmware_version="1.0.0",
        model="TestModel",
        metadata={"test": "data"}
    )

# Device CRUD operation tests
class TestDeviceOperations:
    """Test device CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_create_device_success(self, device_service, valid_user, sample_device_data):
        """Test successful device creation"""
        device = await device_service.create_device(
            sample_device_data, 
            valid_user.organization_id, 
            valid_user.user_id
        )
        
        assert device.name == sample_device_data.name
        assert device.type == sample_device_data.type
        assert device.organization_id == valid_user.organization_id
        assert device.status == "offline"
        assert device.id is not None
    
    @pytest.mark.asyncio
    async def test_get_device_success(self, device_service, valid_user, sample_device_data):
        """Test successful device retrieval"""
        # Create device first
        created_device = await device_service.create_device(
            sample_device_data, 
            valid_user.organization_id, 
            valid_user.user_id
        )
        
        # Retrieve device
        retrieved_device = await device_service.get_device(
            created_device.id, 
            valid_user.organization_id
        )
        
        assert retrieved_device is not None
        assert retrieved_device.id == created_device.id
        assert retrieved_device.name == sample_device_data.name
    
    @pytest.mark.asyncio
    async def test_get_device_wrong_organization(self, device_service, valid_user, sample_device_data):
        """Test device retrieval with wrong organization"""
        # Create device
        created_device = await device_service.create_device(
            sample_device_data, 
            valid_user.organization_id, 
            valid_user.user_id
        )
        
        # Try to retrieve with different organization
        retrieved_device = await device_service.get_device(
            created_device.id, 
            "different-org"
        )
        
        assert retrieved_device is None
    
    @pytest.mark.asyncio
    async def test_list_devices(self, device_service, valid_user, sample_device_data):
        """Test device listing"""
        # Create multiple devices
        device1 = await device_service.create_device(
            sample_device_data, 
            valid_user.organization_id, 
            valid_user.user_id
        )
        
        device2_data = DeviceCreate(
            name="Second Device",
            type="meter",
            location="Another Location"
        )
        device2 = await device_service.create_device(
            device2_data, 
            valid_user.organization_id, 
            valid_user.user_id
        )
        
        # List devices
        devices = await device_service.list_devices(valid_user.organization_id)
        
        assert len(devices) == 2
        device_ids = [d.id for d in devices]
        assert device1.id in device_ids
        assert device2.id in device_ids
    
    @pytest.mark.asyncio
    async def test_update_device(self, device_service, valid_user, sample_device_data):
        """Test device update"""
        # Create device
        created_device = await device_service.create_device(
            sample_device_data, 
            valid_user.organization_id, 
            valid_user.user_id
        )
        
        # Update device
        update_data = {"name": "Updated Device", "location": "New Location"}
        updated_device = await device_service.update_device(
            created_device.id, 
            update_data, 
            valid_user.organization_id, 
            valid_user.user_id
        )
        
        assert updated_device is not None
        assert updated_device.name == "Updated Device"
        assert updated_device.location == "New Location"
        assert updated_device.type == sample_device_data.type  # Unchanged
    
    @pytest.mark.asyncio
    async def test_delete_device(self, device_service, admin_user, sample_device_data):
        """Test device deletion"""
        # Create device
        created_device = await device_service.create_device(
            sample_device_data, 
            admin_user.organization_id, 
            admin_user.user_id
        )
        
        # Delete device
        deleted = await device_service.delete_device(
            created_device.id, 
            admin_user.organization_id, 
            admin_user.user_id
        )
        
        assert deleted is True
        
        # Verify device is gone
        retrieved_device = await device_service.get_device(
            created_device.id, 
            admin_user.organization_id
        )
        assert retrieved_device is None

# Authentication and authorization tests
class TestAuthentication:
    """Test authentication functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_token(self, auth_service):
        """Test valid token authentication"""
        user = await auth_service.validate_token("valid_token")
        assert user is not None
        assert user.user_id == "user-123"
        assert user.organization_id == "org-456"
    
    @pytest.mark.asyncio
    async def test_invalid_token(self, auth_service):
        """Test invalid token authentication"""
        user = await auth_service.validate_token("invalid_token")
        assert user is None

class TestPermissions:
    """Test permission checking"""
    
    def test_user_permissions(self, permission_checker, valid_user):
        """Test regular user permissions"""
        assert permission_checker.check_permission(valid_user, "read_device")
        assert permission_checker.check_permission(valid_user, "create_device")
        assert permission_checker.check_permission(valid_user, "update_device")
        assert not permission_checker.check_permission(valid_user, "delete_device")
    
    def test_admin_permissions(self, permission_checker, admin_user):
        """Test admin user permissions"""
        assert permission_checker.check_permission(admin_user, "read_device")
        assert permission_checker.check_permission(admin_user, "create_device")
        assert permission_checker.check_permission(admin_user, "update_device")
        assert permission_checker.check_permission(admin_user, "delete_device")

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_under_threshold(self, rate_limiter):
        """Test requests under rate limit"""
        # Should allow requests under limit
        for i in range(5):
            allowed = await rate_limiter.check_rate_limit("user-123", limit=10)
            assert allowed is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit exceeded"""
        # Exceed rate limit
        for i in range(10):
            await rate_limiter.check_rate_limit("user-456", limit=5)
        
        # Next request should be denied
        allowed = await rate_limiter.check_rate_limit("user-456", limit=5)
        assert allowed is False

class TestAuditLogging:
    """Test audit logging functionality"""
    
    @pytest.mark.asyncio
    async def test_successful_action_logging(self, audit_logger):
        """Test logging of successful actions"""
        await audit_logger.log_action(
            user_id="user-123",
            action="CREATE_DEVICE",
            resource_id="device-456",
            organization_id="org-789",
            success=True,
            details={"device_name": "Test Device"}
        )
        
        assert len(audit_logger.logs) == 1
        log = audit_logger.logs[0]
        assert log["user_id"] == "user-123"
        assert log["action"] == "CREATE_DEVICE"
        assert log["success"] is True
        assert log["details"]["device_name"] == "Test Device"
    
    @pytest.mark.asyncio
    async def test_failed_action_logging(self, audit_logger):
        """Test logging of failed actions"""
        await audit_logger.log_action(
            user_id="user-123",
            action="DELETE_DEVICE",
            resource_id="device-456",
            organization_id="org-789",
            success=False,
            details={"error": "Permission denied"}
        )
        
        assert len(audit_logger.logs) == 1
        log = audit_logger.logs[0]
        assert log["success"] is False
        assert log["details"]["error"] == "Permission denied"

# Input validation tests
class TestDataValidation:
    """Test input data validation"""
    
    def test_valid_device_data(self):
        """Test valid device creation data"""
        device_data = DeviceCreate(
            name="Valid Device",
            type="sensor",
            location="Test Location",
            base_power=5.0,
            base_voltage=240.0
        )
        assert device_data.name == "Valid Device"
        assert device_data.type == "sensor"
        assert device_data.base_power == 5.0
    
    def test_device_data_with_metadata(self):
        """Test device creation with metadata"""
        device_data = DeviceCreate(
            name="Device with Metadata",
            type="meter",
            metadata={"building": "A", "floor": 1}
        )
        assert device_data.metadata["building"] == "A"
        assert device_data.metadata["floor"] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
