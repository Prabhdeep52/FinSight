"""Apply migration to add thinking_history column"""
from database.supabase_client import get_supabase_client

def apply_migration():
    sb = get_supabase_client()
    
    print("Applying migration: Add thinking_history column...")
    
    # Read SQL from file
    with open('database/migrations/003_add_thinking_history.sql', 'r') as f:
        sql = f.read()
    
    print(f"SQL to execute:\n{sql}\n")
    
    # Execute SQL using Supabase postgrest API
    # Note: We'll manually add the column using the Python client
    try:
        # Check if column already exists
        result = sb.table('conversations').select('*').limit(1).execute()
        
        if result.data and len(result.data) > 0:
            if 'thinking_history' in result.data[0]:
                print("✅ Column 'thinking_history' already exists!")
                return
        
        print("\n❌ Cannot add column via Supabase client API.")
        print("\nPlease run this SQL manually in Supabase SQL Editor:")
        print("-" * 60)
        print(sql)
        print("-" * 60)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    apply_migration()
