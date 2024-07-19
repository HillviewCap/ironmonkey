from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime
from typing import Optional

import httpx
import feedparser
from flask import current_app
from sqlalchemy.orm import Session

from app.models import db, ParsedContent, RSSFeed
from app.utils.logging_config import setup_logger
from app.utils.jina_api import parse_content

logger = setup_logger('feed_parser_service', 'feed_parser_service.log')

# The logger is already set up in logging_config.py, so we can use it directly

def sanitize_html(text: str) -> str:
    """
    Remove HTML tags and unescape HTML entities.
    
    Args:
        text (str): The input text containing HTML.
    
    Returns:
        str: The sanitized text with HTML tags removed and entities unescaped.
    """
    # Unescape HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def fetch_and_parse_feed(feed: RSSFeed) -> int:
    """Fetch and parse a single RSS feed."""
    new_entries_count = 0
    try:
        if current_app.debug:
            logger.debug(f"Starting to fetch and parse feed: {feed.url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(feed.url, timeout=30.0, headers=headers)
            response.raise_for_status()

            # Check if the URL has been redirected
            if response.url != feed.url:
                logger.info(f"Feed URL redirected from {feed.url} to {response.url}")
                feed.url = str(response.url)
                db.session.commit()

            feed_data = feedparser.parse(response.text)
            if current_app.debug:
                logger.debug(f"Parsed feed data for {feed.url}")
            for entry in feed_data.entries:
                try:
                    url = entry.link
                    title = entry.get('title', '')
                    if current_app.debug:
                        logger.debug(f"Processing entry: {url} - {title}")
                    art_hash = hashlib.sha256(f"{url}{title}".encode()).hexdigest()

                    existing_content = ParsedContent.query.filter_by(art_hash=art_hash).first()
                    if not existing_content:
                        if current_app.debug:
                            logger.debug(f"New content found: {url}")
                        parsed_content = await parse_content(url)
                        if parsed_content is not None:
                            pub_date = entry.get('published', '')
                            if pub_date:
                                try:
                                    pub_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                                    pub_date = pub_date.strftime('%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    logger.warning(f"Could not parse date: {pub_date}. Using original string.")
                            
                            new_content = ParsedContent(
                                content=parsed_content,
                                feed_id=feed.id,
                                url=url,
                                title=sanitize_html(title),
                                description=sanitize_html(entry.get('description', '')),
                                pub_date=pub_date,
                                creator=sanitize_html(entry.get('author', '')),
                                art_hash=art_hash
                            )
                            db.session.add(new_content)
                            db.session.flush()  # This will assign the UUID to new_content

                            # TODO: Implement category handling if needed
                            new_entries_count += 1
                            if current_app.debug:
                                logger.debug(f"Added new entry: {url}")
                        else:
                            logger.warning(f"Failed to parse content for URL: {url}")
                    else:
                        if current_app.debug:
                            logger.debug(f"Content already exists: {url}")
                except Exception as entry_error:
                    logger.error(f"Error processing entry {entry.get('link', 'Unknown')} from feed {feed.url}: {str(entry_error)}")
                    continue  # Continue with the next entry

            db.session.commit()
            logger.info(f"Feed: {feed.url} - Added {new_entries_count} new entries to database")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching feed {feed.url}: {e}")
        raise ValueError(f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}")
    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting {feed.url}: {e}")
        raise ValueError(f"Request error: {str(e)}")
    except httpx.TimeoutException as e:
        logger.error(f"Timeout occurred while fetching feed {feed.url}: {e}")
        raise ValueError(f"Timeout error: The request to {feed.url} timed out")
    except feedparser.FeedParserError as e:
        logger.error(f"FeedParser error occurred while parsing feed {feed.url}: {e}")
        raise ValueError(f"FeedParser error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred while parsing feed {feed.url}: {e}", exc_info=True)
        raise RuntimeError(f"Unexpected error: {str(e)}")
    finally:
        return new_entries_count
from typing import Optional
from datetime import datetime
import httpx
import feedparser
from app.models import db, ParsedContent, RSSFeed
from logging_config import setup_logger

logger = setup_logger('feed_parser_service', 'feed_parser_service.log')

async def fetch_and_parse_feed(feed: RSSFeed) -> None:
    """Fetch and parse an RSS feed, storing new entries in the database."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(feed.url)
            response.raise_for_status()
            feed_data = feedparser.parse(response.text)

        for entry in feed_data.entries:
            content = entry.get("content", [{}])[0].get("value", "")
            if not content:
                content = entry.get("summary", "")

            pub_date = entry.get("published_parsed")
            if pub_date:
                pub_date = datetime(*pub_date[:6])

            existing_content = ParsedContent.query.filter_by(url=entry.link).first()
            if existing_content:
                continue

            new_content = ParsedContent(
                title=entry.get("title", ""),
                url=entry.link,
                content=content,
                description=entry.get("summary", ""),
                pub_date=pub_date,
                creator=entry.get("author", ""),
                feed_id=feed.id,
            )
            db.session.add(new_content)

        db.session.commit()
        logger.info(f"Successfully parsed feed: {feed.url}")
    except Exception as e:
        logger.error(f"Error parsing feed {feed.url}: {str(e)}", exc_info=True)
        db.session.rollback()
