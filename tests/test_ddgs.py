# from ddgs import DDGS


# def test_ddgs_news():
#     with DDGS() as ddgs:
#         results = list(ddgs.news("AAPL", max_results=5))
#         print("\n=== DuckDuckGo News Results ===")
#         if not results:
#             print("No news results found. Try a broader query or check your network.")
#         else:
#             for i, r in enumerate(results, start=1):
#                 title = r.get("title", "No title")
#                 url = r.get("url", "No URL")
#                 snippet = r.get("body", "") or r.get("excerpt", "")
#                 print(f"\n{i}. {title}\n   {url}\n   {snippet[:120]}...")


# if __name__ == "__main__":
#     test_ddgs_news()


from agents.tools.search_tool import create_search_tool

news_tool = create_search_tool()
results = news_tool._run("AAPL")  # or "AMZN" etc.

print(results)
