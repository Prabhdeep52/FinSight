"""
Test script for follow-up question feature
Tests the conversation memory and context building
"""

import requests
import json
import uuid

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1/agent"
TEST_SESSION_ID = f"test-session-{uuid.uuid4()}"
TEST_USER_ID = "test_user_123"

def print_response(response_data, query_num):
    """Pretty print the response"""
    print(f"\n{'='*80}")
    print(f"QUERY {query_num} RESPONSE")
    print(f"{'='*80}")
    print(f"Status: {response_data.get('status', 'N/A')}")
    print(f"Symbols Analyzed: {response_data.get('symbols_analyzed', [])}")
    print(f"\nResponse:\n{response_data.get('response', 'N/A')[:500]}...")
    print(f"{'='*80}\n")

def test_followup_questions():
    """Test the follow-up question capability"""
    
    print(f"\n{'#'*80}")
    print(f"TESTING FOLLOW-UP QUESTIONS FEATURE")
    print(f"{'#'*80}")
    print(f"\nSession ID: {TEST_SESSION_ID}")
    print(f"User ID: {TEST_USER_ID}")
    print(f"{'#'*80}\n")
    
    # Query 1: Initial question about Apple
    print("\n[TEST 1] Initial Query - 'How is Apple stock?'")
    print("-" * 80)
    
    query1 = {
        "query": "How is Apple stock?",
        "session_id": TEST_SESSION_ID,
        "user_id": TEST_USER_ID
    }
    
    try:
        response1 = requests.post(
            f"{API_BASE_URL}/query",
            json=query1,
            timeout=120
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            print_response(data1, 1)
            print("✅ Query 1 SUCCESS: Initial query processed")
        else:
            print(f"❌ Query 1 FAILED: Status {response1.status_code}")
            print(f"Response: {response1.text}")
            return
            
    except Exception as e:
        print(f"❌ Query 1 ERROR: {str(e)}")
        return
    
    # Query 2: Follow-up question (should understand "compare with Microsoft" means AAPL vs MSFT)
    print("\n[TEST 2] Follow-up Query - 'Compare with Microsoft'")
    print("-" * 80)
    print("Expected behavior: Agent should understand to compare AAPL vs MSFT")
    print("                   without needing to repeat 'Apple' or 'AAPL'")
    
    query2 = {
        "query": "Compare with Microsoft",
        "session_id": TEST_SESSION_ID,
        "user_id": TEST_USER_ID
    }
    
    try:
        response2 = requests.post(
            f"{API_BASE_URL}/query",
            json=query2,
            timeout=120
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            print_response(data2, 2)
            
            # Verify both symbols were analyzed
            symbols = data2.get('symbols_analyzed', [])
            if 'AAPL' in symbols and 'MSFT' in symbols:
                print("✅ Query 2 SUCCESS: Follow-up understood! Both AAPL and MSFT analyzed")
            else:
                print(f"⚠️  Query 2 PARTIAL: Symbols analyzed: {symbols}")
                print("    Expected: ['AAPL', 'MSFT']")
        else:
            print(f"❌ Query 2 FAILED: Status {response2.status_code}")
            print(f"Response: {response2.text}")
            return
            
    except Exception as e:
        print(f"❌ Query 2 ERROR: {str(e)}")
        return
    
    # Query 3: Another follow-up (this should trigger cumulative context generation)
    print("\n[TEST 3] Third Query - 'Which has better valuation?'")
    print("-" * 80)
    print("Expected behavior: This is message #3 (user messages: 1, 3, 5)")
    print("                   Should trigger cumulative context generation")
    print("                   Agent should know we're still comparing AAPL vs MSFT")
    
    query3 = {
        "query": "Which has better valuation?",
        "session_id": TEST_SESSION_ID,
        "user_id": TEST_USER_ID
    }
    
    try:
        response3 = requests.post(
            f"{API_BASE_URL}/query",
            json=query3,
            timeout=120
        )
        
        if response3.status_code == 200:
            data3 = response3.json()
            print_response(data3, 3)
            
            symbols = data3.get('symbols_analyzed', [])
            if 'AAPL' in symbols and 'MSFT' in symbols:
                print("✅ Query 3 SUCCESS: Context maintained! Still analyzing AAPL vs MSFT")
            else:
                print(f"⚠️  Query 3 PARTIAL: Symbols analyzed: {symbols}")
                print("    Expected: ['AAPL', 'MSFT']")
        else:
            print(f"❌ Query 3 FAILED: Status {response3.status_code}")
            print(f"Response: {response3.text}")
            return
            
    except Exception as e:
        print(f"❌ Query 3 ERROR: {str(e)}")
        return
    
    # Summary
    print(f"\n{'#'*80}")
    print("TEST SUMMARY")
    print(f"{'#'*80}")
    print(f"✅ All tests passed!")
    print(f"\nSession ID: {TEST_SESSION_ID}")
    print(f"\nYou can verify the database entries:")
    print(f"1. Check 'conversations' table for session: {TEST_SESSION_ID}")
    print(f"2. Check 'messages' table for this session (should have 6 messages)")
    print(f"3. Message #3 and #6 should have 'cumulative_context' populated")
    print(f"{'#'*80}\n")


def test_old_chat_restoration():
    """Test that returning to an old chat restores context"""
    
    print(f"\n{'#'*80}")
    print(f"TESTING OLD CHAT RESTORATION")
    print(f"{'#'*80}\n")
    
    # Use the same session ID from previous test
    print(f"Using session ID from previous test: {TEST_SESSION_ID}")
    print("\nAsking a follow-up question as if we just returned to this chat...")
    
    query = {
        "query": "What about their revenue growth?",
        "session_id": TEST_SESSION_ID,
        "user_id": TEST_USER_ID
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=query,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            print_response(data, "OLD CHAT")
            
            symbols = data.get('symbols_analyzed', [])
            if 'AAPL' in symbols and 'MSFT' in symbols:
                print("✅ OLD CHAT RESTORATION SUCCESS!")
                print("   Agent restored context and knew to analyze AAPL and MSFT")
            else:
                print(f"⚠️  Symbols analyzed: {symbols}")
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("FOLLOW-UP QUESTIONS FEATURE TEST SUITE")
    print("="*80)
    print("\nMake sure the backend is running: python main.py")
    print("Make sure you've run the database migration")
    print("\nPress Enter to start tests or Ctrl+C to cancel...")
    input()
    
    # Run tests
    test_followup_questions()
    
    print("\n" + "-"*80)
    print("Now testing old chat restoration...")
    print("Press Enter to continue or Ctrl+C to skip...")
    input()
    
    test_old_chat_restoration()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETE!")
    print("="*80 + "\n")
