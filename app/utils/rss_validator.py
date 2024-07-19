from __future__ import annotations

import feedparser
from typing import Dict, Optional
from datetime import datetime
from urllib.parse import urlparse


def validate_rss_url(url: str) -> bool:
    """
    Validate if the given URL is a valid RSS feed.

    This function attempts to parse the given URL as an RSS feed using the
    feedparser library. It checks if the parsed result has a version and is not
    marked as 'bozo' (feedparser's way of indicating an invalid feed).

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is a valid RSS feed, False otherwise.

    Example:
        >>> validate_rss_url('http://example.com/valid_rss_feed.xml')
        True
        >>> validate_rss_url('http://example.com/invalid_feed.html')
        False
    """
    try:
        parsed = feedparser.parse(url)
        return parsed.version != '' and not parsed.bozo
    except Exception:
        return False


def extract_feed_info(url: str) -> Optional[Dict[str, str]]:
    """
    Extract basic information from an RSS feed.

    This function attempts to parse the given URL as an RSS feed and extract
    key information such as title, description, link, and last build date.
    If the feed is invalid or cannot be parsed, it returns None.

    Args:
        url (str): The URL of the RSS feed.

    Returns:
        Optional[Dict[str, str]]: A dictionary containing feed information,
                                  or None if the feed is invalid.
        The dictionary contains the following keys:
        - 'title': The title of the feed
        - 'description': A brief description of the feed
        - 'link': The website associated with the feed
        - 'last_build_date': The date when the feed was last updated

    Example:
        >>> info = extract_feed_info('http://example.com/valid_rss_feed.xml')
        >>> print(info['title'])
        'Example Feed'
    """
    try:
        parsed = feedparser.parse(url)
        
        if parsed.version == '' or parsed.bozo:
            return None

        feed_info = {
            'title': parsed.feed.get('title', 'Untitled Feed'),
            'description': parsed.feed.get('description', 'No description available'),
            'link': parsed.feed.get('link', url),
            'last_build_date': parsed.feed.get('updated') or parsed.feed.get('published') or datetime.now().isoformat(),
        }

        return feed_info
    except Exception:
        return None
