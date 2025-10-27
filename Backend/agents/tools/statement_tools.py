"""
Statement tools for LangGraph agents.
Provides tools the LLM can call to fetch income statement, balance sheet, cash flow and earnings.
"""
import json
from typing import Dict, Any, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from core.utils import logger
from tools.alphavantage_api import AlphaVantageAPI


class StatementInput(BaseModel):
    symbol: str = Field(description="Stock symbol (e.g., AAPL, INFY)")


class StatementTool(BaseTool):
    name: str = "statement_tool"
    description: str = "Generic statement tool"
    args_schema: Type[BaseModel] = StatementInput

    def __init__(self, fn, name: str, description: str):
        super().__init__()
        self._fn = fn
        self.name = name
        self.description = description

    def _run(self, symbol: str) -> str:
        logger.info(f"{self.name}: Requested symbol: {symbol}")
        try:
            clean_symbol = symbol.strip().upper()
            from tools.alphavantage_api import AlphaVantageAPI

            api = AlphaVantageAPI()
            result = self._fn(api, clean_symbol)
            logger.info(f"{self.name}: Retrieved data for {clean_symbol}")
            return json.dumps(result)

        except Exception as e:
            logger.error(f"{self.name}: Error fetching statement for {symbol}: {str(e)}")
            return json.dumps({'error': True, 'message': str(e), 'symbol': symbol})

    async def _arun(self, symbol: str) -> str:
        return self._run(symbol)


def create_income_statement_tool():
    def _fn(api: AlphaVantageAPI, sym: str):
        return api.fetch_income_statement(sym)

    return StatementTool(_fn, "get_income_statement", "Fetch income statement for a symbol")


def create_balance_sheet_tool():
    def _fn(api: AlphaVantageAPI, sym: str):
        return api.fetch_balance_sheet(sym)

    return StatementTool(_fn, "get_balance_sheet", "Fetch balance sheet for a symbol")


def create_cash_flow_tool():
    def _fn(api: AlphaVantageAPI, sym: str):
        return api.fetch_cash_flow(sym)

    return StatementTool(_fn, "get_cash_flow", "Fetch cash flow statement for a symbol")


def create_earnings_tool():
    def _fn(api: AlphaVantageAPI, sym: str):
        return api.fetch_earnings(sym)

    return StatementTool(_fn, "get_earnings", "Fetch earnings data for a symbol")
