"""
This module provides services for parsing RSS feeds and storing their content.

It includes functionality for fetching RSS feeds, parsing their content,
and storing new entries in the database.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import httpx
import feedparser
from app.services.html_sanitizer_service import sanitize_html
from flask import current_app
from sqlalchemy.orm import Session

from app.models import ParsedContent, RSSFeed, Category
from app.utils.db_connection_manager import DBConnectionManager
from app.utils.logging_config import setup_logger
from app.utils.jina_api import parse_content

from typing import Optional
from datetime import datetime
import httpx
import feedparser
from app.models import db, ParsedContent, RSSFeed
import os
import fcntl
from app.utils.logging_config import setup_logger

logger = setup_logger("feed_parser_service", "feed_parser_service.log")

LOCK_FILE = "feed_parser.lock"

def acquire_lock():
    lock_file = open(LOCK_FILE, 'w')
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file
    except IOError:
        return None

def release_lock(lock_file):
    fcntl.flock(lock_file, fcntl.LOCK_UN)
    lock_file.close()
    os.remove(LOCK_FILE)

def get_or_create_category(name):
    category = Category.query.filter_by(name=name).first()
    if not category:
        category = Category(name=name)
        db.session.add(category)
        db.session.flush()  # This will assign the id to the new category
    return category


async def fetch_and_parse_feed(feed: RSSFeed) -> int:
    """
    Fetch and parse a single RSS feed.

    This function retrieves the content of an RSS feed, parses it, and stores new entries
    in the database. It handles redirects, updates feed metadata, and processes individual
    entries.

    Args:
        feed (RSSFeed): The RSS feed object to fetch and parse.

    Returns:
        int: The number of new entries added to the database.

    Raises:
        ValueError: If there's an HTTP error, request error, or timeout.
        RuntimeError: For unexpected errors during parsing.
    """
    new_entries_count = 0
    lock_file = acquire_lock()
    if not lock_file:
        logger.warning("Another instance is already running. Skipping this run.")
        return new_entries_count

    try:
        logger.info(f"Starting to fetch and parse feed: {feed.url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(feed.url, headers=headers)
            response.raise_for_status()

            with DBConnectionManager.get_session() as session:
                # Check if the URL has been redirected
                if str(response.url) != feed.url:
                    logger.info(f"Feed URL redirected from {feed.url} to {response.url}")
                    feed.url = str(response.url)
                    session.commit()

                feed_data = feedparser.parse(response.content)
                logger.info(f"Parsed feed data for {feed.url}")
                # Update the feed title and description if available
                if "title" in feed_data.feed:
                    feed.title = sanitize_html(feed_data.feed.title)
                if "description" in feed_data.feed:
                    feed.description = sanitize_html(feed_data.feed.description)
                session.commit()

                total_entries = len(feed_data.entries)
                logger.info(f"Found {total_entries} entries in feed: {feed.url}")

                for index, entry in enumerate(feed_data.entries, 1):
                    try:
                        url = entry.link
                        title = entry.get("title", "")
                        logger.info(f"Processing entry {index}/{total_entries}: {url} - {title}")

                        existing_content = session.query(ParsedContent).filter_by(
                            url=url, feed_id=feed.id
                        ).first()
                        if not existing_content:
                            logger.info(f"New content found: {url}")
                            parsed_content = await parse_content(url)
                            if parsed_content is not None:
                                pub_date = entry.get("published", "")
                                if pub_date:
                                    try:
                                        # Try parsing with multiple formats
                                        for date_format in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"]:
                                            try:
                                                parsed_date = datetime.strptime(pub_date, date_format)
                                                pub_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                                                break
                                            except ValueError:
                                                continue
                                        else:
                                            # If no format worked, raise ValueError to log a warning
                                            raise ValueError("No matching date format found")
                                    except ValueError:
                                        logger.warning(
                                            f"Could not parse date: {pub_date}. Using original string."
                                        )

                                new_content = ParsedContent(
                                    content=sanitize_html(parsed_content),
                                    feed_id=feed.id,
                                    url=url,
                                    title=sanitize_html(title),
                                    description=sanitize_html(entry.get("description", "")),
                                    pub_date=pub_date,
                                    creator=sanitize_html(entry.get("author", "")),
                                )
                                session.add(new_content)
                                session.flush()  # This will assign the UUID to new_content

                                # Handle categories
                                categories = entry.get("tags", [])
                                for category in categories:
                                    cat_name = sanitize_html(category.get("term", ""))
                                    if cat_name:
                                        cat_obj = get_or_create_category(cat_name)
                                        new_content.categories.append(cat_obj)
                                new_entries_count += 1
                                logger.info(f"Added new entry: {url}")
                            else:
                                logger.warning(f"Failed to parse content for URL: {url}")
                        else:
                            logger.info(f"Content already exists: {url}")
                    except Exception as entry_error:
                        logger.error(
                            f"Error processing entry {entry.get('link', 'Unknown')} from feed {feed.url}: {str(entry_error)}",
                            exc_info=True
                        )
                        continue  # Continue with the next entry

                session.commit()
                logger.info(
                    f"Feed: {feed.url} - Added {new_entries_count} new entries to database"
                )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching feed {feed.url}: {e}", exc_info=True)
        raise ValueError(
            f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}"
        )
    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting {feed.url}: {e}", exc_info=True)
        raise ValueError(f"Request error: {str(e)}")
    except httpx.TimeoutException as e:
        logger.error(f"Timeout occurred while fetching feed {feed.url}: {e}", exc_info=True)
        raise ValueError(f"Timeout error: The request to {feed.url} timed out")
    except feedparser.FeedParserError as e:
        logger.error(f"FeedParser error occurred while parsing feed {feed.url}: {e}", exc_info=True)
        raise ValueError(f"FeedParser error: {str(e)}")
    except Exception as e:
        logger.error(
            f"Unexpected error occurred while parsing feed {feed.url}: {e}",
            exc_info=True,
        )
        raise RuntimeError(f"Unexpected error: {str(e)}")
    finally:
        if lock_file:
            release_lock(lock_file)
        return new_entries_count
