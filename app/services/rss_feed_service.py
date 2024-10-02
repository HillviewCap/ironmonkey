"""
This module provides services for managing RSS feeds in the application.

It includes functionality for creating, retrieving, updating, and deleting
RSS feeds, as well as parsing feed content.
"""

import uuid
from typing import List, Dict
from sqlalchemy.orm import Session
from app.extensions import db
from dateutil import parser as date_parser

from app.models import RSSFeed, ParsedContent, AwesomeThreatIntelBlog
import asyncio
from app.utils.rss_validator import validate_rss_url
from app.utils.http_client import fetch_feed_info
from app.services.feed_parser_service import fetch_and_parse_feed
from app.utils.logging_config import setup_logger
from app.services.parsed_content_service import ParsedContentService

logger = setup_logger('rss_feed_service', 'rss_feed_service.log')

UUID = uuid.UUID

class RSSFeedService:
    """
    A service class for managing RSS feed operations.

    This class provides static methods for various operations related to
    RSS feeds, including retrieval, creation, updating, deletion, and parsing.
    """
    @staticmethod
    def get_all_feeds() -> List[RSSFeed]:
        """
        Retrieve all RSS feeds.

        Returns:
            List[RSSFeed]: A list of all RSS feed objects.
        """
        with Session(db.engine) as session:
            return session.query(RSSFeed).all()

    @staticmethod
    def get_feed_by_id(feed_id: uuid.UUID) -> RSSFeed:
        """
        Retrieve an RSS feed by its ID.

        Args:
            feed_id (uuid.UUID): The unique identifier of the RSS feed.

        Returns:
            RSSFeed: The RSS feed object with the given ID.
        """
        with Session(db.engine) as session:
            return session.get(RSSFeed, feed_id)

    @staticmethod
    async def create_feed(feed_data: Dict[str, str]) -> RSSFeed:
        """
        Create a new RSS feed.

        Args:
            feed_data (Dict[str, str]): A dictionary containing the feed details.

        Returns:
            RSSFeed: The newly created RSS feed object.

        Raises:
            ValueError: If the RSS feed URL is invalid or already exists.
        """
        url = feed_data['url']
        logger.info(f"Attempting to create feed with URL: {url}")
        
        try:
            if not await validate_rss_url(url):
                logger.error(f"Invalid RSS feed URL: {url}")
                raise ValueError(f"Invalid RSS feed URL: {url}")
        except Exception as e:
            logger.error(f"Error validating RSS feed URL: {url}, {str(e)}")
            raise ValueError(f"Error validating RSS feed URL: {url}, {str(e)}")

        with Session(db.engine) as session:
            existing_feed = session.query(RSSFeed).filter_by(url=url).first()
            if existing_feed:
                logger.warning(f"RSS feed URL already exists: {url}")
                raise ValueError("RSS feed URL already exists")

            try:
                logger.info(f"Fetching feed info for URL: {url}")
                feed_info = await fetch_feed_info(url)
                last_build_date = feed_info.get('last_build_date')
                if last_build_date:
                    try:
                        parsed_date = date_parser.parse(last_build_date)
                        last_build_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        logger.warning(f"Could not parse last_build_date: {e}")
                        last_build_date = None

                feed = RSSFeed(
                    id=uuid.uuid4(),
                    url=url,
                    title=feed_info['title'],
                    description=feed_info['description'],
                    last_build_date=last_build_date,
                    category=feed_data.get('category', 'Uncategorized')
                )

                session.add(feed)
                session.commit()
                logger.info(f"Created new RSS feed: {feed.title}")

                # Immediately parse the newly created feed
                asyncio.create_task(RSSFeedService.parse_feed(feed.id))

                return feed
            except Exception as e:
                logger.error(f"Error creating RSS feed: {str(e)}")
                raise ValueError(f"Error creating RSS feed: {str(e)}")

    @staticmethod
    async def parse_feed(feed_id: UUID) -> List[ParsedContent]:
        """
        Parse an RSS feed and store the parsed content.

        Args:
            feed_id (UUID): The ID of the RSS feed to parse.

        Returns:
            List[ParsedContent]: A list of parsed content items.

        Raises:
            ValueError: If the RSS feed is not found.
        """
        with Session(db.engine) as session:
            feed = session.get(RSSFeed, feed_id)
            if not feed:
                raise ValueError(f"RSS feed with ID {feed_id} not found.")

            parsed_content = await fetch_and_parse_feed(feed)
            return parsed_content

    @staticmethod
    async def update_feed(feed_id: uuid.UUID, feed_data: Dict[str, str]) -> RSSFeed:
        """
        Update an existing RSS feed.

        Args:
            feed_id (uuid.UUID): The unique identifier of the RSS feed.
            feed_data (Dict[str, str]): A dictionary containing the updated feed details.

        Returns:
            RSSFeed: The updated RSS feed object.
        """
        with Session(db.engine) as session:
            feed = session.query(RSSFeed).get(feed_id)
            if not feed:
                raise ValueError(f"RSS feed with ID {feed_id} not found.")

            url = feed_data.get('url', feed.url)
            if url != feed.url and not validate_rss_url(url):
                raise ValueError(f"Invalid RSS feed URL: {url}")

            if url != feed.url:
                feed_info = await fetch_feed_info(url)
                feed.url = url
                feed.title = feed_info['title']
                feed.description = feed_info['description']
                
                last_build_date = feed_info.get('last_build_date')
                if last_build_date:
                    try:
                        parsed_date = date_parser.parse(last_build_date)
                        feed.last_build_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        logger.warning(f"Could not parse last_build_date: {e}")

            feed.category = feed_data.get('category', feed.category)

            session.commit()
            logger.info(f"Updated RSS feed: {feed.title}")
            return feed

    @staticmethod
    def delete_feed(feed_id: uuid.UUID) -> None:
        """
        Delete an RSS feed.

        Args:
            feed_id (uuid.UUID): The unique identifier of the RSS feed.

        Raises:
            ValueError: If the RSS feed with the given ID is not found.
        """
        with Session(db.engine) as session:
            feed = session.get(RSSFeed, feed_id)
            if not feed:
                raise ValueError(f"RSS feed with ID {feed_id} not found.")

            session.delete(feed)
            session.commit()
            logger.info(f"Deleted RSS feed: {feed.title}")

        # Delete associated parsed content
        try:
            ParsedContentService.delete_parsed_content_by_feed_id(feed_id)
            logger.info(f"Deleted associated parsed content for feed ID: {feed_id}")
        except Exception as e:
            logger.error(f"Error deleting associated parsed content: {str(e)}")

    @staticmethod
    async def parse_feed(feed_id: uuid.UUID) -> None:
        """
        Manually trigger the parsing of an RSS feed.

        Args:
            feed_id (uuid.UUID): The unique identifier of the RSS feed.
        """
        with Session(db.engine) as session:
            feed = session.get(RSSFeed, feed_id)
            if not feed:
                raise ValueError(f"RSS feed with ID {feed_id} not found.")

            await fetch_and_parse_feed(feed)
            logger.info(f"Manually parsed RSS feed: {feed.title}")
