from typing import Dict

import httpx


async def search_wikipedia(query: str) -> Dict:
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
    }
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json().get("query", {}).get("search", [])
    return {
        "source": "Wikipedia",
        "reliability": "high",
        "count": len(payload),
        "items": [item.get("title") for item in payload[:3]],
    }
