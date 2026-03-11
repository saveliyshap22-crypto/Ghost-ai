from typing import Dict

import feedparser
import httpx


async def search_stackoverflow(query: str) -> Dict:
    url = "https://api.stackexchange.com/2.3/search/advanced"
    params = {
        "order": "desc",
        "sort": "relevance",
        "site": "stackoverflow",
        "q": query,
        "pagesize": 5,
    }
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        items = response.json().get("items", [])
    return {
        "source": "Stack Overflow",
        "reliability": "medium",
        "count": len(items),
        "items": [it.get("title") for it in items[:3]],
    }


async def search_arxiv(query: str) -> Dict:
    feed = feedparser.parse(f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=5")
    return {
        "source": "arXiv",
        "reliability": "high",
        "count": len(feed.entries),
        "items": [entry.title for entry in feed.entries[:3]],
    }
