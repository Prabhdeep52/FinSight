"""
FastAPI routes for FinSight financial agent system.
Defines API endpoints for accessing stock data and system health.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import asyncio
from Backend.data_services.financial_agent import FinancialAgent
from Backend.core.utils import logger


# Response models for API documentation
class StockDataResponse(BaseModel):
    """Response model for stock data."""

    symbol: str
    name: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    currency: Optional[str] = None
    data_source: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "current_price": 150.25,
                "market_cap": 2450000000000,
                "pe_ratio": 28.5,
                "eps": 5.89,
                "currency": "USD",
                "data_source": "alpha_vantage",
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""

    overall_status: str
    components: Dict[str, Any]
    agent_version: str


class MarketInfoResponse(BaseModel):
    """Response model for market information."""

    symbol: str
    market_type: str
    data_source: str
    currency: str


# Initialize router and agent
router = APIRouter()
financial_agent = FinancialAgent()


@router.get("/", summary="API Information")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "FinSight Financial Agent API",
        "version": "1.0.0",
        "description": "Fetch financial data for Indian and global stocks",
        "endpoints": {
            "/stock/{symbol}": "Get financial data for a stock symbol",
            "/stocks": "Get financial data for multiple stock symbols",
            "/market-info/{symbol}": "Get market classification for a symbol",
            "/health": "Health check for all APIs",
            "/supported-markets": "Information about supported markets",
        },
    }


@router.get("/stock/{symbol}", response_model=Dict[str, Any], summary="Get Stock Data")
async def get_stock_data(symbol: str):
    """
    Get comprehensive financial data for a stock symbol.

    - **symbol**: Stock symbol (e.g., AAPL, INFY, GOOGL)

    Automatically detects if the symbol is from Indian or global markets
    and routes to the appropriate data source.
    """
    try:
        logger.info(f"API request for stock symbol: {symbol}")

        data = await asyncio.to_thread(financial_agent.fetch_stock_data, symbol)

        if data.get("error"):
            raise HTTPException(
                status_code=400,
                detail=data.get("message", "Failed to fetch stock data"),
            )

        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_stock_data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stocks", summary="Get Multiple Stocks Data")
async def get_multiple_stocks(
    symbols: List[str] = Query(..., description="List of stock symbols"),
):
    """
    Get financial data for multiple stock symbols.

    - **symbols**: List of stock symbols (e.g., ["AAPL", "INFY", "GOOGL"])

    Returns data for each symbol, including successful and failed requests.
    """
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols provided")

        if len(symbols) > 10:  # Limit batch size
            raise HTTPException(
                status_code=400, detail="Maximum 10 symbols allowed per request"
            )

        logger.info(f"API request for multiple symbols: {symbols}")

        data = financial_agent.fetch_multiple_stocks(symbols)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_multiple_stocks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/market-info/{symbol}",
    response_model=MarketInfoResponse,
    summary="Get Market Information",
)
async def get_market_info(symbol: str):
    """
    Get market classification and routing information for a stock symbol.

    - **symbol**: Stock symbol to analyze

    Returns information about which market the symbol belongs to and
    which data source will be used.
    """
    try:
        logger.info(f"API request for market info: {symbol}")

        data = financial_agent.get_market_info(symbol)
        return data

    except Exception as e:
        logger.error(f"Error in get_market_info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """
    Check health status of all integrated APIs and services.

    Returns the status of:
    - Screener.in API (for Indian stocks)
    - Alpha Vantage API (for global stocks)
    - Overall system health
    """
    try:
        logger.info("API health check requested")

        health_data = financial_agent.health_check()
        return health_data

    except Exception as e:
        logger.error(f"Error in health_check: {str(e)}")
        # Return degraded status if health check itself fails
        return {
            "overall_status": "unhealthy",
            "components": {"error": str(e)},
            "agent_version": "1.0.0",
        }


@router.get("/supported-markets", summary="Supported Markets")
async def get_supported_markets():
    """
    Get information about supported markets and exchanges.

    Returns details about:
    - Indian markets (NSE, BSE)
    - Global markets (NASDAQ, NYSE, etc.)
    - Example symbols for each market
    """
    try:
        data = financial_agent.get_supported_markets()
        return data

    except Exception as e:
        logger.error(f"Error in get_supported_markets: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
