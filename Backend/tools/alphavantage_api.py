"""
Alpha Vantage API tool for fetching global stock data.
Uses Alpha Vantage's REST API to get financial information for global stocks.
Includes Supabase caching for improved performance and reduced API calls.
"""

import requests
import threading
from typing import Dict, Any, Optional
from core.utils import (
    logger,
    safe_float,
    standardize_financial_data,
    handle_api_error,
)
from core.constants import (
    ALPHAVANTAGE_BASE_URL,
    ALPHAVANTAGE_FUNCTIONS,
    DEFAULT_CURRENCY,
)
from config.settings import get_settings
from database.supabase_client import SupabaseManager


class AlphaVantageAPI:
    """Client for fetching global stock data from Alpha Vantage API."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = ALPHAVANTAGE_BASE_URL
        self.api_key = self.settings.alphavantage_api_key
        self.session = requests.Session()

        # Initialize Supabase manager if credentials are available
        try:
            if self.settings.supabase_url and self.settings.supabase_anon_key:
                self.db = SupabaseManager()
                logger.info(
                    "AlphaVantageAPI: Successfully initialized with Supabase caching"
                )
            else:
                self.db = None
                logger.warning(
                    "AlphaVantageAPI: Supabase credentials not found, caching disabled"
                )
        except Exception as e:
            logger.error(f"AlphaVantageAPI: Failed to initialize Supabase: {str(e)}")
            self.db = None

    def fetch_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch company overview data from cache or Alpha Vantage.

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')

        Returns:
            Dictionary containing financial metrics
        """
        logger.info(f"AlphaVantageAPI: LLM requested data for symbol: {symbol}")

        if not self.api_key:
            logger.error("AlphaVantageAPI: No Alpha Vantage API key configured")
            return {"error": True, "message": "Alpha Vantage API key not configured"}

        # Try to get data from Supabase cache first
        if self.db:
            try:
                cached_data = self.db.get_stock_data(symbol)
                if cached_data:
                    logger.info(
                        f"AlphaVantageAPI: Returning cached data from Supabase for {symbol}"
                    )
                    # Add cache metadata
                    cached_data["cache_info"] = {
                        "cache_hit": True,
                        "data_source": "supabase_cache",
                    }
                    return cached_data
            except Exception as e:
                logger.error(
                    f"AlphaVantageAPI: Error accessing Supabase cache for {symbol}: {str(e)}"
                )
        else:
            logger.info(
                f"AlphaVantageAPI: Supabase not available, fetching directly from API for {symbol}"
            )

        # If no cached data, fetch from Alpha Vantage
        logger.info(
            f"AlphaVantageAPI: Cache miss - fetching fresh data from Alpha Vantage API for {symbol}"
        )

        try:
            params = {
                "function": ALPHAVANTAGE_FUNCTIONS["overview"],
                "symbol": symbol,
                "apikey": self.api_key,
            }

            response = self.session.get(
                self.base_url, params=params, timeout=self.settings.request_timeout
            )

            if response.status_code != 200:
                logger.error(
                    f"AlphaVantageAPI: HTTP error {response.status_code} for {symbol}"
                )
                return handle_api_error(response, "Alpha Vantage")

            data = response.json()

            # Check for API errors
            if "Error Message" in data:
                logger.error(
                    f"AlphaVantageAPI: Alpha Vantage API error for {symbol}: {data['Error Message']}"
                )
                return {"error": True, "message": data["Error Message"]}

            if "Note" in data or "Information" in data:
                logger.warning(
                    f"AlphaVantageAPI: Alpha Vantage rate limit or info for {symbol}"
                )
                return {
                    "error": True,
                    "message": "API rate limit exceeded or other issue",
                    "details": data.get("Note") or data.get("Information"),
                }

            # Process the data
            processed_data = self._process_overview_data(data, symbol)

            if processed_data.get("error"):
                logger.error(f"AlphaVantageAPI: Error processing data for {symbol}")
                return processed_data

            # Add API source metadata
            processed_data["cache_info"] = {
                "cache_hit": False,
                "data_source": "alpha_vantage_api",
            }

            # Save to cache asynchronously (don't wait for it)
            if self.db:

                def save_to_cache():
                    try:
                        success = self.db.save_stock_data(symbol, processed_data)
                        if success:
                            logger.info(
                                f"AlphaVantageAPI: Successfully cached data for {symbol} in background"
                            )
                        else:
                            logger.warning(
                                f"AlphaVantageAPI: Failed to cache data for {symbol}"
                            )
                    except Exception as e:
                        logger.error(
                            f"AlphaVantageAPI: Background cache save error for {symbol}: {str(e)}"
                        )

                # Run cache save in background thread
                cache_thread = threading.Thread(target=save_to_cache, daemon=True)
                cache_thread.start()
                logger.info(
                    f"AlphaVantageAPI: Initiated background cache save for {symbol}"
                )

            logger.info(
                f"AlphaVantageAPI: Successfully fetched and processed data for {symbol}"
            )
            return processed_data

        except requests.RequestException as e:
            logger.error(
                f"AlphaVantageAPI: Network request error for {symbol}: {str(e)}"
            )
            return {"error": True, "message": f"Request failed: {str(e)}"}

        except Exception as e:
            logger.error(f"AlphaVantageAPI: Unexpected error for {symbol}: {str(e)}")
            return {"error": True, "message": f"Processing failed: {str(e)}"}

    def _process_overview_data(
        self, data: Dict[str, Any], symbol: str
    ) -> Dict[str, Any]:
        """Process Alpha Vantage overview data into standardized format."""
        logger.debug(f"Alpha Vantage raw data for {symbol}: {data}")
        try:
            processed = {
                "symbol": symbol,
                "data_source": "alpha_vantage",
                "currency": DEFAULT_CURRENCY,
            }

            # Basic company info
            processed["name"] = data.get("Name", "")
            processed["description"] = data.get("Description", "")
            processed["sector"] = data.get("Sector", "")
            processed["industry"] = data.get("Industry", "")
            processed["exchange"] = data.get("Exchange", "")

            # Financial metrics
            processed["market_cap"] = safe_float(data.get("MarketCapitalization"))
            processed["pe_ratio"] = safe_float(data.get("PERatio"))
            processed["eps"] = safe_float(data.get("EPS"))
            processed["dividend_yield"] = safe_float(data.get("DividendYield"))
            processed["book_value"] = safe_float(data.get("BookValue"))
            processed["revenue_ttm"] = safe_float(data.get("RevenueTTM"))
            processed["profit_margin"] = safe_float(data.get("ProfitMargin"))
            processed["operating_margin"] = safe_float(data.get("OperatingMarginTTM"))
            processed["return_on_assets"] = safe_float(data.get("ReturnOnAssetsTTM"))
            processed["return_on_equity"] = safe_float(data.get("ReturnOnEquityTTM"))
            processed["debt_to_equity"] = safe_float(data.get("DebtToEquityRatio"))

            # Price data
            processed["high_52week"] = safe_float(data.get("52WeekHigh"))
            processed["low_52week"] = safe_float(data.get("52WeekLow"))
            processed["beta"] = safe_float(data.get("Beta"))

            # Shares info
            processed["shares_outstanding"] = safe_float(data.get("SharesOutstanding"))

            # Analyst data
            processed["analyst_target_price"] = safe_float(
                data.get("AnalystTargetPrice")
            )

            # Agent metadata
            processed["agent_info"] = {
                "processed_by": "FinancialAgent",
                "symbol_processed": symbol,
                "market_type": "global",
                "version": "1.0.0",
            }

            return processed

        except Exception as e:
            logger.error(f"Error processing overview data: {e}")
            return {
                "error": True,
                "message": f"Data processing failed: {str(e)}",
                "raw_data": data,
            }

    def fetch_earnings(self, symbol: str) -> Dict[str, Any]:
        """Fetch earnings data for a symbol with cache-first behavior."""
        return self._fetch_statement_with_cache(
            symbol, "earnings", ALPHAVANTAGE_FUNCTIONS["earnings"], table="earnings"
        )

    def fetch_income_statement(self, symbol: str) -> Dict[str, Any]:
        """Fetch income statement for a symbol (cache-first)."""
        return self._fetch_statement_with_cache(
            symbol,
            "income_statement",
            ALPHAVANTAGE_FUNCTIONS["income_statement"],
            table="income_statements",
        )

    def fetch_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """Fetch balance sheet for a symbol (cache-first)."""
        return self._fetch_statement_with_cache(
            symbol,
            "balance_sheet",
            ALPHAVANTAGE_FUNCTIONS["balance_sheet"],
            table="balance_sheets",
        )

    def fetch_cash_flow(self, symbol: str) -> Dict[str, Any]:
        """Fetch cash flow statement for a symbol (cache-first)."""
        return self._fetch_statement_with_cache(
            symbol, "cash_flow", ALPHAVANTAGE_FUNCTIONS["cash_flow"], table="cash_flows"
        )

    def _fetch_statement_with_cache(
        self, symbol: str, friendly_name: str, function_name: str, table: str
    ) -> Dict[str, Any]:
        """Generic helper to fetch a statement using cache-first approach."""
        logger.info(
            f"AlphaVantageAPI: LLM requested {friendly_name} for symbol: {symbol}"
        )

        if not self.api_key:
            logger.error("AlphaVantageAPI: No Alpha Vantage API key configured")
            return {"error": True, "message": "Alpha Vantage API key not configured"}

        # Try cache first
        if self.db:
            try:
                cached = self.db.get_statement_data(table, symbol)
                if cached:
                    logger.info(
                        f"AlphaVantageAPI: Returning cached {friendly_name} from Supabase for {symbol}"
                    )
                    cached["cache_info"] = {
                        "cache_hit": True,
                        "data_source": "supabase_cache",
                        "table": table,
                    }
                    return cached
            except Exception as e:
                logger.error(
                    f"AlphaVantageAPI: Error accessing Supabase cache for {symbol} ({friendly_name}): {str(e)}"
                )

        # Cache miss - call Alpha Vantage
        logger.info(
            f"AlphaVantageAPI: Cache miss - fetching {friendly_name} from Alpha Vantage for {symbol}"
        )
        try:
            params = {
                "function": function_name,
                "symbol": symbol,
                "apikey": self.api_key,
            }

            response = self.session.get(
                self.base_url, params=params, timeout=self.settings.request_timeout
            )
            if response.status_code != 200:
                logger.error(
                    f"AlphaVantageAPI: HTTP error {response.status_code} for {symbol} ({friendly_name})"
                )
                return handle_api_error(response, f"Alpha Vantage {friendly_name}")

            data = response.json()
            if "Error Message" in data:
                return {"error": True, "message": data["Error Message"]}
            if "Note" in data or "Information" in data:
                return {
                    "error": True,
                    "message": "API rate limit or information",
                    "details": data.get("Note") or data.get("Information"),
                }

            result = {
                "symbol": symbol,
                "data": data,
                "data_source": f"alpha_vantage_{friendly_name}",
            }

            # Save to cache asynchronously
            if self.db:

                def save():
                    try:
                        saved = self.db.save_statement_data(table, symbol, result)
                        if saved:
                            logger.info(
                                f"AlphaVantageAPI: Cached {friendly_name} for {symbol} in {table}"
                            )
                        else:
                            logger.warning(
                                f"AlphaVantageAPI: Failed to cache {friendly_name} for {symbol}"
                            )
                    except Exception as e:
                        logger.error(
                            f"AlphaVantageAPI: Background cache save error for {symbol} ({friendly_name}): {str(e)}"
                        )

                t = threading.Thread(target=save, daemon=True)
                t.start()

            result["cache_info"] = {
                "cache_hit": False,
                "data_source": "alpha_vantage_api",
                "table": table,
            }
            return result

        except requests.RequestException as e:
            logger.error(
                f"AlphaVantageAPI: Network error fetching {friendly_name} for {symbol}: {str(e)}"
            )
            return {"error": True, "message": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(
                f"AlphaVantageAPI: Unexpected error fetching {friendly_name} for {symbol}: {str(e)}"
            )
            return {"error": True, "message": f"Processing failed: {str(e)}"}

    def health_check(self) -> Dict[str, Any]:
        """Check if Alpha Vantage API is accessible."""
        if not self.api_key:
            return {"status": "unhealthy", "error": "API key not configured"}

        try:
            # Test with a simple query
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "AAPL",
                "apikey": self.api_key,
            }

            response = self.session.get(self.base_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if "Error Message" not in data and "Note" not in data:
                    return {"status": "healthy"}

            return {
                "status": "unhealthy",
                "status_code": response.status_code,
                "response": response.text[:200],
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
