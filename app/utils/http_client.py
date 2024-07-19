import aiohttp
import asyncio
import feedparser
from typing import Dict

async def fetch_feed_info(url: str) -> Dict[str, str]:
    """
    Fetch feed information from the given URL.

    Args:
        url (str): The URL of the RSS feed.

    Returns:
        dict: A dictionary containing feed information.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                feed = feedparser.parse(content)
                if feed.bozo:
                    raise Exception(f"Failed to parse feed: {feed.bozo_exception}")
                
                feed_info = {
                    "title": feed.feed.get("title", "No Title"),
                    "description": feed.feed.get("description", "No Description"),
                    "last_build_date": feed.feed.get("updated", "No Date"),
                    "category": "Default Category"  # Set a default category
                }
                return feed_info
            else:
                raise Exception(f"Failed to fetch feed: HTTP {response.status}")
