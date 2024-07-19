from __future__ import annotations

import feedparser
from typing import Dict, Optional
from urllib.parse import urlparse


def validate_rss_url(url: str) -> bool:
    """
    Validate if the given URL is a valid RSS feed.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is a valid RSS feed, False otherwise.
    """
    parsed = feedparser.parse(url)
    return parsed.version != '' and not parsed.bozo


def extract_feed_info(url: str) -> Optional[Dict[str, str]]:
    """
    Extract basic information from an RSS feed.

    Args:
        url (str): The URL of the RSS feed.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing feed information,
                                  or None if the feed is invalid.
    """
    parsed = feedparser.parse(url)
    
    if parsed.version == '' or parsed.bozo:
        return None

    feed_info = {
        'title': parsed.feed.get('title', 'Untitled Feed'),
        'description': parsed.feed.get('description', 'No description available'),
        'link': parsed.feed.get('link', url),
    }

    return feed_info
