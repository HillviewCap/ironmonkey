import uuid
from typing import List, Dict
from sqlalchemy.orm import Session
from app.extensions import db

from app.models import RSSFeed
from ..models.parsed_content import ParsedContent
from app.utils.rss_validator import validate_rss_url, extract_feed_info
from app.services.feed_parser_service import fetch_and_parse_feed
from logging_config import setup_logger
from app.services.parsed_content_service import ParsedContentService

logger = setup_logger('rss_feed_service', 'rss_feed_service.log')

class RSSFeedService:
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
            return session.query(RSSFeed).get(feed_id)

    @staticmethod
    def create_feed(feed_data: Dict[str, str]) -> RSSFeed:
        """
        Create a new RSS feed.

        Args:
            feed_data (Dict[str, str]): A dictionary containing the feed details.

        Returns:
            RSSFeed: The newly created RSS feed object.
        """
        url = feed_data['url']
        if not validate_rss_url(url):
            raise ValueError(f"Invalid RSS feed URL: {url}")

        feed_info = extract_feed_info(url)
        feed = RSSFeed(
            id=uuid.uuid4(),
            url=url,
            title=feed_info['title'],
            description=feed_info['description'],
            last_build_date=feed_info['last_build_date'],
            category=feed_data.get('category', 'Uncategorized')
        )

        with Session(db.engine) as session:
            session.add(feed)
            session.commit()
            logger.info(f"Created new RSS feed: {feed.title}")
            return feed

    @staticmethod
    def update_feed(feed_id: uuid.UUID, feed_data: Dict[str, str]) -> RSSFeed:
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
                feed_info = extract_feed_info(url)
                feed.url = url
                feed.title = feed_info['title']
                feed.description = feed_info['description']
                feed.last_build_date = feed_info['last_build_date']

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
            feed = session.query(RSSFeed).get(feed_id)
            if not feed:
                raise ValueError(f"RSS feed with ID {feed_id} not found.")

            session.delete(feed)
            session.commit()
            logger.info(f"Deleted RSS feed: {feed.title}")

        # Delete associated parsed content
        ParsedContentService.delete_parsed_content_by_feed_id(feed_id)

    @staticmethod
    async def parse_feed(feed_id: uuid.UUID) -> None:
        """
        Manually trigger the parsing of an RSS feed.

        Args:
            feed_id (uuid.UUID): The unique identifier of the RSS feed.
        """
        with Session(db.engine) as session:
            feed = session.query(RSSFeed).get(feed_id)
            if not feed:
                raise ValueError(f"RSS feed with ID {feed_id} not found.")

            await fetch_and_parse_feed(feed)
            logger.info(f"Manually parsed RSS feed: {feed.title}")
