# InvestIQ - Minimal Financial Agent

This workspace contains a minimal FastAPI application that exposes two endpoints to fetch
stock data. It automatically detects whether a symbol is an Indian stock (uses Screener.in)
or a global stock (uses Alpha Vantage).

Endpoints

- GET /api/v1/stock/{symbol} - fetch single symbol
- GET /api/v1/stocks?symbols=AAPL,INFY - fetch multiple symbols (comma separated)
- GET /health - basic health checks for adapters

Run locally (example, Windows PowerShell):

```powershell
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Notes

- Alpha Vantage requires an API key. The existing `tools/alphavantage_api.py` expects a
  settings provider (`config.settings.get_settings`) which is not included in this minimal
  scaffold. Either provide a settings module compatible with the client or modify the
  `AlphaVantageAPI` class to set `self.api_key` directly for testing.
- Screener.in scraping uses BeautifulSoup and may break if screener.in changes their HTML.
