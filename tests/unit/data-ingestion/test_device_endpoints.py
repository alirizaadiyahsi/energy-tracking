"""
Unit tests for device CRUD endpoints in data-ingestion service
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Mock data models to avoid import issues
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

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
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

class DevicePermission:
    READ_DEVICE = "read_device"
    CREATE_DEVICE = "create_device" 
    UPDATE_DEVICE = "update_device"
    DELETE_DEVICE = "delete_device"

# Mock services and components
mock_device_service = MagicMock()
mock_auth_service = MagicMock()
mock_permission_checker = MagicMock()
mock_rate_limiter = MagicMock()
mock_audit_logger = MagicMock()


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def device_service():
    """Device service instance for testing"""
    return DeviceService()


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return User(
        user_id="test-user-123",
        email="test@example.com",
        roles=["admin"],
        organization_id="test-org-123"
    )


@pytest.fixture
def sample_device_create():
    """Sample device creation data"""
    return DeviceCreate(
        name="Test Device",
        type="meter",
        location="Test Location",
        description="Test device for unit testing",
        base_power=5.0,
        base_voltage=240.0,
        firmware_version="1.0.0",
        model="TestModel",
        metadata={"test": "data"}
    )


@pytest.fixture
def sample_device_response():
    """Sample device response data"""
    return DeviceResponse(
        id="test-device-123",
        name="Test Device",
        type="meter",
        location="Test Location",
        description="Test device for unit testing",
        status="offline",
        base_power=5.0,
        base_voltage=240.0,
        firmware_version="1.0.0",
        model="TestModel",
        metadata={"test": "data"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_seen=None
    )


class TestDeviceEndpoints:
    """Test class for device CRUD endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_device_success(self, mock_db, device_service, mock_user, sample_device_create, sample_device_response):
        """Test successful device creation"""
        # Mock the device service create method
        with patch.object(device_service, 'create_device', return_value=sample_device_response) as mock_create:
            # Mock authentication and permissions
            with patch('api.routes.get_current_user', return_value=mock_user), \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'), \
                 patch('api.routes.AuditLogger.log_device_action'):
                
                client = TestClient(app)
                response = client.post(
                    "/api/v1/data/devices",
                    json=sample_device_create.model_dump(),
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["success"] is True
                assert data["data"]["name"] == "Test Device"
                assert "created successfully" in data["message"]
                
                # Verify service was called with correct parameters
                mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_device_unauthorized(self, sample_device_create):
        """Test device creation without authentication"""
        with patch('api.routes.get_current_user', side_effect=HTTPException(status_code=401)):
            client = TestClient(app)
            response = client.post(
                "/api/v1/data/devices",
                json=sample_device_create.model_dump()
            )
            
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_device_insufficient_permissions(self, mock_user, sample_device_create):
        """Test device creation with insufficient permissions"""
        # Mock user without create permissions
        limited_user = User(
            user_id="test-user-123",
            email="test@example.com",
            roles=["viewer"],
            organization_id="test-org-123"
        )
        
        with patch('api.routes.get_current_user', return_value=limited_user), \
             patch('api.routes.check_device_permission', side_effect=HTTPException(status_code=403)):
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/data/devices",
                json=sample_device_create.model_dump(),
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_create_device_rate_limited(self, mock_user, sample_device_create):
        """Test device creation with rate limiting"""
        with patch('api.routes.get_current_user', return_value=mock_user), \
             patch('api.routes.check_rate_limit', side_effect=HTTPException(status_code=429)):
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/data/devices",
                json=sample_device_create.model_dump(),
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code == 429
    
    @pytest.mark.asyncio
    async def test_get_device_success(self, mock_db, device_service, mock_user, sample_device_response):
        """Test successful device retrieval"""
        with patch.object(device_service, 'get_device', return_value=sample_device_response) as mock_get:
            with patch('api.routes.get_current_user', return_value=mock_user), \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'), \
                 patch('api.routes.AuditLogger.log_device_action'):
                
                client = TestClient(app)
                response = client.get(
                    "/api/v1/data/devices/test-device-123/db",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["id"] == "test-device-123"
                
                mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_device_not_found(self, mock_db, device_service, mock_user):
        """Test device retrieval when device doesn't exist"""
        with patch.object(device_service, 'get_device', return_value=None):
            with patch('api.routes.get_current_user', return_value=mock_user), \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'):
                
                client = TestClient(app)
                response = client.get(
                    "/api/v1/data/devices/nonexistent-device/db",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_device_success(self, mock_db, device_service, mock_user, sample_device_response):
        """Test successful device update"""
        update_data = DeviceUpdate(name="Updated Device Name")
        
        with patch.object(device_service, 'get_device', return_value=sample_device_response), \
             patch.object(device_service, 'update_device', return_value=sample_device_response) as mock_update:
            with patch('api.routes.get_current_user', return_value=mock_user), \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'), \
                 patch('api.routes.AuditLogger.log_device_action'):
                
                client = TestClient(app)
                response = client.put(
                    "/api/v1/data/devices/test-device-123",
                    json=update_data.model_dump(),
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "updated successfully" in data["message"]
    
    @pytest.mark.asyncio
    async def test_delete_device_success(self, mock_db, device_service, mock_user, sample_device_response):
        """Test successful device deletion"""
        with patch.object(device_service, 'get_device', return_value=sample_device_response), \
             patch.object(device_service, 'delete_device', return_value=True) as mock_delete:
            with patch('api.routes.get_current_user', return_value=mock_user), \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'), \
                 patch('api.routes.AuditLogger.log_device_action'):
                
                client = TestClient(app)
                response = client.delete(
                    "/api/v1/data/devices/test-device-123",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["deleted"] is True
    
    @pytest.mark.asyncio
    async def test_list_devices_success(self, mock_db, device_service, mock_user, sample_device_response):
        """Test successful device listing"""
        devices_list = [sample_device_response]
        
        with patch.object(device_service, 'list_devices', return_value=devices_list) as mock_list:
            with patch('api.routes.get_current_user', return_value=mock_user), \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'), \
                 patch('api.routes.AuditLogger.log_device_action'):
                
                client = TestClient(app)
                response = client.get(
                    "/api/v1/data/devices/list",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]) == 1
                assert data["data"][0]["id"] == "test-device-123"
    
    @pytest.mark.asyncio
    async def test_list_devices_with_filters(self, mock_db, device_service, mock_user, sample_device_response):
        """Test device listing with filters"""
        devices_list = [sample_device_response]
        
        with patch.object(device_service, 'list_devices', return_value=devices_list) as mock_list:
            with patch('api.routes.get_current_user', return_value=mock_user), \
                 patch('api.routes.check_rate_limit'), \
                 patch('api.routes.check_device_permission'), \
                 patch('api.routes.AuditLogger.log_device_action'):
                
                client = TestClient(app)
                response = client.get(
                    "/api/v1/data/devices/list?device_type=meter&status=online&limit=50",
                    headers={"Authorization": "Bearer test-token"}
                )
                
                assert response.status_code == 200
                # Verify filters were passed to service
                mock_list.assert_called_once()
                call_kwargs = mock_list.call_args.kwargs
                assert call_kwargs.get('device_type') == 'meter'
                assert call_kwargs.get('status') == 'online'
                assert call_kwargs.get('limit') == 50


class TestDeviceValidation:
    """Test class for device data validation"""
    
    def test_device_create_validation(self):
        """Test device creation data validation"""
        # Valid device data
        valid_data = {
            "name": "Test Device",
            "type": "meter",
            "location": "Test Location"
        }
        device = DeviceCreate(**valid_data)
        assert device.name == "Test Device"
        assert device.type == "meter"
        
        # Invalid device type
        with pytest.raises(ValueError):
            DeviceCreate(name="Test", type="invalid_type")
    
    def test_device_update_validation(self):
        """Test device update data validation"""
        # Valid update data (all fields optional)
        update_data = DeviceUpdate(name="Updated Name")
        assert update_data.name == "Updated Name"
        assert update_data.type is None  # Optional field
        
        # Invalid device type
        with pytest.raises(ValueError):
            DeviceUpdate(type="invalid_type")


class TestPermissionChecking:
    """Test class for permission checking logic"""
    
    def test_role_based_permissions(self):
        """Test role-based device permissions"""
        from core.permissions import PermissionChecker, DevicePermission
        
        # Admin has all permissions
        admin_permissions = PermissionChecker.get_device_permissions_for_role("admin")
        assert DevicePermission.CREATE.value in admin_permissions
        assert DevicePermission.DELETE.value in admin_permissions
        
        # Viewer has limited permissions
        viewer_permissions = PermissionChecker.get_device_permissions_for_role("viewer")
        assert DevicePermission.READ.value in viewer_permissions
        assert DevicePermission.CREATE.value not in viewer_permissions
        assert DevicePermission.DELETE.value not in viewer_permissions
    
    def test_organization_access_control(self):
        """Test organization-based access control"""
        from core.permissions import PermissionChecker
        
        # Same organization - should have access
        assert PermissionChecker.can_access_organization_devices("org-1", "org-1") is True
        
        # Different organization - should not have access
        assert PermissionChecker.can_access_organization_devices("org-1", "org-2") is False
        
        # Super admin (no org) - should have access to all
        assert PermissionChecker.can_access_organization_devices(None, "org-1") is True
        
        # Public device (no org) - should be accessible
        assert PermissionChecker.can_access_organization_devices("org-1", None) is True


class TestRateLimiting:
    """Test class for rate limiting functionality"""
    
    def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiting functionality"""
        from core.permissions import RateLimiter
        
        rate_limiter = RateLimiter()
        user_id = "test-user"
        operation = "create_device"
        
        # First requests should be allowed
        for i in range(5):
            assert rate_limiter.is_allowed(user_id, operation) is True
        
        # Additional requests should be rejected (assuming low limit for testing)
        # Note: This test would need adjustment based on actual limits
    
    def test_rate_limiter_different_users(self):
        """Test rate limiting for different users"""
        from core.permissions import RateLimiter
        
        rate_limiter = RateLimiter()
        operation = "create_device"
        
        # Different users should have separate limits
        assert rate_limiter.is_allowed("user-1", operation) is True
        assert rate_limiter.is_allowed("user-2", operation) is True


class TestAuditLogging:
    """Test class for audit logging functionality"""
    
    def test_audit_logging_device_actions(self):
        """Test audit logging for device actions"""
        from core.permissions import AuditLogger, AuditAction
        
        # This would be enhanced to test actual audit database writes in production
        with patch('core.permissions.logger') as mock_logger:
            AuditLogger.log_device_action(
                user_id="test-user",
                action=AuditAction.DEVICE_CREATED,
                device_id="test-device",
                details={"device_name": "Test Device"}
            )
            
            # Verify audit log was called
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            assert "AUDIT:" in log_call
            assert "device_created" in log_call
