"""
Stock data tool for LangGraph agents.
Provides LLM with ability to fetch stock data through direct function calls.
"""

import json
from typing import Dict, Any, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from core.utils import logger


class StockDataInput(BaseModel):
    """Input schema for stock data tool."""

    symbol: str = Field(
        description="Stock symbol to fetch data for (e.g., AAPL, GOOGL, INFY, TCS). "
        "Can be from any market - Indian or global. "
        "Examples: AAPL (Apple), GOOGL (Google), INFY (Infosys), TCS (Tata Consultancy)"
    )


class StockDataTool(BaseTool):
    """
    Tool for fetching comprehensive stock data directly from the financial agent.

    This tool can fetch data for both Indian and global stocks.
    Uses direct function calls instead of HTTP requests to avoid circular dependencies.
    """

    name: str = "get_stock_data"
    description: str = (
        "Fetch comprehensive financial data for any stock symbol. "
        "Use this tool when you need current stock information including "
        "price, market cap, P/E ratio, financial metrics, and company details. "
        "Works for both Indian stocks (like INFY, TCS, RELIANCE) and "
        "global stocks (like AAPL, GOOGL, MSFT). "
        "Input should be just the stock symbol."
    )
    args_schema: Type[BaseModel] = StockDataInput

    def _run(self, symbol: str) -> str:
        """
        Execute the stock data retrieval using direct function calls.

        Args:
            symbol: Stock symbol to fetch data for

        Returns:
            JSON string containing stock data or error information
        """
        logger.info(f"StockDataTool: Starting data fetch for symbol: {symbol}")

        try:
            # Clean and validate symbol
            clean_symbol = symbol.strip().upper()
            logger.info(f"StockDataTool: Cleaned symbol: {clean_symbol}")

            # Import here to avoid circular imports
            from data_services.financial_agent import FinancialAgent

            logger.info(
                f"StockDataTool: Using direct FinancialAgent call for {clean_symbol}"
            )

            # Create financial agent and fetch data directly
            financial_agent = FinancialAgent()
            data = financial_agent.fetch_stock_data(clean_symbol)

            logger.info(f"StockDataTool: Successfully fetched data for {clean_symbol}")
            logger.debug(
                f"StockDataTool: Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
            )

            # Return the data as JSON string for LLM to process
            return json.dumps(data, indent=2)

        except Exception as e:
            logger.error(f"StockDataTool: Unexpected error for {symbol}: {str(e)}")
            error_data = {
                "error": True,
                "message": f"Error fetching stock data: {str(e)}",
                "symbol": symbol,
                "error_type": "UnexpectedException",
            }
            return json.dumps(error_data, indent=2)

    async def _arun(self, symbol: str) -> str:
        """Async version of the run method."""
        logger.info(f"StockDataTool: Async execution requested for symbol: {symbol}")
        # For now, we'll use the sync version
        # In future, this can be implemented with aiohttp for better performance
        return self._run(symbol)


def create_stock_data_tool() -> StockDataTool:
    """
    Factory function to create a stock data tool.

    Returns:
        Configured StockDataTool instance
    """
    logger.info("Creating StockDataTool with direct function call approach")
    tool = StockDataTool()
    logger.info("StockDataTool created successfully")
    return tool
