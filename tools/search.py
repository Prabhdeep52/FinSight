# tools/duckduckgo_search_tool.py
from ddgs import DDGS


def duckduckgo_search(query: str, max_results: int = 5):
    """Perform a DuckDuckGo web search."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "title": r.get("title"),
                "href": r.get("href"),
                "body": r.get("body"),
            }
            for r in results
        ]
