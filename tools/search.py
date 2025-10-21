from ddgs import DDGS
from tools.fetch_article_text import fetch_article_text


def duckduckgo_search(query: str, max_results: int = 5):
    """Perform a DuckDuckGo news search and fetch full article text."""
    with DDGS() as ddgs:
        results = list(ddgs.news(query, max_results=max_results))

    enriched = []
    for r in results:
        title = r.get("title")
        url = r.get("url") or r.get("href")
        snippet = r.get("body") or r.get("excerpt", "")
        if title and url:
            full_text = fetch_article_text(url)
            enriched.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "content": full_text[:4000],
                }
            )

    return enriched
