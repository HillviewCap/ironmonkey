from __future__ import annotations

import feedparser
import logging
import httpx
from typing import Dict, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

async def validate_rss_url(url: str) -> Tuple[bool, str]:
    """
    Validate if the given URL is a potentially valid RSS feed.

    This function attempts to parse the given URL as an RSS feed using the
    feedparser library. It checks if the parsed result has a version and is not
    marked as 'bozo' (feedparser's way of indicating an invalid feed).

    Args:
        url (str): The URL to validate.

    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating if the URL is
        potentially a valid RSS feed, and the final URL after any redirects.

    Example:
        >>> validate_rss_url('http://example.com/valid_rss_feed.xml')
        (True, 'http://example.com/valid_rss_feed.xml')
        >>> validate_rss_url('http://example.com/invalid_feed.html')
        (False, 'http://example.com/invalid_feed.html')
    """
    try:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            logger.warning(f"Invalid URL format: {url}")
            return False, url

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url)
            final_url = str(response.url)

        parsed = feedparser.parse(response.text)
        if parsed.version != '' and not parsed.bozo:
            logger.info(f"URL {final_url} passed RSS validation")
            return True, final_url
        else:
            logger.warning(f"URL {final_url} failed RSS validation: version={parsed.version}, bozo={parsed.bozo}")
            return False, final_url
    except Exception as e:
        logger.error(f"Error validating RSS feed URL {url}: {str(e)}")
        return False, url


async def extract_feed_info(url: str) -> Optional[Dict[str, str]]:
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
        - 'url': The final URL of the feed after any redirects

    Example:
        >>> info = await extract_feed_info('http://example.com/valid_rss_feed.xml')
        >>> print(info['title'])
        'Example Feed'
    """
    try:
        is_valid, final_url = await validate_rss_url(url)
        if not is_valid:
            return None

        async with httpx.AsyncClient() as client:
            response = await client.get(final_url)
        parsed = feedparser.parse(response.text)

        feed_info = {
            'title': parsed.feed.get('title', 'Untitled Feed'),
            'description': parsed.feed.get('description', 'No description available'),
            'link': parsed.feed.get('link', final_url),
            'last_build_date': parsed.feed.get('updated') or parsed.feed.get('published') or datetime.now().isoformat(),
            'url': final_url,
        }

        return feed_info
    except Exception as e:
        logger.error(f"Error extracting feed info from {url}: {str(e)}")
        return None
