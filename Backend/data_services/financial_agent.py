"""
Financial Agent for FinSight system.
Routes stock data requests to appropriate tools and returns unified financial data.
"""

from typing import Dict, Any, Optional
from Backend.core.utils import logger, is_indian_stock, clean_symbol, validate_symbol
from Backend.tools.screener_api import ScreenerAPI
from Backend.tools.alphavantage_api import AlphaVantageAPI


class FinancialAgent:
    """
    Main financial data agent that coordinates between different data sources.
    Determines the appropriate API to use based on stock symbol and market.
    """

    def __init__(self):
        self.screener_api = ScreenerAPI()
        self.alphavantage_api = AlphaVantageAPI()

    def fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch comprehensive stock data for any symbol.

        Args:
            symbol: Stock symbol (e.g., 'INFY', 'AAPL', 'GOOGL')

        Returns:
            Dictionary containing standardized financial data
        """
        try:
            # Validate and clean symbol
            if not validate_symbol(symbol):
                return {"error": True, "message": f"Invalid symbol format: {symbol}"}

            clean_sym = clean_symbol(symbol)
            logger.info(f"Processing request for symbol: {clean_sym}")

            # Route to appropriate API based on market detection
            if is_indian_stock(clean_sym):
                logger.info(f"Routing {clean_sym} to Indian market (Screener.in)")
                data = self.screener_api.fetch_company_data(clean_sym)
            else:
                logger.info(f"Routing {clean_sym} to global market (Alpha Vantage)")
                data = self.alphavantage_api.fetch_company_overview(clean_sym)

            # Enhance data with agent metadata
            if not data.get("error"):
                data["agent_info"] = {
                    "processed_by": "FinancialAgent",
                    "symbol_processed": clean_sym,
                    "market_type": "indian" if is_indian_stock(clean_sym) else "global",
                    "version": "1.0.0",
                }

            return data

        except Exception as e:
            logger.error(f"Error in FinancialAgent for {symbol}: {str(e)}")
            return {
                "error": True,
                "message": f"Agent processing failed: {str(e)}",
                "symbol": symbol,
            }

    def fetch_multiple_stocks(self, symbols: list) -> Dict[str, Any]:
        """
        Fetch data for multiple stocks.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary with results for each symbol
        """
        results = {}

        for symbol in symbols:
            try:
                results[symbol] = self.fetch_stock_data(symbol)
            except Exception as e:
                results[symbol] = {"error": True, "message": str(e)}

        return {
            "batch_results": results,
            "total_symbols": len(symbols),
            "successful": len([r for r in results.values() if not r.get("error")]),
            "failed": len([r for r in results.values() if r.get("error")]),
        }

    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get market classification and routing information for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with market information
        """
        clean_sym = clean_symbol(symbol)
        is_indian = is_indian_stock(clean_sym)

        return {
            "symbol": clean_sym,
            "original_symbol": symbol,
            "market_type": "indian" if is_indian else "global",
            "data_source": "screener.in" if is_indian else "alpha_vantage",
            "currency": "INR" if is_indian else "USD",
            "exchange_hints": ["NSE", "BSE"]
            if is_indian
            else ["NASDAQ", "NYSE", "TSX"],
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Check health status of all integrated APIs.

        Returns:
            Dictionary with health status of each component
        """
        logger.info("Performing health check on all APIs")

        screener_health = self.screener_api.health_check()
        alphavantage_health = self.alphavantage_api.health_check()

        overall_status = "healthy"
        if (
            screener_health.get("status") != "healthy"
            or alphavantage_health.get("status") != "healthy"
        ):
            overall_status = "degraded"

        return {
            "overall_status": overall_status,
            "components": {
                "screener_api": screener_health,
                "alphavantage_api": alphavantage_health,
            },
            "agent_version": "1.0.0",
        }

    def get_supported_markets(self) -> Dict[str, Any]:
        """Get information about supported markets and exchanges."""
        return {
            "indian_markets": {
                "exchanges": ["NSE", "BSE"],
                "data_source": "screener.in",
                "currency": "INR",
                "symbol_examples": ["INFY", "TCS", "RELIANCE"],
            },
            "global_markets": {
                "exchanges": ["NASDAQ", "NYSE", "TSX", "LSE"],
                "data_source": "alpha_vantage",
                "currency": "USD",
                "symbol_examples": ["AAPL", "GOOGL", "MSFT"],
            },
            "total_coverage": "Indian + Global markets",
        }
