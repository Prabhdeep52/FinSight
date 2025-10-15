"""
Alpha Vantage API tool for fetching global stock data.
Uses Alpha Vantage's REST API to get financial information for global stocks.
"""
import requests
from typing import Dict, Any, Optional
from core.utils import logger, safe_float, standardize_financial_data, handle_api_error
from core.constants import ALPHAVANTAGE_BASE_URL, ALPHAVANTAGE_FUNCTIONS, DEFAULT_CURRENCY
from config.settings import get_settings


class AlphaVantageAPI:
    """Client for fetching global stock data from Alpha Vantage API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = ALPHAVANTAGE_BASE_URL
        self.api_key = self.settings.alphavantage_api_key
        self.session = requests.Session()
    
    def fetch_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch company overview data from Alpha Vantage.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
            
        Returns:
            Dictionary containing financial metrics
        """
        if not self.api_key:
            return {
                'error': True,
                'message': 'Alpha Vantage API key not configured'
            }
        
        try:
            params = {
                'function': ALPHAVANTAGE_FUNCTIONS['overview'],
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            logger.info(f"Fetching data from Alpha Vantage for symbol: {symbol}")
            
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.settings.request_timeout
            )
            
            if response.status_code != 200:
                return handle_api_error(response, "Alpha Vantage")
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                return {
                    'error': True,
                    'message': data['Error Message']
                }
            
            if 'Note' in data or 'Information' in data:
                return {
                    'error': True,
                    'message': 'API rate limit exceeded or other issue',
                    'details': data.get('Note') or data.get('Information')
                }
            
            # Process the data
            processed_data = self._process_overview_data(data, symbol)
            
            logger.info(f"Successfully fetched data for {symbol}")
            return processed_data
            
        except requests.RequestException as e:
            logger.error(f"Request error for {symbol}: {str(e)}")
            return {'error': True, 'message': f'Request failed: {str(e)}'}
        
        except Exception as e:
            logger.error(f"Unexpected error for {symbol}: {str(e)}")
            return {'error': True, 'message': f'Processing failed: {str(e)}'}
    
    def _process_overview_data(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Process Alpha Vantage overview data into standardized format."""
        logger.debug(f"Alpha Vantage raw data for {symbol}: {data}")
        try:
            processed = {
                'symbol': symbol,
                'data_source': 'alpha_vantage',
                'currency': DEFAULT_CURRENCY
            }
            
            # Basic company info
            processed['name'] = data.get('Name', '')
            processed['description'] = data.get('Description', '')
            processed['sector'] = data.get('Sector', '')
            processed['industry'] = data.get('Industry', '')
            processed['exchange'] = data.get('Exchange', '')
            
            # Financial metrics
            processed['market_cap'] = safe_float(data.get('MarketCapitalization'))
            processed['pe_ratio'] = safe_float(data.get('PERatio'))
            processed['eps'] = safe_float(data.get('EPS'))
            processed['dividend_yield'] = safe_float(data.get('DividendYield'))
            processed['book_value'] = safe_float(data.get('BookValue'))
            processed['revenue_ttm'] = safe_float(data.get('RevenueTTM'))
            processed['profit_margin'] = safe_float(data.get('ProfitMargin'))
            processed['operating_margin'] = safe_float(data.get('OperatingMarginTTM'))
            processed['return_on_assets'] = safe_float(data.get('ReturnOnAssetsTTM'))
            processed['return_on_equity'] = safe_float(data.get('ReturnOnEquityTTM'))
            processed['debt_to_equity'] = safe_float(data.get('DebtToEquityRatio'))
            
            # Price data
            processed['high_52week'] = safe_float(data.get('52WeekHigh'))
            processed['low_52week'] = safe_float(data.get('52WeekLow'))
            processed['beta'] = safe_float(data.get('Beta'))
            
            # Shares info
            processed['shares_outstanding'] = safe_float(data.get('SharesOutstanding'))
            
            # Analyst data
            processed['analyst_target_price'] = safe_float(data.get('AnalystTargetPrice'))
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing overview data: {e}")
            return {
                'error': True,
                'message': f'Data processing failed: {str(e)}',
                'raw_data': data
            }
    
    def fetch_earnings(self, symbol: str) -> Dict[str, Any]:
        """Fetch earnings data for a symbol."""
        if not self.api_key:
            return {
                'error': True,
                'message': 'Alpha Vantage API key not configured'
            }
        
        try:
            params = {
                'function': ALPHAVANTAGE_FUNCTIONS['earnings'],
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.settings.request_timeout
            )
            
            if response.status_code != 200:
                return handle_api_error(response, "Alpha Vantage Earnings")
            
            data = response.json()
            
            if 'Error Message' in data:
                return {
                    'error': True,
                    'message': data['Error Message']
                }
            
            return {
                'symbol': symbol,
                'earnings_data': data,
                'data_source': 'alpha_vantage_earnings'
            }
            
        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
            return {'error': True, 'message': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Alpha Vantage API is accessible."""
        if not self.api_key:
            return {
                'status': 'unhealthy',
                'error': 'API key not configured'
            }
        
        try:
            # Test with a simple query
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL',
                'apikey': self.api_key
            }
            
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'Error Message' not in data and 'Note' not in data:
                    return {'status': 'healthy'}
            
            return {
                'status': 'unhealthy',
                'status_code': response.status_code,
                'response': response.text[:200]
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }