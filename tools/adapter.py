"""
Adapter layer that unifies different data sources (Screener.in for Indian stocks
and AlphaVantage for global stocks) behind a simple interface.

Responsibilities:
- detect whether a symbol is Indian or global
- call the appropriate client and return standardized dict
"""
from typing import Dict, Any, List
import re

from tools.screener_api import ScreenerAPI
from tools.alphavantage_api import AlphaVantageAPI


INDIAN_SUFFIXES = [".NS", ".BO"]


class DataAdapter:
    def __init__(self):
        # instantiate clients lazily to avoid heavy imports/tests
        self._screener = ScreenerAPI()
        self._alpha = AlphaVantageAPI()

    def is_indian(self, symbol: str) -> bool:
        """Return True if symbol looks like an Indian stock.

        Heuristics used:
        - explicit suffix .NS or .BO (NSE / BSE)
        - symbol contains only letters and length<=5 (common for Indian tickers)
        - symbol is all-uppercase and not containing a dot but shorter than 6
        """
        if not symbol:
            return False

        # normalized
        s = symbol.strip()
        # explicit suffix
        for suf in INDIAN_SUFFIXES:
            if s.upper().endswith(suf):
                return True

        # if contains dot with global exchange like .NS handled above, treat as global
        if '.' in s:
            return False

        # simple alpha-only short tickers are likely Indian (e.g., TCS, INFY)
        if re.fullmatch(r"[A-Z]{1,5}", s):
            return True

        return False

    def fetch(self, symbol: str) -> Dict[str, Any]:
        """Fetch a single symbol, auto-detecting source.

        Returns the client response dict directly. Caller should handle errors.
        """
        s = symbol.strip()
        if self.is_indian(s):
            # Screener expects the company short name (no exchange suffix)
            # Try to remove common suffixes if provided
            for suf in INDIAN_SUFFIXES:
                if s.upper().endswith(suf):
                    s = s[:-len(suf)]
                    break
            return self._screener.fetch_company_data(s)

        # otherwise treat as global
        # AlphaVantage often expects symbol like 'AAPL' or 'MSFT'
        return self._alpha.fetch_company_overview(s)

    def fetch_multiple(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch multiple symbols and return dict mapping symbol->result."""
        results = {}
        for sym in symbols:
            try:
                results[sym] = self.fetch(sym)
            except Exception as e:
                results[sym] = {'error': True, 'message': str(e)}
        return results
