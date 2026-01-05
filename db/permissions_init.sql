-- Create user_permissions table for granular access control
-- This table stores which permissions each user has been granted

CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    permission_name VARCHAR(50) NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER,
    
    -- Foreign key to users table (assuming it exists in t4alerts database)
    -- CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Ensure a user can't have duplicate permissions
    CONSTRAINT unique_user_permission UNIQUE (user_id, permission_name)
);

-- Create index for faster permission lookups
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_permission_name ON user_permissions(permission_name);

-- Insert comment for documentation
COMMENT ON TABLE user_permissions IS 'Stores granular permissions for users to access specific sections (certificates, errors)';
COMMENT ON COLUMN user_permissions.permission_name IS 'Valid values: view_certificates, view_errors';
