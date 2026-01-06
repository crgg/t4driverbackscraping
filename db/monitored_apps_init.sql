-- Schema for dynamically configured monitored applications
-- This replaces the hardcoded APPS_CONFIG in app/config.py

CREATE TABLE IF NOT EXISTS monitored_apps (
    id SERIAL PRIMARY KEY,
    app_key VARCHAR(50) UNIQUE NOT NULL,
    app_name VARCHAR(255) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    login_path VARCHAR(200) DEFAULT '/login',
    logs_path VARCHAR(200) DEFAULT '/logs',
    username VARCHAR(255) NOT NULL,
    password TEXT NOT NULL,  -- Encrypted using Fernet
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_monitored_apps_active ON monitored_apps(is_active);
CREATE INDEX IF NOT EXISTS idx_monitored_apps_key ON monitored_apps(app_key);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_monitored_apps_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_monitored_apps_timestamp
BEFORE UPDATE ON monitored_apps
FOR EACH ROW
EXECUTE FUNCTION update_monitored_apps_timestamp();
