-- Migration: Add thinking_history column to conversations
-- Description: Store all thinking events for a conversation in one column
-- Date: 2025-10-20

-- Add thinking_history column to conversations table
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS thinking_history JSONB DEFAULT '[]'::jsonb;

-- Create GIN index for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_conversations_thinking_history 
ON conversations USING GIN (thinking_history);

-- Add comment
COMMENT ON COLUMN conversations.thinking_history IS 'Array of all thinking events from agent execution, appended after each query completion';

-- Completion message
DO $$
BEGIN
    RAISE NOTICE 'Migration 003_add_thinking_history completed successfully!';
    RAISE NOTICE 'Added thinking_history column to conversations table';
END $$;
