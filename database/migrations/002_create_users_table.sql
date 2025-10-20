-- =====================================================
-- Table: users
-- Purpose: Store user information and their associated chat sessions
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY, -- Corresponds to user_id in conversations table
    username VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for users
CREATE INDEX idx_users_created_at ON users(created_at DESC);
