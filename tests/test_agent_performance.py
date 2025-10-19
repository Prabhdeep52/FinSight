"""
Test script to compare performance of original vs optimized agent.
Run this to see the difference in LLM calls and execution time.
"""

import time
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Test both agents
def test_single_stock():
    """Test single stock query on both agents."""
    query = "How is Apple stock doing currently?"
    
    print("\n" + "="*80)
    print("TEST 1: Single Stock Query")
    print("="*80)
    print(f"Query: {query}\n")
    
    # Test Original Agent
    print("--- ORIGINAL AGENT ---")
    os.environ['USE_OPTIMIZED_AGENT'] = 'false'
    
    from agents.langgraph_agent import create_financial_agent
    
    start = time.time()
    agent = create_financial_agent()
    result = agent.process_query(query)
    duration = time.time() - start
    
    print(f"✓ Completed in {duration:.1f}s")
    print(f"✓ Response length: {len(result['response'])} characters")
    print(f"✓ Symbols analyzed: {result['symbols_analyzed']}")
    
    # Test Optimized Agent
    print("\n--- OPTIMIZED AGENT ---")
    os.environ['USE_OPTIMIZED_AGENT'] = 'true'
    
    from agents.langgraph_agent_optimized import create_optimized_financial_agent
    
    start = time.time()
    optimized_agent = create_optimized_financial_agent()
    result = optimized_agent.process_query(query)
    duration = time.time() - start
    
    print(f"✓ Completed in {duration:.1f}s")
    print(f"✓ Response length: {len(result['response'])} characters")
    print(f"✓ Symbols analyzed: {result['symbols_analyzed']}")


def test_comparison():
    """Test comparison query on both agents."""
    query = "Compare Apple and Microsoft for short-term investment"
    
    print("\n" + "="*80)
    print("TEST 2: Comparison Query (2 Stocks)")
    print("="*80)
    print(f"Query: {query}\n")
    
    # Test Original Agent
    print("--- ORIGINAL AGENT ---")
    os.environ['USE_OPTIMIZED_AGENT'] = 'false'
    
    from agents.langgraph_agent import create_financial_agent
    
    start = time.time()
    agent = create_financial_agent()
    result = agent.process_query(query)
    duration = time.time() - start
    
    print(f"✓ Completed in {duration:.1f}s")
    print(f"✓ Response length: {len(result['response'])} characters")
    print(f"✓ Symbols analyzed: {result['symbols_analyzed']}")
    
    # Test Optimized Agent
    print("\n--- OPTIMIZED AGENT ---")
    os.environ['USE_OPTIMIZED_AGENT'] = 'true'
    
    from agents.langgraph_agent_optimized import create_optimized_financial_agent
    
    start = time.time()
    optimized_agent = create_optimized_financial_agent()
    result = optimized_agent.process_query(query)
    duration = time.time() - start
    
    print(f"✓ Completed in {duration:.1f}s")
    print(f"✓ Response length: {len(result['response'])} characters")
    print(f"✓ Symbols analyzed: {result['symbols_analyzed']}")


if __name__ == "__main__":
    print("\n🚀 Agent Performance Comparison Test")
    print("This will compare the original agentic loop vs optimized hybrid approach.\n")
    
    # Run tests
    test_single_stock()
    test_comparison()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("""
Expected Improvements:
- Single Stock:  7 LLM calls → 3 LLM calls (57% reduction)
- Comparison:   15 LLM calls → 4 LLM calls (73% reduction)
- Speed:        50-67% faster execution
- Tokens:       60-75% reduction

Check the logs to see actual LLM call counts!
    """)
