"""Quick script to check database contents"""
from database.supabase_client import get_supabase_client

def check_database():
    sb = get_supabase_client()
    
    # Check conversations
    conversations = sb.table('conversations').select('*').execute()
    print(f"\n=== CONVERSATIONS ({len(conversations.data)} total) ===")
    for conv in conversations.data[:10]:
        print(f"  Session: {conv['session_id']}")
        print(f"  User: {conv['user_id']}")
        print(f"  Title: {conv['title']}")
        print(f"  Created: {conv['created_at']}")
        
        # Check thinking_history
        thinking_history = conv.get('thinking_history', []) or []
        print(f"  Thinking events: {len(thinking_history)}")
        if len(thinking_history) > 0:
            print(f"    First event: {thinking_history[0].get('step', 'unknown')}")
            print(f"    Last event: {thinking_history[-1].get('step', 'unknown')}")
        print(f"  ---")
    
    # Check messages
    messages = sb.table('messages').select('session_id, role, metadata').execute()
    print(f"\n=== MESSAGES ({len(messages.data)} total) ===")
    for msg in messages.data[:5]:
        print(f"  Session: {msg['session_id']}")
        print(f"  Role: {msg['role']}")
        metadata = msg.get('metadata', {}) or {}
        print(f"  Has symbols: {'symbols' in metadata}")
        print(f"  ---")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total conversations: {len(conversations.data)}")
    print(f"Total messages: {len(messages.data)}")
    
    # Count conversations with thinking
    convs_with_thinking = [c for c in conversations.data if len(c.get('thinking_history', []) or []) > 0]
    print(f"Conversations with thinking: {len(convs_with_thinking)}")
    
    if len(convs_with_thinking) > 0:
        total_events = sum(len(c.get('thinking_history', []) or []) for c in convs_with_thinking)
        print(f"Total thinking events across all conversations: {total_events}")

if __name__ == "__main__":
    check_database()
