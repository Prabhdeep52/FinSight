"""
Test script for FinSight LangGraph Financial Agent.
Tests the agent functionality without requiring API keys.
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.utils import logger
from agents.tools.stock_tool import create_stock_data_tool
from agents.tools.analysis_tool import create_financial_analysis_tool


def test_tools():
    """Test the tools independently."""
    print("Testing FinSight Financial Agent Tools")
    print("=" * 50)

    # Test stock tool creation
    print("\n1. Testing Stock Data Tool Creation...")
    try:
        stock_tool = create_stock_data_tool()
        print("   ✓ Stock data tool created successfully")
        print(f"   ✓ Tool name: {stock_tool.name}")
        print(f"   ✓ Tool description: {stock_tool.description[:80]}...")
    except Exception as e:
        assert False, f"Stock tool creation failed: {e}"

    # Test analysis tool creation
    print("\n2. Testing Analysis Tool Creation...")
    try:
        analysis_tool = create_financial_analysis_tool()
        print("   ✓ Analysis tool created successfully")
        print(f"   ✓ Tool name: {analysis_tool.name}")
        print(f"   ✓ Tool description: {analysis_tool.description[:80]}...")
    except Exception as e:
        print(f"   ✗ Analysis tool creation failed: {e}")
        assert False, f"Analysis tool creation failed: {e}"

    # Test analysis tool with mock data
    print("\n3. Testing Analysis Tool with Mock Data...")
    try:
        mock_stock_data = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "current_price": 150.25,
            "market_cap": 2400000000000,
            "pe_ratio": 28.5,
            "eps": 5.89,
            "profit_margin": 22.5,
            "return_on_equity": 18.2,
            "debt_to_equity": 1.2,
            "high_52week": 180.0,
            "low_52week": 120.0,
            "currency": "USD",
        }

        result = analysis_tool._run(json.dumps(mock_stock_data))
        analysis_result = json.loads(result)

        print("   ✓ Analysis completed successfully")
        print(
            f"   ✓ Analysis for: {analysis_result.get('symbol')} - {analysis_result.get('company_name')}"
        )
        print(
            f"   ✓ Key insights generated: {len(analysis_result.get('insights', {}))}"
        )
        print(
            f"   ✓ Recommendations count: {len(analysis_result.get('recommendations', []))}"
        )

    except Exception as e:
        print(f"   ✗ Analysis tool test failed: {e}")
        assert False, f"Analysis tool test failed: {e}"


def test_indian_vs_global_detection():
    """Test the Indian vs Global stock detection logic."""
    print("\n4. Testing Stock Market Detection...")

    try:
        from core.utils import is_indian_stock

        test_cases = [
            ("AAPL", False, "Apple - Global"),
            ("GOOGL", False, "Google - Global"),
            ("MSFT", False, "Microsoft - Global"),
            ("INFY", True, "Infosys - Indian"),
            ("TCS", True, "TCS - Indian"),
            ("RELIANCE", True, "Reliance - Indian"),
            ("WIPRO", True, "Wipro - Indian"),
            ("HDFC", True, "HDFC - Indian"),
        ]

        for symbol, expected, description in test_cases:
            result = is_indian_stock(symbol)
            assert result == expected, f"{symbol}: Expected {expected}, got {result}"
            market = "Indian" if result else "Global"

    except Exception as e:
        print(f"   ✗ Market detection test failed: {e}")
        assert False, f"Market detection test failed: {e}"


def test_agent_without_llm():
    """Test agent components that don't require LLM."""
    print("\n5. Testing Agent Components (No LLM)...")

    try:
        # Test imports
        from agents.langgraph_agent import AgentState

        print("   ✓ Agent state model imported successfully")

        # Test state creation
        state = AgentState(
            user_query="What is the situation of Apple stock?",
            extracted_symbols=["AAPL"],
            current_step="test",
        )
        print("   ✓ Agent state created successfully")
        print(f"   ✓ Query: {state['user_query']}")
        print(f"   ✓ Symbols: {state['extracted_symbols']}")

        return True

    except Exception as e:
        print(f"   ✗ Agent component test failed: {e}")
        assert False, f"Agent component test failed: {e}"


def main():
    """Run all tests."""
    print("FinSight LangGraph Financial Agent - Test Suite")
    print("=" * 60)

    # Configure logging to show our test progress
    logging.basicConfig(level=logging.INFO)

    tests = [test_tools, test_indian_vs_global_detection, test_agent_without_llm]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("\n   Test failed!")
        except Exception as e:
            print(f"\n   Test error: {e}")

    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed! The agent implementation is working correctly.")
        print("\nNext steps:")
        print("1. Configure GOOGLE_API_KEY in .env file for full LLM functionality")
        print("2. Test with actual queries using the /api/v1/agent/query endpoint")
        print(
            "3. Visit http://localhost:8000/docs to see the interactive API documentation"
        )
    else:
        print("✗ Some tests failed. Please check the implementation.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
