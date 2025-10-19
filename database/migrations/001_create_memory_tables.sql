-- Migration: Create memory tables for conversation continuity
-- Description: Two-tier memory system with conversations and messages
-- Author: InvestIQ Team
-- Date: 2024

-- =====================================================
-- Table: conversations
-- Purpose: Store conversation sessions
-- =====================================================
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    title TEXT DEFAULT 'New Conversation',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT conversations_user_session_unique UNIQUE (user_id, session_id)
);

-- Create indexes for conversations
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);


-- =====================================================
-- Table: messages
-- Purpose: Store conversation messages with metadata
-- =====================================================
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    cumulative_context TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key
    CONSTRAINT fk_messages_session
        FOREIGN KEY (session_id) 
        REFERENCES conversations(session_id)
        ON DELETE CASCADE
);

-- Create indexes for messages
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_session_created ON messages(session_id, created_at DESC);

-- GIN index for efficient JSONB queries on metadata
CREATE INDEX idx_messages_metadata ON messages USING GIN (metadata);


-- =====================================================
-- Function: Update updated_at timestamp
-- Purpose: Auto-update updated_at on conversation changes
-- =====================================================
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET updated_at = NOW()
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update conversation timestamp when message added
CREATE TRIGGER trigger_update_conversation_timestamp
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION update_conversation_timestamp();


-- =====================================================
-- Function: Auto-generate conversation title
-- Purpose: Generate title from first user message
-- =====================================================
CREATE OR REPLACE FUNCTION generate_conversation_title()
RETURNS TRIGGER AS $$
DECLARE
    first_msg TEXT;
BEGIN
    -- Only for user messages
    IF NEW.role = 'user' THEN
        -- Check if this is the first message in conversation
        SELECT content INTO first_msg
        FROM messages
        WHERE session_id = NEW.session_id AND role = 'user'
        ORDER BY created_at ASC
        LIMIT 1;
        
        -- If this is the first message, update conversation title
        IF first_msg IS NOT NULL THEN
            UPDATE conversations
            SET title = CASE
                WHEN LENGTH(first_msg) > 60 THEN LEFT(first_msg, 57) || '...'
                ELSE first_msg
            END
            WHERE session_id = NEW.session_id AND title = 'New Conversation';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-generate title from first message
CREATE TRIGGER trigger_generate_conversation_title
AFTER INSERT ON messages
FOR EACH ROW
EXECUTE FUNCTION generate_conversation_title();


-- =====================================================
-- Sample Queries (for reference)
-- =====================================================

-- Get all conversations for a user
-- SELECT * FROM conversations WHERE user_id = 'user_123' ORDER BY updated_at DESC;

-- Get conversation with messages
-- SELECT 
--     c.session_id,
--     c.title,
--     c.created_at,
--     c.updated_at,
--     COUNT(m.id) as message_count
-- FROM conversations c
-- LEFT JOIN messages m ON c.session_id = m.session_id
-- WHERE c.user_id = 'user_123'
-- GROUP BY c.session_id, c.title, c.created_at, c.updated_at
-- ORDER BY c.updated_at DESC;

-- Get messages for a session
-- SELECT * FROM messages WHERE session_id = 'abc-123' ORDER BY created_at ASC;

-- Get last cumulative context for a session
-- SELECT cumulative_context, created_at
-- FROM messages
-- WHERE session_id = 'abc-123' AND cumulative_context IS NOT NULL
-- ORDER BY created_at DESC
-- LIMIT 1;

-- Search conversations by metadata (e.g., find sessions analyzing AAPL)
-- SELECT DISTINCT session_id
-- FROM messages
-- WHERE metadata @> '{"symbols": ["AAPL"]}'
-- ORDER BY created_at DESC;


-- =====================================================
-- Grant Permissions (adjust as needed for your setup)
-- =====================================================

-- Grant access to authenticated users (Supabase default)
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Create RLS policies if needed
-- CREATE POLICY "Users can view own conversations" ON conversations
--     FOR SELECT USING (auth.uid()::text = user_id);

-- CREATE POLICY "Users can insert own conversations" ON conversations
--     FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- CREATE POLICY "Users can view own messages" ON messages
--     FOR SELECT USING (
--         session_id IN (SELECT session_id FROM conversations WHERE user_id = auth.uid()::text)
--     );

-- CREATE POLICY "Users can insert own messages" ON messages
--     FOR INSERT WITH CHECK (
--         session_id IN (SELECT session_id FROM conversations WHERE user_id = auth.uid()::text)
--     );


-- =====================================================
-- Completion Message
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE 'Migration 001_create_memory_tables completed successfully!';
    RAISE NOTICE 'Created tables: conversations, messages';
    RAISE NOTICE 'Created indexes for optimal query performance';
    RAISE NOTICE 'Created triggers for auto-updating timestamps and titles';
END $$;
