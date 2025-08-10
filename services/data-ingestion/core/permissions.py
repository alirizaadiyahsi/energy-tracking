"""
Permission definitions and checking logic for device management.
"""

from enum import Enum
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class DevicePermission(Enum):
    """Device-specific permissions"""
    CREATE = "device_create"
    READ = "device_read"
    UPDATE = "device_update"
    DELETE = "device_delete"
    MANAGE = "device_manage"
    LIST = "device_list"

class SystemRole(Enum):
    """System roles with device access"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    DEVICE_TECHNICIAN = "device_technician"
    ANALYST = "analyst"
    VIEWER = "viewer"

class PermissionChecker:
    """Utility class for permission checking logic"""
    
    @staticmethod
    def get_device_permissions_for_role(role: str) -> List[str]:
        """Get device permissions for a given role"""
        role_permissions = {
            SystemRole.SUPER_ADMIN.value: [
                DevicePermission.CREATE.value,
                DevicePermission.READ.value,
                DevicePermission.UPDATE.value,
                DevicePermission.DELETE.value,
                DevicePermission.MANAGE.value,
                DevicePermission.LIST.value,
            ],
            SystemRole.ADMIN.value: [
                DevicePermission.CREATE.value,
                DevicePermission.READ.value,
                DevicePermission.UPDATE.value,
                DevicePermission.DELETE.value,
                DevicePermission.LIST.value,
            ],
            SystemRole.MANAGER.value: [
                DevicePermission.CREATE.value,
                DevicePermission.READ.value,
                DevicePermission.UPDATE.value,
                DevicePermission.LIST.value,
            ],
            SystemRole.OPERATOR.value: [
                DevicePermission.READ.value,
                DevicePermission.UPDATE.value,
                DevicePermission.LIST.value,
            ],
            SystemRole.DEVICE_TECHNICIAN.value: [
                DevicePermission.CREATE.value,
                DevicePermission.READ.value,
                DevicePermission.UPDATE.value,
                DevicePermission.DELETE.value,
                DevicePermission.LIST.value,
            ],
            SystemRole.ANALYST.value: [
                DevicePermission.READ.value,
                DevicePermission.LIST.value,
            ],
            SystemRole.VIEWER.value: [
                DevicePermission.READ.value,
                DevicePermission.LIST.value,
            ],
        }
        
        return role_permissions.get(role, [])
    
    @staticmethod
    def has_device_permission(user_roles: List[str], required_permission: str) -> bool:
        """Check if user roles include required device permission"""
        for role in user_roles:
            role_permissions = PermissionChecker.get_device_permissions_for_role(role)
            if required_permission in role_permissions:
                return True
        return False
    
    @staticmethod
    def can_access_organization_devices(user_org_id: Optional[str], device_org_id: Optional[str]) -> bool:
        """Check if user can access devices from specific organization"""
        # Super admins can access all organizations
        if user_org_id is None:
            return True
            
        # Users can access devices from their own organization
        if user_org_id == device_org_id:
            return True
            
        # Devices without organization are public (for backward compatibility)
        if device_org_id is None:
            return True
            
        return False
    
    @staticmethod
    def get_accessible_device_filter(user_org_id: Optional[str]) -> Optional[str]:
        """Get SQL filter for accessible devices based on user organization"""
        if user_org_id is None:
            # Super admin - no filter
            return None
        else:
            # Organization user - filter by organization or public devices
            return f"(organization_id = '{user_org_id}' OR organization_id IS NULL)"


class AuditAction(Enum):
    """Audit actions for device operations"""
    DEVICE_CREATED = "device_created"
    DEVICE_UPDATED = "device_updated"
    DEVICE_DELETED = "device_deleted"
    DEVICE_VIEWED = "device_viewed"
    DEVICE_LISTED = "device_listed"

class AuditLogger:
    """Audit logging for device operations"""
    
    @staticmethod
    def log_device_action(
        user_id: str,
        action: AuditAction,
        device_id: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """Log device-related user action"""
        audit_entry = {
            "user_id": user_id,
            "action": action.value,
            "device_id": device_id,
            "details": details or {},
            "timestamp": None  # Will be set by database
        }
        
        # Log to application logs (in production, this would go to audit database)
        logger.info(f"AUDIT: {audit_entry}")
        
        # TODO: In production, implement database audit logging
        # await audit_service.log_action(audit_entry)


# Rate limiting configuration
DEVICE_RATE_LIMITS = {
    "create_device": {"limit": 10, "window": 60},  # 10 creates per minute
    "update_device": {"limit": 30, "window": 60},  # 30 updates per minute
    "delete_device": {"limit": 5, "window": 60},   # 5 deletes per minute
    "list_devices": {"limit": 100, "window": 60},  # 100 lists per minute
    "get_device": {"limit": 200, "window": 60},    # 200 gets per minute
}

class RateLimiter:
    """Simple in-memory rate limiter (in production, use Redis)"""
    
    def __init__(self):
        self.requests = {}  # {user_id: {operation: [(timestamp, count)]}}
    
    def is_allowed(self, user_id: str, operation: str) -> bool:
        """Check if user is within rate limits for operation"""
        import time
        
        if operation not in DEVICE_RATE_LIMITS:
            return True
            
        limit_config = DEVICE_RATE_LIMITS[operation]
        limit = limit_config["limit"]
        window = limit_config["window"]
        
        current_time = time.time()
        
        # Initialize user tracking if needed
        if user_id not in self.requests:
            self.requests[user_id] = {}
        if operation not in self.requests[user_id]:
            self.requests[user_id][operation] = []
        
        # Clean old requests outside window
        user_requests = self.requests[user_id][operation]
        self.requests[user_id][operation] = [
            (timestamp, count) for timestamp, count in user_requests
            if current_time - timestamp < window
        ]
        
        # Count current requests
        current_count = sum(count for _, count in self.requests[user_id][operation])
        
        if current_count >= limit:
            return False
        
        # Add current request
        self.requests[user_id][operation].append((current_time, 1))
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()
