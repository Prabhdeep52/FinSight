"""
Screener.in API tool for fetching Indian stock data.
Scrapes financial data from Screener.in since they don't provide a public API.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from Backend.core.utils import logger, safe_float, format_currency, handle_api_error
from Backend.core.constants import SCREENER_COMPANY_URL, DEFAULT_INDIAN_CURRENCY
from Backend.config.settings import get_settings


class ScreenerAPI:
    """Client for fetching Indian stock data from Screener.in."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = SCREENER_COMPANY_URL
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def fetch_company_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch comprehensive financial data for an Indian company.

        Args:
            symbol: Stock symbol (e.g., 'INFY', 'TCS')

        Returns:
            Dictionary containing financial metrics
        """
        try:
            url = f"{self.base_url}/{symbol}/"
            logger.info(f"Fetching data from Screener.in for symbol: {symbol}")

            response = self.session.get(url, timeout=self.settings.request_timeout)

            if response.status_code != 200:
                return handle_api_error(response, "Screener.in")

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract company data
            company_data = self._extract_company_info(soup, symbol)
            financial_data = self._extract_financial_metrics(soup)
            ratios_data = self._extract_ratios(soup)

            # Combine all data
            result = {
                **company_data,
                **financial_data,
                **ratios_data,
                "data_source": "screener.in",
                "currency": DEFAULT_INDIAN_CURRENCY,
            }

            logger.info(f"Successfully fetched data for {symbol}")
            return result

        except requests.RequestException as e:
            logger.error(f"Request error for {symbol}: {str(e)}")
            return {"error": True, "message": f"Request failed: {str(e)}"}

        except Exception as e:
            logger.error(f"Unexpected error for {symbol}: {str(e)}")
            return {"error": True, "message": f"Parsing failed: {str(e)}"}

    def _extract_company_info(self, soup: BeautifulSoup, symbol: str) -> Dict[str, Any]:
        """Extract basic company information."""
        data = {"symbol": symbol}

        try:
            # Company name
            name_element = soup.find("h1")
            if name_element:
                data["name"] = name_element.get_text().strip()

            # Current price
            price_element = soup.find("span", {"class": "number"})
            if price_element:
                data["current_price"] = safe_float(price_element.get_text())

        except Exception as e:
            logger.warning(f"Error extracting company info: {e}")

        return data

    def _extract_financial_metrics(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract financial metrics from the page."""
        data = {}

        try:
            # Look for the ratios table
            ratios_section = soup.find("section", {"id": "ratios"})
            if ratios_section:
                rows = ratios_section.find_all("li")

                for row in rows:
                    spans = row.find_all("span")
                    if len(spans) >= 2:
                        key = spans[0].get_text().strip().lower()
                        value = spans[-1].get_text().strip()

                        # Map key names to standardized format
                        if "market cap" in key:
                            data["market_cap"] = self._parse_market_cap(value)
                        elif "current price" in key:
                            data["current_price"] = safe_float(value)
                        elif "high / low" in key:
                            high_low = value.split("/")
                            if len(high_low) == 2:
                                data["high_52week"] = safe_float(high_low[0].strip())
                                data["low_52week"] = safe_float(high_low[1].strip())
                        elif "book value" in key:
                            data["book_value"] = safe_float(value)
                        elif "dividend yield" in key:
                            data["dividend_yield"] = safe_float(value.replace("%", ""))
                        elif "roce" in key:
                            data["roce"] = safe_float(value.replace("%", ""))
                        elif "roe" in key:
                            data["roe"] = safe_float(value.replace("%", ""))
                        elif "face value" in key:
                            data["face_value"] = safe_float(value)

        except Exception as e:
            logger.warning(f"Error extracting financial metrics: {e}")

        return data

    def _extract_ratios(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract financial ratios."""
        data = {}

        try:
            # Look for key ratio boxes
            ratio_boxes = soup.find_all("div", {"class": "flex flex-space-between"})

            for box in ratio_boxes:
                text = box.get_text().strip()

                if "P/E" in text:
                    pe_value = text.split(":")[-1].strip()
                    data["pe_ratio"] = safe_float(pe_value)
                elif "P/B" in text:
                    pb_value = text.split(":")[-1].strip()
                    data["pb_ratio"] = safe_float(pb_value)
                elif "EPS" in text and "₹" in text:
                    eps_value = text.replace("₹", "").strip()
                    data["eps"] = safe_float(eps_value)

        except Exception as e:
            logger.warning(f"Error extracting ratios: {e}")

        return data

    def _parse_market_cap(self, value: str) -> Optional[float]:
        """Parse market cap value (handles Cr, thousands, etc.)."""
        try:
            value = value.lower().replace("₹", "").replace(",", "").strip()

            if "cr" in value or "crore" in value:
                number = safe_float(
                    value.replace("cr", "").replace("crore", "").strip()
                )
                return (
                    number * 10000000 if number else None
                )  # Convert crores to actual value
            elif "l" in value or "lakh" in value:
                number = safe_float(value.replace("l", "").replace("lakh", "").strip())
                return (
                    number * 100000 if number else None
                )  # Convert lakhs to actual value
            else:
                return safe_float(value)

        except:
            return None

    def health_check(self) -> Dict[str, Any]:
        """Check if Screener.in is accessible."""
        try:
            response = self.session.get("https://www.screener.in", timeout=10)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
