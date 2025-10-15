"""
Constants for InvestIQ financial agent system.
Contains API endpoints, base URLs, and other configuration constants.
"""

# Alpha Vantage API
ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHAVANTAGE_FUNCTIONS = {
    "overview": "OVERVIEW",
    "earnings": "EARNINGS", 
    "income_statement": "INCOME_STATEMENT",
    "balance_sheet": "BALANCE_SHEET",
    "cash_flow": "CASH_FLOW"
}

# Screener.in URLs (for Indian stocks)
SCREENER_BASE_URL = "https://www.screener.in"
SCREENER_COMPANY_URL = f"{SCREENER_BASE_URL}/company"

# Yahoo Finance (fallback)
YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

# Stock exchanges and market identifiers
INDIAN_EXCHANGES = ["NSE", "BSE"]
GLOBAL_EXCHANGES = ["NASDAQ", "NYSE", "TSX", "LSE"]

# Common Indian stock suffixes
INDIAN_STOCK_SUFFIXES = [".NS", ".BO"]  # NSE, BSE

# Financial metrics keys for standardization
FINANCIAL_METRICS = {
    "revenue": ["Revenue", "Total Revenue", "Sales"],
    "profit": ["Net Income", "Profit After Tax", "PAT"],
    "eps": ["EPS", "Earnings Per Share"],
    "pe_ratio": ["PE Ratio", "P/E Ratio", "PERatio"],
    "market_cap": ["Market Cap", "Market Capitalization"],
    "debt_to_equity": ["Debt to Equity", "D/E Ratio"],
    "roe": ["ROE", "Return on Equity"],
    "dividend_yield": ["Dividend Yield", "DividendYield"]
}

# HTTP status codes
HTTP_SUCCESS = 200
HTTP_NOT_FOUND = 404
HTTP_SERVER_ERROR = 500

# Default values
DEFAULT_CURRENCY = "USD"
DEFAULT_INDIAN_CURRENCY = "INR"