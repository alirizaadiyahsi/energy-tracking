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

-- Create users table
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Create device groups table
CREATE TABLE IF NOT EXISTS energy.device_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES energy.device_groups(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
CREATE INDEX IF NOT EXISTS idx_alerts_status ON energy.alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON energy.alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON energy.alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_device_id ON energy.alerts(device_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_device_id ON analytics.forecasts(device_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_period ON analytics.forecasts USING gist(forecast_period);

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

-- Insert default admin user (password: admin123)
-- Note: In production, change this password immediately
INSERT INTO auth.users (email, hashed_password, full_name, is_superuser) 
VALUES (
    'admin@energy-tracking.com', 
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 
    'System Administrator', 
    TRUE
) ON CONFLICT (email) DO NOTHING;

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
    d.device_type
FROM energy.alerts a
LEFT JOIN energy.devices d ON a.device_id = d.id
WHERE a.created_at >= NOW() - INTERVAL '7 days'
ORDER BY a.created_at DESC;

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
