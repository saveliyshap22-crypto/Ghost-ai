from typing import Dict

import feedparser


GOOGLE_NEWS = "https://news.google.com/rss/search?q={query}"
BBC_NEWS = "http://feeds.bbci.co.uk/news/rss.xml"
REUTERS = "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"


async def search_news(query: str) -> Dict:
    feed = feedparser.parse(GOOGLE_NEWS.format(query=query))
    return {
        "source": "Google News RSS",
        "reliability": "high",
        "count": len(feed.entries),
        "items": [item.title for item in feed.entries[:3]],
    }


async def top_headlines() -> list[Dict]:
    bbc = feedparser.parse(BBC_NEWS)
    reuters = feedparser.parse(REUTERS)
    return [
        {"source": "BBC RSS", "count": len(bbc.entries), "items": [x.title for x in bbc.entries[:2]]},
        {"source": "Reuters RSS", "count": len(reuters.entries), "items": [x.title for x in reuters.entries[:2]]},
    ]
