"""
This module provides services for managing RSS feeds in the application.

It includes functionality for creating, retrieving, updating, and deleting
RSS feeds, as well as parsing feed content.
"""

import uuid
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.extensions import db
from app.models import RSSFeed, ParsedContent
from app.utils.rss_validator import validate_rss_url
from app.utils.http_client import fetch_feed_info
from app.services.feed_parser_service import fetch_and_parse_feed
from app.utils.logging_config import setup_logger
from app.services.parsed_content_service import ParsedContentService
from app.utils.db_lock import with_lock, is_database_locked, acquire_lock, release_lock

logger = setup_logger('rss_feed_service', 'rss_feed_service.log')

class RSSFeedService:
    """
    A service class for managing RSS feed operations.

    This class provides methods for various operations related to
    RSS feeds, including retrieval, creation, updating, deletion, and parsing.
    """

    @staticmethod
    @with_lock
    def get_all_feeds() -> List[RSSFeed]:
        """Retrieve all RSS feeds."""
        with Session(db.engine) as session:
            return session.query(RSSFeed).all()

    @staticmethod
    @with_lock
    def get_feed_by_id(feed_id: uuid.UUID) -> Optional[RSSFeed]:
        """Retrieve an RSS feed by its ID."""
        with Session(db.engine) as session:
            return session.get(RSSFeed, feed_id)

    @staticmethod
    @with_lock
    async def create_feed(feed_data: Dict[str, str]) -> RSSFeed:
        """Create a new RSS feed."""
        url = feed_data['url']
        logger.info(f"Attempting to create feed with URL: {url}")
        
        await RSSFeedService._validate_feed_url(url)
        
        with Session(db.engine) as session:
            RSSFeedService._check_existing_feed(session, url)
            feed = await RSSFeedService._create_feed_object(session, url, feed_data)
            return feed

    @staticmethod
    async def update_feed(feed_id: uuid.UUID, feed_data: Dict[str, str]) -> RSSFeed:
        """Update an existing RSS feed."""
        RSSFeedService._check_database_lock()
        
        with acquire_lock():
            with Session(db.engine) as session:
                feed = RSSFeedService._get_feed_or_raise(session, feed_id)
                await RSSFeedService._update_feed_data(feed, feed_data)
                session.commit()
                logger.info(f"Updated RSS feed: {feed.title}")
                return feed

    @staticmethod
    def delete_feed(feed_id: uuid.UUID) -> None:
        """Delete an RSS feed."""
        RSSFeedService._check_database_lock()
        
        with acquire_lock():
            with Session(db.engine) as session:
                feed = RSSFeedService._get_feed_or_raise(session, feed_id)
                session.delete(feed)
                session.commit()
                logger.info(f"Deleted RSS feed: {feed.title}")
            
            ParsedContentService.delete_parsed_content_by_feed_id(feed_id)

    @staticmethod
    async def parse_feed(feed_id: uuid.UUID) -> List[ParsedContent]:
        """Parse an RSS feed and store the parsed content."""
        RSSFeedService._check_database_lock()
        
        with acquire_lock():
            with Session(db.engine) as session:
                feed = RSSFeedService._get_feed_or_raise(session, feed_id)
                parsed_content = await fetch_and_parse_feed(feed)
                return parsed_content

    # Helper methods
    @staticmethod
    async def _validate_feed_url(url: str) -> None:
        try:
            if not await validate_rss_url(url):
                raise ValueError(f"Invalid RSS feed URL: {url}")
        except Exception as e:
            logger.error(f"Error validating RSS feed URL: {url}, {str(e)}")
            raise ValueError(f"Error validating RSS feed URL: {url}, {str(e)}")

    @staticmethod
    def _check_existing_feed(session: Session, url: str) -> None:
        existing_feed = session.query(RSSFeed).filter_by(url=url).first()
        if existing_feed:
            logger.warning(f"RSS feed URL already exists: {url}")
            raise ValueError("RSS feed URL already exists")

    @staticmethod
    async def _create_feed_object(session: Session, url: str, feed_data: Dict[str, str]) -> RSSFeed:
        try:
            logger.info(f"Fetching feed info for URL: {url}")
            feed_info = await fetch_feed_info(url)
            feed = RSSFeed(
                id=uuid.uuid4(),
                url=url,
                title=feed_info['title'],
                description=feed_info['description'],
                last_build_date=feed_info['last_build_date'],
                category=feed_data.get('category', 'Uncategorized')
            )
            session.add(feed)
            session.commit()
            logger.info(f"Created new RSS feed: {feed.title}")
            return feed
        except Exception as e:
            logger.error(f"Error creating RSS feed: {str(e)}")
            raise ValueError(f"Error creating RSS feed: {str(e)}")

    @staticmethod
    def _check_database_lock() -> None:
        if is_database_locked():
            logger.warning("Database is locked. Cannot perform the operation at this time.")
            raise ValueError("Database is locked. Cannot perform the operation at this time.")

    @staticmethod
    def _get_feed_or_raise(session: Session, feed_id: uuid.UUID) -> RSSFeed:
        feed = session.get(RSSFeed, feed_id)
        if not feed:
            raise ValueError(f"RSS feed with ID {feed_id} not found.")
        return feed

    @staticmethod
    async def _update_feed_data(feed: RSSFeed, feed_data: Dict[str, str]) -> None:
        url = feed_data.get('url', feed.url)
        if url != feed.url:
            await RSSFeedService._validate_feed_url(url)
            feed_info = await fetch_feed_info(url)
            feed.url = url
            feed.title = feed_info['title']
            feed.description = feed_info['description']
            feed.last_build_date = feed_info['last_build_date']
        feed.category = feed_data.get('category', feed.category)
