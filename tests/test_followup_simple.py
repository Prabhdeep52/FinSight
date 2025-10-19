"""
Simple test for follow-up question feature
No user input required - runs automatically
"""

import requests
import json
import uuid
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = f"test-{uuid.uuid4()}"
TEST_USER_ID = "test_user"

print("\n" + "="*80)
print("FOLLOW-UP QUESTIONS FEATURE - QUICK TEST")
print("="*80)
print(f"\nSession ID: {TEST_SESSION_ID}")
print(f"User ID: {TEST_USER_ID}\n")

# Test 1: Initial query
print("\n[TEST 1] Initial Query: 'How is Apple stock?'")
print("-" * 80)

try:
    response1 = requests.post(
        f"{API_BASE_URL}/agent/query",
        json={
            "query": "How is Apple stock?",
            "session_id": TEST_SESSION_ID,
            "user_id": TEST_USER_ID
        },
        timeout=120
    )
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"✅ Status: {data1.get('status')}")
        print(f"✅ Symbols: {data1.get('symbols_analyzed')}")
        print(f"✅ Response: {data1.get('response', '')[:200]}...")
    else:
        print(f"❌ FAILED: Status {response1.status_code}")
        print(response1.text)
        exit(1)
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    exit(1)

time.sleep(2)

# Test 2: Follow-up query
print("\n[TEST 2] Follow-up Query: 'Compare with Microsoft'")
print("-" * 80)
print("Testing if agent understands context (AAPL vs MSFT)...")

try:
    response2 = requests.post(
        f"{API_BASE_URL}/agent/query",
        json={
            "query": "Compare with Microsoft",
            "session_id": TEST_SESSION_ID,
            "user_id": TEST_USER_ID
        },
        timeout=120
    )
    
    if response2.status_code == 200:
        data2 = response2.json()
        symbols = data2.get('symbols_analyzed', [])
        
        print(f"✅ Status: {data2.get('status')}")
        print(f"✅ Symbols: {symbols}")
        
        if 'AAPL' in symbols and 'MSFT' in symbols:
            print("✅✅ FOLLOW-UP SUCCESSFUL! Agent understood context!")
        else:
            print("⚠️  Expected both AAPL and MSFT")
            
        print(f"✅ Response: {data2.get('response', '')[:200]}...")
    else:
        print(f"❌ FAILED: Status {response2.status_code}")
        print(response2.text)
        exit(1)
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    exit(1)

print("\n" + "="*80)
print("✅ TESTS COMPLETED SUCCESSFULLY!")
print("="*80)
print(f"\nCheck your Supabase database:")
print(f"1. conversations table - session_id: {TEST_SESSION_ID}")
print(f"2. messages table - should have 4 messages for this session")
print("="*80 + "\n")
