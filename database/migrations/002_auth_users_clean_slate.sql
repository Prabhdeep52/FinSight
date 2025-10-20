-- Alternative migration if you have existing data that needs to be preserved
-- This version will clear existing data before changing the column type

-- Step 1: Backup existing data (optional - run this separately if you want to keep data)
-- CREATE TABLE conversations_backup AS SELECT * FROM conversations;
-- CREATE TABLE messages_backup AS SELECT * FROM messages;

-- Step 2: Clear existing data (since it has invalid user_ids)
DELETE FROM messages;  -- Must delete messages first due to foreign key
DELETE FROM conversations;

-- Step 3: Enable Row Level Security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Step 4: Drop existing foreign key constraint if exists
ALTER TABLE conversations 
  DROP CONSTRAINT IF EXISTS conversations_user_id_fkey;

-- Step 5: Convert user_id from varchar to uuid
ALTER TABLE conversations 
  ALTER COLUMN user_id TYPE uuid USING NULL::uuid;  -- Set all to NULL first

-- Step 6: Add the foreign key constraint
ALTER TABLE conversations
  ADD CONSTRAINT conversations_user_id_fkey 
  FOREIGN KEY (user_id) 
  REFERENCES auth.users(id) 
  ON DELETE CASCADE;

-- Step 7: Create RLS policies for conversations
CREATE POLICY "Users can view their own conversations"
  ON conversations FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own conversations"
  ON conversations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own conversations"
  ON conversations FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own conversations"
  ON conversations FOR DELETE
  USING (auth.uid() = user_id);

-- Step 8: Create RLS policies for messages
CREATE POLICY "Users can view messages from their conversations"
  ON messages FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.session_id = messages.session_id
      AND conversations.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert messages to their conversations"
  ON messages FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.session_id = messages.session_id
      AND conversations.user_id = auth.uid()
    )
  );

-- Step 9: Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
