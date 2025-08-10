-- Initialize the Energy Tracking Database
-- This script sets up the initial database structure

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS energy;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Create enum types
CREATE TYPE device_status AS ENUM ('online', 'offline', 'maintenance', 'error');
CREATE TYPE device_type AS ENUM ('meter', 'sensor', 'gateway', 'controller');
CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'error', 'critical');
CREATE TYPE alert_status AS ENUM ('open', 'acknowledged', 'resolved', 'closed');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'pending_activation');
CREATE TYPE permission_action AS ENUM ('create', 'read', 'update', 'delete', 'execute', 'manage');
CREATE TYPE resource_type AS ENUM ('device', 'device_group', 'user', 'role', 'alert', 'analytics', 'dashboard', 'system');

-- Create users table
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    department VARCHAR(100),
    position VARCHAR(100),
    status user_status DEFAULT 'pending_activation',
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Create roles table
CREATE TABLE IF NOT EXISTS auth.roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Create permissions table
CREATE TABLE IF NOT EXISTS auth.permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    resource_type resource_type NOT NULL,
    action permission_action NOT NULL,
    conditions JSONB DEFAULT '{}',
    is_system_permission BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user roles junction table
CREATE TABLE IF NOT EXISTS auth.user_roles (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES auth.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES auth.users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, role_id)
);

-- Create role permissions junction table
CREATE TABLE IF NOT EXISTS auth.role_permissions (
    role_id UUID REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES auth.permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID REFERENCES auth.users(id),
    PRIMARY KEY (role_id, permission_id)
);

-- Create user permissions table (direct permissions outside of roles)
CREATE TABLE IF NOT EXISTS auth.user_permissions (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES auth.permissions(id) ON DELETE CASCADE,
    resource_id UUID,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID REFERENCES auth.users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, permission_id, COALESCE(resource_id, '00000000-0000-0000-0000-000000000000'::UUID))
);

-- Create user sessions table
CREATE TABLE IF NOT EXISTS auth.user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create audit log table
CREATE TABLE IF NOT EXISTS auth.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create devices table
CREATE TABLE IF NOT EXISTS energy.devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    device_type device_type NOT NULL,
    mac_address VARCHAR(17) UNIQUE,
    ip_address INET,
    location VARCHAR(255),
    description TEXT,
    status device_status DEFAULT 'offline',
    last_seen TIMESTAMP WITH TIME ZONE,
    configuration JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    owner_id UUID REFERENCES auth.users(id),
    organization_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Create organizations table for multi-tenant support
CREATE TABLE IF NOT EXISTS auth.organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    domain VARCHAR(255),
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Create user organizations table
CREATE TABLE IF NOT EXISTS auth.user_organizations (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES auth.organizations(id) ON DELETE CASCADE,
    role_in_org VARCHAR(100),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, organization_id)
);

-- Add organization reference to devices
ALTER TABLE energy.devices 
ADD CONSTRAINT fk_devices_organization 
FOREIGN KEY (organization_id) REFERENCES auth.organizations(id);

-- Create device groups table
CREATE TABLE IF NOT EXISTS energy.device_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES energy.device_groups(id),
    organization_id UUID REFERENCES auth.organizations(id),
    access_level VARCHAR(50) DEFAULT 'private', -- 'public', 'private', 'restricted'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Create device group memberships
CREATE TABLE IF NOT EXISTS energy.device_group_memberships (
    device_id UUID REFERENCES energy.devices(id) ON DELETE CASCADE,
    group_id UUID REFERENCES energy.device_groups(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (device_id, group_id)
);

-- Create alerts table
CREATE TABLE IF NOT EXISTS energy.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID REFERENCES energy.devices(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity alert_severity DEFAULT 'info',
    status alert_status DEFAULT 'open',
    rule_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES auth.users(id)
);

-- Create alert rules table
CREATE TABLE IF NOT EXISTS energy.alert_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    conditions JSONB NOT NULL,
    severity alert_severity DEFAULT 'warning',
    is_active BOOLEAN DEFAULT TRUE,
    device_group_id UUID REFERENCES energy.device_groups(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Create data sources table
CREATE TABLE IF NOT EXISTS energy.data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID REFERENCES energy.devices(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    unit VARCHAR(50),
    description TEXT,
    configuration JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analytics models table
CREATE TABLE IF NOT EXISTS analytics.models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    description TEXT,
    configuration JSONB DEFAULT '{}',
    model_data BYTEA,
    accuracy_metrics JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    trained_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Create forecasts table
CREATE TABLE IF NOT EXISTS analytics.forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES analytics.models(id) ON DELETE CASCADE,
    device_id UUID REFERENCES energy.devices(id) ON DELETE CASCADE,
    forecast_type VARCHAR(100) NOT NULL,
    forecast_data JSONB NOT NULL,
    forecast_period TSTZRANGE NOT NULL,
    confidence_level NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_devices_status ON energy.devices(status);
CREATE INDEX IF NOT EXISTS idx_devices_type ON energy.devices(device_type);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON energy.devices(last_seen);
CREATE INDEX IF NOT EXISTS idx_devices_owner ON energy.devices(owner_id);
CREATE INDEX IF NOT EXISTS idx_devices_organization ON energy.devices(organization_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON energy.alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON energy.alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON energy.alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_device_id ON energy.alerts(device_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_device_id ON analytics.forecasts(device_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_period ON analytics.forecasts USING gist(forecast_period);

-- Auth-related indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON auth.users(username);
CREATE INDEX IF NOT EXISTS idx_users_status ON auth.users(status);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON auth.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON auth.user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id ON auth.role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON auth.user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_resource ON auth.user_permissions(resource_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON auth.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON auth.user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON auth.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON auth.audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON auth.audit_log(action);
CREATE INDEX IF NOT EXISTS idx_organizations_name ON auth.organizations(name);
CREATE INDEX IF NOT EXISTS idx_user_organizations_user ON auth.user_organizations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_organizations_org ON auth.user_organizations(organization_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON auth.roles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON auth.organizations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON energy.devices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_device_groups_updated_at BEFORE UPDATE ON energy.device_groups 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON energy.alerts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON energy.alert_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON energy.data_sources 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON analytics.models 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    excluded_cols TEXT[] = ARRAY['updated_at', 'last_accessed'];
BEGIN
    IF TG_OP = 'DELETE' THEN
        old_data = to_jsonb(OLD);
        INSERT INTO auth.audit_log (user_id, action, resource_type, resource_id, old_values)
        VALUES (
            NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID,
            'DELETE',
            TG_TABLE_NAME,
            (OLD.id)::UUID,
            old_data
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        old_data = to_jsonb(OLD) - excluded_cols;
        new_data = to_jsonb(NEW) - excluded_cols;
        IF old_data != new_data THEN
            INSERT INTO auth.audit_log (user_id, action, resource_type, resource_id, old_values, new_values)
            VALUES (
                NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID,
                'UPDATE',
                TG_TABLE_NAME,
                (NEW.id)::UUID,
                old_data,
                new_data
            );
        END IF;
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        new_data = to_jsonb(NEW);
        INSERT INTO auth.audit_log (user_id, action, resource_type, resource_id, new_values)
        VALUES (
            NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID,
            'INSERT',
            TG_TABLE_NAME,
            (NEW.id)::UUID,
            new_data
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create audit triggers for important tables
CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_roles AFTER INSERT OR UPDATE OR DELETE ON auth.roles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_user_roles AFTER INSERT OR UPDATE OR DELETE ON auth.user_roles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_devices AFTER INSERT OR UPDATE OR DELETE ON energy.devices
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_device_groups AFTER INSERT OR UPDATE OR DELETE ON energy.device_groups
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_alerts AFTER INSERT OR UPDATE OR DELETE ON energy.alerts
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Insert default admin user (password: admin123)
-- Note: In production, change this password immediately
INSERT INTO auth.users (email, hashed_password, full_name, is_superuser, status) 
VALUES (
    'admin@energy-tracking.com', 
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 
    'System Administrator', 
    TRUE,
    'active'
) ON CONFLICT (email) DO NOTHING;

-- Insert simple admin user (password: admin123)
INSERT INTO auth.users (email, hashed_password, full_name, is_superuser, status) 
VALUES (
    'admin@mail.com', 
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Local Administrator',
    TRUE,
    'active'
) ON CONFLICT (email) DO NOTHING;

-- Insert default organization
INSERT INTO auth.organizations (name, display_name, description) VALUES
    ('default', 'Default Organization', 'Default organization for initial setup')
ON CONFLICT DO NOTHING;

-- Insert default roles
INSERT INTO auth.roles (name, display_name, description, is_system_role) VALUES
    ('super_admin', 'Super Administrator', 'Full system access and management', TRUE),
    ('admin', 'Administrator', 'Organization administration and management', TRUE),
    ('manager', 'Manager', 'Department or team management', TRUE),
    ('operator', 'Operator', 'Device operation and monitoring', TRUE),
    ('analyst', 'Data Analyst', 'Data analysis and reporting', TRUE),
    ('viewer', 'Viewer', 'Read-only access to dashboards and data', TRUE),
    ('device_technician', 'Device Technician', 'Device installation and maintenance', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insert system permissions
INSERT INTO auth.permissions (name, display_name, description, resource_type, action, is_system_permission) VALUES
    -- User management permissions
    ('user_create', 'Create Users', 'Create new user accounts', 'user', 'create', TRUE),
    ('user_read', 'View Users', 'View user information and lists', 'user', 'read', TRUE),
    ('user_update', 'Update Users', 'Modify user accounts and profiles', 'user', 'update', TRUE),
    ('user_delete', 'Delete Users', 'Delete user accounts', 'user', 'delete', TRUE),
    ('user_manage', 'Manage Users', 'Full user account management', 'user', 'manage', TRUE),
    
    -- Role management permissions
    ('role_create', 'Create Roles', 'Create new roles and permissions', 'role', 'create', TRUE),
    ('role_read', 'View Roles', 'View roles and permissions', 'role', 'read', TRUE),
    ('role_update', 'Update Roles', 'Modify roles and permissions', 'role', 'update', TRUE),
    ('role_delete', 'Delete Roles', 'Delete roles', 'role', 'delete', TRUE),
    ('role_manage', 'Manage Roles', 'Full role and permission management', 'role', 'manage', TRUE),
    
    -- Device management permissions
    ('device_create', 'Create Devices', 'Add new devices to the system', 'device', 'create', TRUE),
    ('device_read', 'View Devices', 'View device information and status', 'device', 'read', TRUE),
    ('device_update', 'Update Devices', 'Modify device configurations', 'device', 'update', TRUE),
    ('device_delete', 'Delete Devices', 'Remove devices from system', 'device', 'delete', TRUE),
    ('device_manage', 'Manage Devices', 'Full device management including maintenance', 'device', 'manage', TRUE),
    
    -- Device group permissions
    ('device_group_create', 'Create Device Groups', 'Create device groups and hierarchies', 'device_group', 'create', TRUE),
    ('device_group_read', 'View Device Groups', 'View device group information', 'device_group', 'read', TRUE),
    ('device_group_update', 'Update Device Groups', 'Modify device groups', 'device_group', 'update', TRUE),
    ('device_group_delete', 'Delete Device Groups', 'Delete device groups', 'device_group', 'delete', TRUE),
    ('device_group_manage', 'Manage Device Groups', 'Full device group management', 'device_group', 'manage', TRUE),
    
    -- Alert management permissions
    ('alert_create', 'Create Alerts', 'Create alert rules and notifications', 'alert', 'create', TRUE),
    ('alert_read', 'View Alerts', 'View alerts and notifications', 'alert', 'read', TRUE),
    ('alert_update', 'Update Alerts', 'Acknowledge and modify alerts', 'alert', 'update', TRUE),
    ('alert_delete', 'Delete Alerts', 'Delete alerts and rules', 'alert', 'delete', TRUE),
    ('alert_manage', 'Manage Alerts', 'Full alert system management', 'alert', 'manage', TRUE),
    
    -- Analytics permissions
    ('analytics_read', 'View Analytics', 'View analytics dashboards and reports', 'analytics', 'read', TRUE),
    ('analytics_create', 'Create Analytics', 'Create custom analytics and reports', 'analytics', 'create', TRUE),
    ('analytics_execute', 'Execute Analytics', 'Run analytics and generate forecasts', 'analytics', 'execute', TRUE),
    ('analytics_manage', 'Manage Analytics', 'Full analytics system management', 'analytics', 'manage', TRUE),
    
    -- Dashboard permissions
    ('dashboard_read', 'View Dashboards', 'View dashboards and visualizations', 'dashboard', 'read', TRUE),
    ('dashboard_create', 'Create Dashboards', 'Create custom dashboards', 'dashboard', 'create', TRUE),
    ('dashboard_update', 'Update Dashboards', 'Modify dashboards and layouts', 'dashboard', 'update', TRUE),
    ('dashboard_delete', 'Delete Dashboards', 'Delete custom dashboards', 'dashboard', 'delete', TRUE),
    ('dashboard_manage', 'Manage Dashboards', 'Full dashboard management', 'dashboard', 'manage', TRUE),
    
    -- System permissions
    ('system_read', 'View System Info', 'View system status and configuration', 'system', 'read', TRUE),
    ('system_manage', 'Manage System', 'Full system administration', 'system', 'manage', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Assign permissions to roles
INSERT INTO auth.role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM auth.roles r, auth.permissions p 
WHERE r.name = 'super_admin' 
ON CONFLICT DO NOTHING;

INSERT INTO auth.role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM auth.roles r, auth.permissions p 
WHERE r.name = 'admin' AND p.name IN (
    'user_create', 'user_read', 'user_update', 'user_delete',
    'role_read', 'role_update',
    'device_create', 'device_read', 'device_update', 'device_delete', 'device_manage',
    'device_group_create', 'device_group_read', 'device_group_update', 'device_group_delete',
    'alert_create', 'alert_read', 'alert_update', 'alert_delete',
    'analytics_read', 'analytics_create', 'analytics_execute',
    'dashboard_read', 'dashboard_create', 'dashboard_update', 'dashboard_delete',
    'system_read'
) ON CONFLICT DO NOTHING;

INSERT INTO auth.role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM auth.roles r, auth.permissions p 
WHERE r.name = 'manager' AND p.name IN (
    'user_read', 'user_update',
    'device_read', 'device_update', 'device_create',
    'device_group_read', 'device_group_update', 'device_group_create',
    'alert_read', 'alert_update', 'alert_create',
    'analytics_read', 'analytics_create', 'analytics_execute',
    'dashboard_read', 'dashboard_create', 'dashboard_update'
) ON CONFLICT DO NOTHING;

INSERT INTO auth.role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM auth.roles r, auth.permissions p 
WHERE r.name = 'operator' AND p.name IN (
    'device_read', 'device_update',
    'device_group_read',
    'alert_read', 'alert_update',
    'analytics_read',
    'dashboard_read'
) ON CONFLICT DO NOTHING;

INSERT INTO auth.role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM auth.roles r, auth.permissions p 
WHERE r.name = 'analyst' AND p.name IN (
    'device_read',
    'device_group_read',
    'alert_read',
    'analytics_read', 'analytics_create', 'analytics_execute',
    'dashboard_read', 'dashboard_create', 'dashboard_update'
) ON CONFLICT DO NOTHING;

INSERT INTO auth.role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM auth.roles r, auth.permissions p 
WHERE r.name = 'viewer' AND p.name IN (
    'device_read',
    'device_group_read',
    'alert_read',
    'analytics_read',
    'dashboard_read'
) ON CONFLICT DO NOTHING;

INSERT INTO auth.role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM auth.roles r, auth.permissions p 
WHERE r.name = 'device_technician' AND p.name IN (
    'device_read', 'device_update', 'device_create', 'device_manage',
    'device_group_read',
    'alert_read', 'alert_update',
    'dashboard_read'
) ON CONFLICT DO NOTHING;

-- Assign super_admin role to admin user
INSERT INTO auth.user_roles (user_id, role_id, assigned_by) 
SELECT u.id, r.id, u.id 
FROM auth.users u, auth.roles r 
WHERE u.email = 'admin@energy-tracking.com' AND r.name = 'super_admin'
ON CONFLICT DO NOTHING;

-- Assign super_admin role to simple admin user
INSERT INTO auth.user_roles (user_id, role_id, assigned_by) 
SELECT u.id, r.id, u.id 
FROM auth.users u, auth.roles r 
WHERE u.email = 'admin@mail.com' AND r.name = 'super_admin'
ON CONFLICT DO NOTHING;

-- Insert default device groups
INSERT INTO energy.device_groups (name, description) VALUES
    ('All Devices', 'Root group containing all devices'),
    ('Smart Meters', 'Electrical energy meters'),
    ('Temperature Sensors', 'Temperature monitoring devices'),
    ('Motion Sensors', 'Motion detection devices'),
    ('Gateways', 'Network gateways and bridges')
ON CONFLICT DO NOTHING;

-- Insert sample alert rules
INSERT INTO energy.alert_rules (name, description, conditions, severity) VALUES
    (
        'High Energy Consumption', 
        'Alert when energy consumption exceeds threshold',
        '{"metric": "energy_kwh", "operator": "gt", "value": 100, "duration": "5m"}',
        'warning'
    ),
    (
        'Device Offline', 
        'Alert when device has not been seen for extended period',
        '{"metric": "last_seen", "operator": "lt", "value": "30m"}',
        'error'
    ),
    (
        'Temperature Anomaly', 
        'Alert for abnormal temperature readings',
        '{"metric": "temperature", "operator": "outside_range", "min": -10, "max": 50}',
        'warning'
    )
ON CONFLICT DO NOTHING;

-- Create a view for device status summary
CREATE OR REPLACE VIEW energy.device_status_summary AS
SELECT 
    device_type,
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY device_type), 2) as percentage
FROM energy.devices
GROUP BY device_type, status
ORDER BY device_type, status;

-- Create a view for recent alerts
CREATE OR REPLACE VIEW energy.recent_alerts AS
SELECT 
    a.id,
    a.title,
    a.description,
    a.severity,
    a.status,
    a.created_at,
    d.name as device_name,
    d.device_type,
    d.organization_id
FROM energy.alerts a
LEFT JOIN energy.devices d ON a.device_id = d.id
WHERE a.created_at >= NOW() - INTERVAL '7 days'
ORDER BY a.created_at DESC;

-- Create a view for user permissions (combining role and direct permissions)
CREATE OR REPLACE VIEW auth.user_permissions_view AS
-- Permissions from roles
SELECT DISTINCT
    ur.user_id,
    p.id as permission_id,
    p.name as permission_name,
    p.resource_type,
    p.action,
    'role' as source,
    r.name as source_name,
    NULL as resource_id,
    NULL as expires_at
FROM auth.user_roles ur
JOIN auth.role_permissions rp ON ur.role_id = rp.role_id
JOIN auth.permissions p ON rp.permission_id = p.id
JOIN auth.roles r ON ur.role_id = r.id
WHERE ur.is_active = TRUE 
  AND (ur.expires_at IS NULL OR ur.expires_at > NOW())

UNION ALL

-- Direct user permissions
SELECT 
    up.user_id,
    p.id as permission_id,
    p.name as permission_name,
    p.resource_type,
    p.action,
    'direct' as source,
    'direct_permission' as source_name,
    up.resource_id,
    up.expires_at
FROM auth.user_permissions up
JOIN auth.permissions p ON up.permission_id = p.id
WHERE up.is_active = TRUE 
  AND (up.expires_at IS NULL OR up.expires_at > NOW());

-- Create a function to check user permissions
CREATE OR REPLACE FUNCTION auth.user_has_permission(
    p_user_id UUID,
    p_permission_name VARCHAR,
    p_resource_id UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    has_permission BOOLEAN := FALSE;
BEGIN
    -- Check if user has the permission (either from role or direct)
    SELECT EXISTS (
        SELECT 1 
        FROM auth.user_permissions_view upv
        WHERE upv.user_id = p_user_id 
          AND upv.permission_name = p_permission_name
          AND (p_resource_id IS NULL OR upv.resource_id IS NULL OR upv.resource_id = p_resource_id)
          AND (upv.expires_at IS NULL OR upv.expires_at > NOW())
    ) INTO has_permission;
    
    RETURN has_permission;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to get user's accessible devices
CREATE OR REPLACE FUNCTION auth.get_user_accessible_devices(
    p_user_id UUID
)
RETURNS TABLE (
    device_id UUID,
    device_name VARCHAR(255),
    device_type device_type,
    access_level VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.name,
        d.device_type,
        CASE 
            WHEN d.owner_id = p_user_id THEN 'owner'
            WHEN auth.user_has_permission(p_user_id, 'device_manage') THEN 'manage'
            WHEN auth.user_has_permission(p_user_id, 'device_update') THEN 'write'
            WHEN auth.user_has_permission(p_user_id, 'device_read') THEN 'read'
            ELSE 'none'
        END as access_level
    FROM energy.devices d
    LEFT JOIN auth.user_organizations uo ON d.organization_id = uo.organization_id
    WHERE 
        -- User owns the device
        d.owner_id = p_user_id
        -- Or user has system-wide device permissions
        OR auth.user_has_permission(p_user_id, 'device_read')
        -- Or user belongs to the same organization
        OR (uo.user_id = p_user_id AND uo.is_active = TRUE)
    ORDER BY d.name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to log user activities
CREATE OR REPLACE FUNCTION auth.log_user_activity(
    p_user_id UUID,
    p_action VARCHAR(100),
    p_resource_type VARCHAR(100),
    p_resource_id UUID DEFAULT NULL,
    p_details JSONB DEFAULT '{}'::JSONB
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO auth.audit_log (
        user_id,
        action,
        resource_type,
        resource_id,
        new_values,
        ip_address,
        user_agent
    ) VALUES (
        p_user_id,
        p_action,
        p_resource_type,
        p_resource_id,
        p_details,
        INET(COALESCE(current_setting('app.client_ip', TRUE), '127.0.0.1')),
        current_setting('app.user_agent', TRUE)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to clean up expired sessions
CREATE OR REPLACE FUNCTION auth.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM auth.user_sessions 
    WHERE expires_at < NOW() OR is_active = FALSE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get role hierarchy
CREATE OR REPLACE FUNCTION auth.get_role_permissions(p_role_id UUID)
RETURNS TABLE (
    permission_id UUID,
    permission_name VARCHAR(100),
    display_name VARCHAR(255),
    resource_type resource_type,
    action permission_action,
    conditions JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.name,
        p.display_name,
        p.resource_type,
        p.action,
        p.conditions
    FROM auth.permissions p
    JOIN auth.role_permissions rp ON p.id = rp.permission_id
    WHERE rp.role_id = p_role_id
    ORDER BY p.resource_type, p.action;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant permissions
GRANT USAGE ON SCHEMA energy TO postgres;
GRANT USAGE ON SCHEMA auth TO postgres;
GRANT USAGE ON SCHEMA analytics TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA energy TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA energy TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO postgres;
