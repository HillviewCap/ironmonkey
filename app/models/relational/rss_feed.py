from __future__ import annotations
from uuid import uuid4
from typing import Dict, Any, Tuple, Optional
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db
from app.utils.http_client import fetch_feed_info

from pydantic import BaseModel

class RSSFeed(db.Model):
    """Model for storing RSS feed information."""

    __tablename__ = 'rss_feed'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    last_build_date = Column(String(100), nullable=True)
    etag = Column(String(255), nullable=True)
    last_modified = Column(String(255), nullable=True)
    
    # Relationship with ParsedContent
    parsed_items = db.relationship('ParsedContent', back_populates='feed', cascade='all, delete-orphan')
    
    # Relationship with AwesomeThreatIntelBlog
    awesome_blog_id = Column(UUID(as_uuid=True), ForeignKey('awesome_threat_intel_blog.id'), nullable=True)
    awesome_blog = db.relationship('AwesomeThreatIntelBlog', back_populates='rss_feeds')

    class Config:
        from_attributes = True

    def __init__(self, **kwargs: Any) -> None:
        super(RSSFeed, self).__init__(**kwargs)
        if not self.id:
            self.id = uuid4()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the RSSFeed object to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the RSSFeed object.
        """
        return {
            'id': str(self.id),
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'last_build_date': self.last_build_date
        }

    @staticmethod
    def fetch_feed_info(url: str) -> Tuple[str, str, Optional[str]]:
        """
        Fetch RSS feed information from the given URL.

        Args:
            url (str): The URL of the RSS feed.

        Returns:
            Tuple[str, str, Optional[str]]: A tuple containing the title, description, and last build date.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(fetch_feed_info(url))
        loop.close()
        return result['title'], result.get('description'), result.get('last_build_date')
        """
        Fetch RSS feed information from the given URL.

        Args:
            url (str): The URL of the RSS feed.

        Returns:
            Tuple[str, str, Optional[str]]: A tuple containing the title, description, and last build date.
        """
        return fetch_feed_info(url)
