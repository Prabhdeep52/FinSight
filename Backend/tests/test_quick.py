"""
Quick test to verify memory manager initialization
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1/agent"

def test_quick():
    """Quick test of basic functionality"""
    print("\n" + "="*80)
    print("QUICK TEST: Memory Manager Initialization")
    print("="*80 + "\n")
    
    query = {
        "query": "How is Apple stock?",
        "session_id": "test-quick-123",
        "user_id": "test_user"
    }
    
    try:
        print(f"Sending request to {API_BASE_URL}/query...")
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=query,
            timeout=120
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Symbols analyzed: {data.get('symbols_analyzed', [])}")
            print(f"Response length: {len(data.get('response', ''))}")
        else:
            print(f"❌ FAILED")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_quick()
