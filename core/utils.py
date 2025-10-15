"""
Utility functions for InvestIQ financial agent system.
Contains helper functions for formatting, error handling, and data processing.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal, InvalidOperation
from config.settings import settings


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Set up logger for the application."""
    log_level = "DEBUG" if settings.debug else level
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def is_indian_stock(symbol: str) -> bool:
    """Check if a stock symbol is from Indian market."""
    symbol_upper = symbol.upper()
    
    # Check for NSE/BSE suffixes
    if any(symbol_upper.endswith(suffix) for suffix in [".NS", ".BO"]):
        return True
    
    # Known global symbols that should not be classified as Indian
    global_symbols = {'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'IBM', 'NFLX', 'PYPL'}
    if symbol_upper in global_symbols:
        return False
    
    # Indian symbols are typically 3-5 letters, all caps, no dots
    # and commonly known Indian companies
    known_indian = {'INFY', 'TCS', 'RELIANCE', 'WIPRO', 'HDFC', 'ICICI', 'SBI', 'ITC', 'BHARTI'}
    if symbol_upper in known_indian:
        return True
    
    # Heuristic: If it's 4 letters or less, all alpha, and not in global list, assume Indian
    if len(symbol_upper) <= 4 and symbol_upper.isalpha() and symbol_upper not in global_symbols:
        return True
    
    return False


def clean_symbol(symbol: str) -> str:
    """Clean and standardize stock symbol."""
    return symbol.upper().strip()


def format_currency(value: Union[str, int, float], currency: str = "USD") -> str:
    """Format numeric value as currency."""
    try:
        if isinstance(value, str):
            # Remove commas and convert to float
            cleaned_value = re.sub(r'[,\s]', '', value)
            value = float(cleaned_value)
        
        if currency == "INR":
            return f"₹{value:,.2f}"
        elif currency == "USD":
            return f"${value:,.2f}"
        else:
            return f"{value:,.2f} {currency}"
    
    except (ValueError, TypeError):
        return f"N/A {currency}"


def format_percentage(value: Union[str, int, float]) -> str:
    """Format numeric value as percentage."""
    try:
        if isinstance(value, str):
            cleaned_value = re.sub(r'[,%\s]', '', value)
            value = float(cleaned_value)
        
        return f"{value:.2f}%"
    
    except (ValueError, TypeError):
        return "N/A%"


def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return None
    
    try:
        if isinstance(value, str):
            # Remove commas, spaces, and percentage signs
            cleaned = re.sub(r'[,\s%]', '', value)
            return float(cleaned)
        return float(value)
    
    except (ValueError, TypeError, InvalidOperation):
        return None


def safe_int(value: Any) -> Optional[int]:
    """Safely convert value to integer."""
    if value is None:
        return None
    
    try:
        if isinstance(value, str):
            cleaned = re.sub(r'[,\s]', '', value)
            return int(float(cleaned))
        return int(value)
    
    except (ValueError, TypeError, InvalidOperation):
        return None


def extract_number_from_text(text: str) -> Optional[float]:
    """Extract numeric value from text string."""
    if not text:
        return None
    
    # Find numeric patterns in text
    pattern = r'[-+]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)'
    matches = re.findall(pattern, text.replace(',', ''))
    
    if matches:
        try:
            return float(matches[0])
        except ValueError:
            return None
    
    return None


def standardize_financial_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize financial data structure."""
    standardized = {}
    
    # Map common variations to standard keys
    key_mappings = {
        'market_cap': ['MarketCapitalization', 'Market Cap', 'market_cap'],
        'pe_ratio': ['PERatio', 'PE Ratio', 'P/E Ratio', 'pe_ratio'],
        'eps': ['EPS', 'Earnings Per Share', 'eps'],
        'revenue': ['Revenue', 'Total Revenue', 'Sales', 'revenue'],
        'profit': ['Net Income', 'Profit After Tax', 'PAT', 'profit'],
        'dividend_yield': ['DividendYield', 'Dividend Yield', 'dividend_yield'],
        'debt_to_equity': ['DebtToEquityRatio', 'Debt to Equity', 'debt_to_equity']
    }
    
    for standard_key, variations in key_mappings.items():
        for variation in variations:
            if variation in data:
                value = data[variation]
                if isinstance(value, str) and value.lower() in ['none', 'n/a', '-']:
                    standardized[standard_key] = None
                else:
                    standardized[standard_key] = safe_float(value)
                break
        else:
            standardized[standard_key] = None
    
    return standardized


def handle_api_error(response, api_name: str) -> Dict[str, Any]:
    """Handle API response errors."""
    logger = setup_logger(__name__)
    
    error_data = {
        "error": True,
        "api": api_name,
        "status_code": response.status_code,
        "message": f"API request failed with status {response.status_code}"
    }
    
    try:
        error_data["details"] = response.json()
    except:
        error_data["details"] = response.text
    
    logger.error(f"{api_name} API error: {error_data}")
    return error_data


def validate_symbol(symbol: str) -> bool:
    """Validate stock symbol format."""
    if not symbol or len(symbol) < 1:
        return False
    
    # Basic validation - alphanumeric characters and dots
    return bool(re.match(r'^[A-Za-z0-9.]+$', symbol))


logger = setup_logger(__name__)