-- Migration Script: Add RBAC System to Existing Energy Tracking Database
-- ========================================================================
-- This script adds the Role-Based Access Control system to an existing database
-- Run this AFTER the initial database setup if RBAC wasn't included initially

-- Step 1: Add new enum types if they don't exist
DO $$ BEGIN
    CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'pending_activation');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE permission_action AS ENUM ('create', 'read', 'update', 'delete', 'execute', 'manage');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE resource_type AS ENUM ('device', 'device_group', 'user', 'role', 'alert', 'analytics', 'dashboard', 'system');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Step 2: Add new columns to existing users table
DO $$ BEGIN
    -- Add new columns to users table
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS username VARCHAR(100) UNIQUE;
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS department VARCHAR(100);
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS position VARCHAR(100);
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS status user_status DEFAULT 'active';
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP WITH TIME ZONE;
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT TRUE;
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(255);
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(255);
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS password_reset_expires TIMESTAMP WITH TIME ZONE;
    ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES auth.users(id);
    
    -- Update existing users to active status
    UPDATE auth.users SET status = 'active' WHERE status IS NULL;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Some columns might already exist: %', SQLERRM;
END $$;

-- Step 3: Create new RBAC tables (will skip if already exist)
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

CREATE TABLE IF NOT EXISTS auth.user_roles (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES auth.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID REFERENCES auth.users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS auth.role_permissions (
    role_id UUID REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES auth.permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID REFERENCES auth.users(id),
    PRIMARY KEY (role_id, permission_id)
);

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

CREATE TABLE IF NOT EXISTS auth.user_organizations (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES auth.organizations(id) ON DELETE CASCADE,
    role_in_org VARCHAR(100),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (user_id, organization_id)
);

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

-- Step 4: Add organization support to existing tables
DO $$ BEGIN
    ALTER TABLE energy.devices ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES auth.users(id);
    ALTER TABLE energy.devices ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES auth.organizations(id);
    ALTER TABLE energy.device_groups ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES auth.organizations(id);
    ALTER TABLE energy.device_groups ADD COLUMN IF NOT EXISTS access_level VARCHAR(50) DEFAULT 'private';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Some device table columns might already exist: %', SQLERRM;
END $$;

-- Step 5: Create indexes for new tables
CREATE INDEX IF NOT EXISTS idx_users_email_new ON auth.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username_new ON auth.users(username);
CREATE INDEX IF NOT EXISTS idx_users_status_new ON auth.users(status);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id_new ON auth.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id_new ON auth.user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id_new ON auth.role_permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id_new ON auth.user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_resource_new ON auth.user_permissions(resource_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id_new ON auth.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token_new ON auth.user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id_new ON auth.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp_new ON auth.audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_action_new ON auth.audit_log(action);
CREATE INDEX IF NOT EXISTS idx_organizations_name_new ON auth.organizations(name);
CREATE INDEX IF NOT EXISTS idx_user_organizations_user_new ON auth.user_organizations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_organizations_org_new ON auth.user_organizations(organization_id);
CREATE INDEX IF NOT EXISTS idx_devices_owner_new ON energy.devices(owner_id);
CREATE INDEX IF NOT EXISTS idx_devices_organization_new ON energy.devices(organization_id);

-- Step 6: Create/Update triggers for new tables
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for new tables
DO $$ BEGIN
    CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON auth.roles 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON auth.organizations 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Step 7: Insert default data if not exists
INSERT INTO auth.organizations (name, display_name, description) VALUES
    ('default', 'Default Organization', 'Default organization for initial setup')
ON CONFLICT (name) DO NOTHING;

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

-- Insert permissions (will be a long list - this is a sample)
INSERT INTO auth.permissions (name, display_name, description, resource_type, action, is_system_permission) VALUES
    ('user_create', 'Create Users', 'Create new user accounts', 'user', 'create', TRUE),
    ('user_read', 'View Users', 'View user information and lists', 'user', 'read', TRUE),
    ('user_update', 'Update Users', 'Modify user accounts and profiles', 'user', 'update', TRUE),
    ('user_delete', 'Delete Users', 'Delete user accounts', 'user', 'delete', TRUE),
    ('user_manage', 'Manage Users', 'Full user account management', 'user', 'manage', TRUE),
    ('device_create', 'Create Devices', 'Add new devices to the system', 'device', 'create', TRUE),
    ('device_read', 'View Devices', 'View device information and status', 'device', 'read', TRUE),
    ('device_update', 'Update Devices', 'Modify device configurations', 'device', 'update', TRUE),
    ('device_delete', 'Delete Devices', 'Remove devices from system', 'device', 'delete', TRUE),
    ('device_manage', 'Manage Devices', 'Full device management including maintenance', 'device', 'manage', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Step 8: Assign super_admin role to existing admin users
INSERT INTO auth.user_roles (user_id, role_id, assigned_by) 
SELECT u.id, r.id, u.id 
FROM auth.users u, auth.roles r 
WHERE u.is_superuser = TRUE AND r.name = 'super_admin'
ON CONFLICT DO NOTHING;

-- Step 9: Create default organization membership for existing users
INSERT INTO auth.user_organizations (user_id, organization_id, role_in_org)
SELECT u.id, o.id, 'member'
FROM auth.users u, auth.organizations o
WHERE o.name = 'default'
  AND NOT EXISTS (
      SELECT 1 FROM auth.user_organizations uo 
      WHERE uo.user_id = u.id AND uo.organization_id = o.id
  );

-- Step 10: Update existing devices to belong to default organization
UPDATE energy.devices 
SET organization_id = (SELECT id FROM auth.organizations WHERE name = 'default')
WHERE organization_id IS NULL;

RAISE NOTICE 'RBAC Migration completed successfully!';
RAISE NOTICE 'Please review the new roles and permissions, and assign appropriate roles to users.';
RAISE NOTICE 'Check the auth.roles and auth.permissions tables for available options.';
RAISE NOTICE 'Use auth.user_roles table to assign roles to users.';
