"""
Supabase client for financial agent.
Handles database operations for stock data caching.
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from supabase import create_client, Client
from core.utils import logger
from config.settings import get_settings


class SupabaseManager:
    """
    Manager class for Supabase operations.
    Handles stock data caching and retrieval with TTL support.
    """
    
    def __init__(self):
        """Initialize Supabase client with settings from config."""
        settings = get_settings()
        self.url: str = settings.supabase_url
        self.key: str = settings.supabase_anon_key
        
        if not self.url or not self.key:
            logger.error("SupabaseManager: Missing supabase_url or supabase_anon_key in settings")
            raise ValueError("Supabase URL and key must be set in settings/environment variables")
        
        try:
            self.client: Client = create_client(self.url, self.key)
            logger.info("SupabaseManager: Successfully initialized Supabase client")
        except Exception as e:
            logger.error(f"SupabaseManager: Failed to initialize Supabase client: {str(e)}")
            raise

    def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock data from Supabase if it exists and is not stale.
        
        Args:
            symbol: Stock symbol to retrieve data for
            
        Returns:
            Stock data if found and fresh, None otherwise
        """
        try:
            logger.info(f"SupabaseManager: Checking cache for symbol: {symbol}")
            
            response = self.client.table('stock_overview') \
                .select("*") \
                .eq('symbol', symbol.upper()) \
                .execute()

            if response.data and len(response.data) > 0:
                record = response.data[0]
                last_updated_str = record.get('last_updated')
                
                if last_updated_str:
                    # Parse the timestamp
                    last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                    age_hours = (datetime.now(timezone.utc) - last_updated).total_seconds() / 3600

                    if age_hours < 24:  # Cache is fresh (less than 24 hours old)
                        logger.info(f"SupabaseManager: Cache hit for {symbol}, age: {age_hours:.2f} hours")
                        return record.get('data')
                    else:
                        logger.info(f"SupabaseManager: Cache expired for {symbol}, age: {age_hours:.2f} hours")
                        return None
                else:
                    logger.warning(f"SupabaseManager: No timestamp found for {symbol}, treating as stale")
                    return None
            else:
                logger.info(f"SupabaseManager: No cached data found for {symbol}")
                return None

        except Exception as e:
            logger.error(f"SupabaseManager: Error fetching data for {symbol}: {str(e)}")
            return None

    def save_stock_data(self, symbol: str, data: Dict[str, Any]) -> bool:
        """
        Save or update stock data in Supabase.
        
        Args:
            symbol: Stock symbol
            data: Stock data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"SupabaseManager: Saving data for symbol: {symbol}")
            
            # Prepare the data for insertion
            upsert_data = {
                'symbol': symbol.upper(),
                'data': data,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # Upsert data (insert or update if exists)
            response = self.client.table('stock_overview') \
                .upsert(upsert_data) \
                .execute()

            if response.data:
                logger.info(f"SupabaseManager: Successfully saved data for {symbol}")
                return True
            else:
                logger.error(f"SupabaseManager: Failed to save data for {symbol} - no response data")
                return False

        except Exception as e:
            logger.error(f"SupabaseManager: Error saving data for {symbol}: {str(e)}")
            return False

    # --- Generic statement caching helpers ---
    def _get_statement_record(self, table: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Internal helper to read a statement record from a specific table."""
        try:
            logger.info(f"SupabaseManager: Checking cache table '{table}' for symbol: {symbol}")
            response = self.client.table(table) \
                .select("*") \
                .eq('symbol', symbol.upper()) \
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"SupabaseManager: Error fetching record from {table} for {symbol}: {str(e)}")
            return None

    def get_statement_data(self, table: str, symbol: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """Get statement JSON for a symbol from a named table if fresh.

        Args:
            table: Supabase table name for the statement (e.g., 'income_statements')
            symbol: Stock symbol
            max_age_hours: TTL in hours (default 24)

        Returns:
            The stored JSON data dict if present and fresh; otherwise None
        """
        try:
            record = self._get_statement_record(table, symbol)
            if not record:
                logger.info(f"SupabaseManager: No cached record in {table} for {symbol}")
                return None

            last_updated_str = record.get('last_updated')
            if not last_updated_str:
                logger.warning(f"SupabaseManager: No timestamp found in {table} for {symbol}, treating as stale")
                return None

            last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            age_hours = (datetime.now(timezone.utc) - last_updated).total_seconds() / 3600
            if age_hours < max_age_hours:
                logger.info(f"SupabaseManager: Cache hit in {table} for {symbol}, age: {age_hours:.2f} hours")
                return record.get('data')
            else:
                logger.info(f"SupabaseManager: Cache expired in {table} for {symbol}, age: {age_hours:.2f} hours")
                return None

        except Exception as e:
            logger.error(f"SupabaseManager: Error getting statement data from {table} for {symbol}: {str(e)}")
            return None

    def save_statement_data(self, table: str, symbol: str, data: Dict[str, Any]) -> bool:
        """Save statement JSON into the specified table (upsert).

        Args:
            table: Supabase table name
            symbol: Stock symbol
            data: JSON-serializable dict to store

        Returns:
            True on success, False otherwise
        """
        try:
            logger.info(f"SupabaseManager: Saving record to table '{table}' for symbol: {symbol}")
            upsert_data = {
                'symbol': symbol.upper(),
                'data': data,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }

            response = self.client.table(table) \
                .upsert(upsert_data) \
                .execute()

            if response.data:
                logger.info(f"SupabaseManager: Successfully saved statement for {symbol} to {table}")
                return True
            logger.error(f"SupabaseManager: Failed to save statement for {symbol} to {table} - no response data")
            return False

        except Exception as e:
            logger.error(f"SupabaseManager: Error saving statement to {table} for {symbol}: {str(e)}")
            return False

    def delete_stock_data(self, symbol: str) -> bool:
        """
        Delete stock data from Supabase.
        
        Args:
            symbol: Stock symbol to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"SupabaseManager: Deleting data for symbol: {symbol}")
            
            response = self.client.table('stock_overview') \
                .delete() \
                .eq('symbol', symbol.upper()) \
                .execute()

            logger.info(f"SupabaseManager: Successfully deleted data for {symbol}")
            return True

        except Exception as e:
            logger.error(f"SupabaseManager: Error deleting data for {symbol}: {str(e)}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        try:
            logger.info("SupabaseManager: Fetching cache statistics")
            
            # Count total records
            response = self.client.table('stock_overview') \
                .select("symbol, last_updated", count="exact") \
                .execute()
            
            total_records = response.count if hasattr(response, 'count') else len(response.data or [])
            
            # Count fresh records (less than 24 hours old)
            from datetime import timedelta
            fresh_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            fresh_response = self.client.table('stock_overview') \
                .select("symbol", count="exact") \
                .gte('last_updated', fresh_cutoff.isoformat()) \
                .execute()
            
            fresh_records = fresh_response.count if hasattr(fresh_response, 'count') else len(fresh_response.data or [])
            
            stats = {
                'total_records': total_records,
                'fresh_records': fresh_records,
                'stale_records': total_records - fresh_records,
                'cache_hit_rate': (fresh_records / total_records * 100) if total_records > 0 else 0
            }
            
            logger.info(f"SupabaseManager: Cache stats - {stats}")
            return stats

        except Exception as e:
            logger.error(f"SupabaseManager: Error fetching cache stats: {str(e)}")
            return {
                'total_records': 0,
                'fresh_records': 0,
                'stale_records': 0,
                'cache_hit_rate': 0,
                'error': str(e)
            }

    def health_check(self) -> Dict[str, Any]:
        """
        Check if Supabase connection is healthy.
        
        Returns:
            Health check results
        """
        try:
            logger.info("SupabaseManager: Performing health check")
            
            # Try to query the table structure
            response = self.client.table('stock_overview') \
                .select("symbol") \
                .limit(1) \
                .execute()
            
            logger.info("SupabaseManager: Health check passed")
            return {
                'status': 'healthy',
                'connection': 'active',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"SupabaseManager: Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'connection': 'failed',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }