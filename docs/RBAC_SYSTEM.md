# User Roles and Permissions System
# =================================

This document describes the comprehensive Role-Based Access Control (RBAC) system implemented in the Energy Tracking IoT Platform.

## 🔐 System Overview

The platform implements a flexible RBAC system that supports:
- **Multi-tenancy** with organization-based access control
- **Role-based permissions** with granular resource access
- **Direct user permissions** for specific resource access
- **Hierarchical device groups** with inheritance
- **Comprehensive audit logging** for all user activities
- **Session management** with token-based authentication

## 👥 User Management

### User Status Types
- `active` - Normal active user
- `inactive` - Temporarily disabled user
- `suspended` - User suspended due to policy violations
- `pending_activation` - New user awaiting email verification

### User Attributes
```sql
- id (UUID) - Unique user identifier
- email - Primary authentication credential
- username - Optional display name
- full_name - User's full name
- department - Organizational department
- position - Job title or position
- phone - Contact phone number
- status - Current user status
- last_login - Last successful login timestamp
- failed_login_attempts - Security tracking
- locked_until - Account lockout timestamp
- email_verified - Email verification status
```

## 🏢 Organization Structure

### Multi-Tenant Support
The system supports multiple organizations with isolated data access:

```sql
Organizations:
- id (UUID) - Unique organization identifier
- name - Organization short name
- display_name - Full organization name
- domain - Email domain for automatic assignment
- settings - JSON configuration
- is_active - Organization status
```

### User-Organization Relationships
- Users can belong to multiple organizations
- Each relationship has a specific role within the organization
- Organization-scoped data access controls

## 🎭 Role System

### Predefined System Roles

#### 1. Super Administrator (`super_admin`)
- **Purpose**: Complete system control across all organizations
- **Access**: All permissions across all resources
- **Use Case**: Platform administrators and system maintenance

#### 2. Administrator (`admin`)  
- **Purpose**: Full organization management
- **Permissions**:
  - User management (create, read, update, delete)
  - Role assignment (except super_admin)
  - Device management (full access)
  - Alert management (full access)
  - Analytics (create and execute)
  - Dashboard management
  - System monitoring (read-only)

#### 3. Manager (`manager`)
- **Purpose**: Department or team leadership
- **Permissions**:
  - User management (read, update)
  - Device management (create, read, update)
  - Device group management
  - Alert management (create, read, update)
  - Analytics (read, create, execute)
  - Dashboard management

#### 4. Operator (`operator`)
- **Purpose**: Day-to-day device operations
- **Permissions**:
  - Device monitoring (read, update configurations)
  - Alert handling (read, acknowledge)
  - Basic analytics (read)
  - Dashboard viewing

#### 5. Data Analyst (`analyst`)
- **Purpose**: Data analysis and reporting
- **Permissions**:
  - Device data (read-only)
  - Advanced analytics (create, execute)
  - Custom dashboards (create, update)
  - Report generation

#### 6. Viewer (`viewer`)
- **Purpose**: Read-only dashboard access
- **Permissions**:
  - Device information (read-only)
  - Dashboard viewing
  - Alert viewing
  - Basic analytics (read-only)

#### 7. Device Technician (`device_technician`)
- **Purpose**: Device installation and maintenance
- **Permissions**:
  - Device management (full access)
  - Device configuration
  - Maintenance alerts
  - Field service dashboards

## 🔑 Permission System

### Permission Structure
Each permission consists of:
- **Resource Type**: What the permission applies to
- **Action**: What action is allowed
- **Conditions**: Optional JSON-based conditions

### Resource Types
- `user` - User account management
- `role` - Role and permission management
- `device` - IoT device management
- `device_group` - Device organization
- `alert` - Alert and notification system
- `analytics` - Data analysis and forecasting
- `dashboard` - Dashboard and visualization
- `system` - System administration

### Actions
- `create` - Create new resources
- `read` - View resource information
- `update` - Modify existing resources
- `delete` - Remove resources
- `execute` - Execute operations (analytics, reports)
- `manage` - Full resource management

### Permission Examples

```sql
-- Device Management Permissions
device_create     - Create new devices
device_read       - View device information
device_update     - Modify device configurations
device_delete     - Remove devices from system
device_manage     - Full device lifecycle management

-- Analytics Permissions
analytics_read    - View analytics dashboards
analytics_create  - Create custom analytics
analytics_execute - Run forecasting models
analytics_manage  - Full analytics system administration
```

## 🔐 Access Control Implementation

### Role-Based Access
```sql
-- Check if user has permission through roles
SELECT auth.user_has_permission(
    'user_id_here'::UUID,
    'device_read',
    'specific_device_id'::UUID  -- Optional resource-specific check
);
```

### Direct Permissions
Users can have direct permissions outside of roles:
```sql
-- Grant specific user access to specific device
INSERT INTO auth.user_permissions (user_id, permission_id, resource_id)
VALUES ('user_id', 'device_manage_permission_id', 'device_id');
```

### Organization-Scoped Access
```sql
-- Get user's accessible devices based on organization membership
SELECT * FROM auth.get_user_accessible_devices('user_id'::UUID);
```

## 🛡️ Security Features

### Session Management
- JWT-based authentication with refresh tokens
- Session tracking with IP and user agent
- Automatic session cleanup for expired tokens
- Concurrent session limits

### Account Security
- Failed login attempt tracking
- Account lockout after multiple failed attempts
- Password complexity requirements
- Email verification for new accounts
- Password reset with secure tokens

### Audit Logging
All user activities are automatically logged:
```sql
-- Automatic audit logging for all CRUD operations
- User actions (login, logout, password changes)
- Resource modifications (device updates, role changes)
- Permission grants and revocations
- Administrative actions
```

## 📊 Data Access Patterns

### Device Access Control
```sql
-- Users can access devices if they:
1. Own the device (owner_id = user_id)
2. Have system-wide device permissions
3. Belong to the same organization as the device
4. Have been granted specific device permissions
```

### Hierarchical Device Groups
```sql
-- Device groups support inheritance:
- Parent group permissions cascade to child groups
- Organization-level groups restrict access by membership
- Access levels: public, private, restricted
```

### Alert Access
```sql
-- Alert visibility based on:
1. Device access permissions
2. Alert severity level permissions
3. Organization membership
4. Direct alert permissions
```

## 🔧 Administrative Functions

### User Management
```sql
-- Create new user
INSERT INTO auth.users (email, hashed_password, full_name, department)
VALUES ('user@example.com', 'hashed_pw', 'John Doe', 'Engineering');

-- Assign role to user
INSERT INTO auth.user_roles (user_id, role_id, assigned_by)
VALUES ('user_id', 'role_id', 'admin_user_id');
```

### Permission Management
```sql
-- Grant direct permission
INSERT INTO auth.user_permissions (user_id, permission_id, resource_id)
VALUES ('user_id', 'permission_id', 'resource_id');

-- Revoke permission
UPDATE auth.user_permissions 
SET is_active = FALSE 
WHERE user_id = 'user_id' AND permission_id = 'permission_id';
```

### Session Management
```sql
-- Cleanup expired sessions
SELECT auth.cleanup_expired_sessions();

-- Force logout user
UPDATE auth.user_sessions 
SET is_active = FALSE 
WHERE user_id = 'user_id';
```

## 📈 Monitoring and Reports

### User Activity Reports
```sql
-- Recent user activities
SELECT * FROM auth.audit_log 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Failed login attempts
SELECT user_id, COUNT(*) as failed_attempts
FROM auth.audit_log 
WHERE action = 'LOGIN_FAILED' 
  AND timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY user_id;
```

### Permission Reports
```sql
-- Users with specific permissions
SELECT u.email, u.full_name, upv.permission_name
FROM auth.users u
JOIN auth.user_permissions_view upv ON u.id = upv.user_id
WHERE upv.permission_name = 'device_manage';

-- Role permission matrix
SELECT r.name as role_name, p.name as permission_name
FROM auth.roles r
JOIN auth.role_permissions rp ON r.id = rp.role_id
JOIN auth.permissions p ON rp.permission_id = p.id
ORDER BY r.name, p.resource_type, p.action;
```

## 🚀 Implementation Examples

### API Authentication Middleware
```python
async def check_permission(user_id: UUID, permission: str, resource_id: UUID = None):
    result = await database.fetch_one(
        "SELECT auth.user_has_permission($1, $2, $3)",
        user_id, permission, resource_id
    )
    return result[0] if result else False
```

### Device Access Control
```python
@require_permission("device_read")
async def get_device(device_id: UUID, current_user: User):
    # User permission already checked by decorator
    return await device_service.get_device(device_id)
```

### Organization Context
```python
@require_organization_membership
async def get_organization_devices(org_id: UUID, current_user: User):
    # User organization membership already verified
    return await device_service.get_devices_by_organization(org_id)
```

This comprehensive RBAC system ensures secure, scalable, and auditable access control for the entire IoT energy tracking platform.
