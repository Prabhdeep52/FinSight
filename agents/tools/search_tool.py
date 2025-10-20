# agents/news_search_tool.py
import json
from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from tools.search import duckduckgo_search
from core.utils import logger


class SearchInput(BaseModel):
    query: str = Field(description="Search query for latest news")
    max_results: int = Field(default=5, description="Max number of news articles")


class SearchTool(BaseTool):
    name: str = "get_latest_news"
    description: str = (
        "Searches DuckDuckGo for latest headlines and URLs related to a topic."
    )
    args_schema: Type[BaseModel] = SearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        logger.info(f"SearchTool: Searching news for '{query}'")
        results = duckduckgo_search(query, max_results)
        return json.dumps(results)

    async def _arun(self, query: str, max_results: int = 5) -> str:
        return self._run(query, max_results)


def create_search_tool() -> SearchTool:
    """
    Factory function to create a NewsSearchTool instance.
    Keeps consistency with other create_*_tool() functions.
    """
    logger.info("Creating NewsSearchTool")
    return SearchTool()
