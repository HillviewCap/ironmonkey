"""
This module provides services for parsing RSS feeds and storing their content.

It includes functionality for fetching RSS feeds, parsing their content,
and storing new entries in the database.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List

import httpx
import feedparser
from dateutil import parser as date_parser
from app.services.html_sanitizer_service import sanitize_html
from flask import current_app
import asyncio
from sqlalchemy.orm import Session

from app.models import ParsedContent, RSSFeed, Category
from app.utils.db_connection_manager import DBConnectionManager
from app.utils.logging_config import setup_logger
from app.utils.jina_api import parse_content

import os
import tempfile
import time
from sqlalchemy.exc import OperationalError
import random

logger = setup_logger("feed_parser_service", "feed_parser_service.log")

from sqlalchemy.orm import Session
from sqlalchemy import select, func

def get_or_create_category(session: Session, name: str) -> Category:
    max_retries = 5
    retry_delay = 1  # Start with 1 second delay

    for attempt in range(max_retries):
        try:
            category = session.query(Category).filter_by(name=name).first()
            if not category:
                category = Category(name=name)
                session.add(category)
                session.flush()  # This will assign the id to the new category
            return category
        except OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                retry_delay += random.uniform(0, 1)  # Add jitter
                session.rollback()
            else:
                logger.error(f"Failed to get or create category after {max_retries} attempts: {e}")
                raise

async def fetch_and_parse_feed(feed_id: str, force_update: bool = False) -> int:
    """
    Fetch and parse a single RSS feed.

    This function retrieves the content of an RSS feed, parses it, and stores new entries
    in the database. It handles redirects, updates feed metadata, and processes all
    entries every time.

    Args:
        feed_id (str): The ID of the RSS feed to fetch and parse.
        force_update (bool): Not used, kept for compatibility.

    Returns:
        int: The number of new entries added to the database.

    Raises:
        ValueError: If there's an HTTP error, request error, or timeout.
        RuntimeError: For unexpected errors during parsing.
    """
    new_entries_count = 0
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        with DBConnectionManager.get_session() as session:
            feed = session.get(RSSFeed, feed_id)
            if not feed:
                logger.error(f"Feed with id {feed_id} not found")
                return 0

            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(feed.url, headers=headers)
                response.raise_for_status()

                # Check if the URL has been redirected
                if str(response.url) != feed.url:
                    feed.url = str(response.url)
                    session.commit()

            feed_data = feedparser.parse(response.content)

            # Update feed metadata
            if "title" in feed_data.feed:
                feed.title = sanitize_html(feed_data.feed.title)
            if "description" in feed_data.feed:
                feed.description = sanitize_html(feed_data.feed.description)
            
            # Update last_build_date if available
            if 'updated' in feed_data.feed:
                try:
                    new_build_date = date_parser.parse(feed_data.feed.updated)
                    if new_build_date.tzinfo is None:
                        new_build_date = new_build_date.replace(tzinfo=timezone.utc)
                    feed.last_build_date = new_build_date.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.warning(f"Could not parse feed updated date: {e}")

            feed.last_checked = datetime.now(timezone.utc)
            session.commit()

            total_entries = len(feed_data.entries)

            for entry in feed_data.entries:
                try:
                    url = entry.link
                    title = entry.get("title", "")

                    pub_date = entry.get("published", "")
                    if pub_date and pub_date.lower() != "invalid date":
                        try:
                            parsed_date = date_parser.parse(pub_date)
                            if parsed_date.tzinfo is None:
                                parsed_date = parsed_date.replace(tzinfo=datetime.timezone.utc)
                        except Exception as e:
                            logger.warning(f"Could not parse date: {pub_date}. Error: {str(e)}. Using current date and time.")
                            parsed_date = datetime.now(datetime.timezone.utc)
                    else:
                        logger.warning(f"Invalid or no published date found: {pub_date}. Using current date and time.")
                        parsed_date = datetime.now(datetime.timezone.utc)

                    existing_content = session.execute(
                        select(ParsedContent).filter_by(url=url, feed_id=feed.id).with_for_update(nowait=True)
                    ).scalar_one_or_none()

                    if not existing_content:
                        parsed_content = await parse_content(url)
                        if parsed_content is not None:
                            new_content = ParsedContent(
                                content=sanitize_html(parsed_content),
                                feed_id=feed.id,
                                url=url,
                                title=sanitize_html(title),
                                description=sanitize_html(entry.get("description", "")),
                                pub_date=parsed_date,
                                creator=sanitize_html(entry.get("author", "")),
                            )
                            session.add(new_content)
                            session.flush()  # This will assign the UUID to new_content

                            # Handle categories
                            categories = entry.get("tags", [])
                            for category in categories:
                                cat_name = sanitize_html(category.get("term", ""))
                                if cat_name:
                                    cat_obj = get_or_create_category(session, cat_name)
                                    new_content.categories.append(cat_obj)
                            new_entries_count += 1
                        else:
                            logger.warning(f"Failed to parse content for URL: {url}")
                except OperationalError as e:
                    if "database is locked" in str(e):
                        logger.warning(f"Database locked for entry {url}, skipping...")
                        continue
                    else:
                        raise
                except Exception as entry_error:
                    logger.error(
                        f"Error processing entry {entry.get('link', 'Unknown')} from feed {feed.url}: {str(entry_error)}",
                        exc_info=True
                    )
                    session.rollback()
                    continue  # Continue with the next entry

                session.commit()  # Commit after each successful entry processing

            logger.info(f"Feed: {feed.url} - Added {new_entries_count} new entries to database")
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
        return new_entries_count
def fetch_and_parse_feed_sync(feed_id: str, force_update: bool = False) -> int:
    return asyncio.run(fetch_and_parse_feed(feed_id, force_update))
