import requests
from bs4 import BeautifulSoup


def fetch_article_text(url: str) -> str:
    """
    Try to fetch readable article content from a URL.
    Returns a cleaned-up plain-text version.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # (DuckDuckGo results are mostly news pages with <article> tags)
        article_tag = soup.find("article")

        if article_tag:
            text = article_tag.get_text(separator=" ", strip=True)
        else:
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)

        text = " ".join(text.split())

        # Filter out garbage (very short text)
        if len(text) < 100:
            return ""

        return text

    except Exception as e:
        print(f"[WARN] Could not extract article text from {url}: {e}")
        return ""
