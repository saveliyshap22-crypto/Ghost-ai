from typing import Dict

import httpx


SUBREDDITS = ["askscience", "explainlikeimfive"]


async def search_reddit(query: str) -> Dict:
    headers = {"User-Agent": "GhostAI/1.0"}
    items = []
    async with httpx.AsyncClient(timeout=8, headers=headers) as client:
        for sub in SUBREDDITS:
            url = f"https://www.reddit.com/r/{sub}/search.json"
            params = {"q": query, "restrict_sr": "on", "limit": 5, "sort": "relevance"}
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                children = resp.json().get("data", {}).get("children", [])
                items.extend([c.get("data", {}).get("title") for c in children])
    return {
        "source": "Reddit",
        "reliability": "medium",
        "count": len(items),
        "items": items[:5],
    }
