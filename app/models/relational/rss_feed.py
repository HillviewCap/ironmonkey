from uuid import UUID as PyUUID, uuid4
from typing import Tuple, Optional
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app import db
from app.utils.http_client import fetch_feed_info

class RSSFeed(db.Model):
    """Model for storing RSS feed information."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    last_build_date = Column(String(100), nullable=True)
    
    # Relationship with ParsedContent
    parsed_items = db.relationship('ParsedContent', back_populates='feed', cascade='all, delete-orphan')
    
    # Relationship with AwesomeThreatIntelBlog
    awesome_blog_id = Column(UUID(as_uuid=True), ForeignKey('awesome_threat_intel_blog.id'), nullable=True)
    awesome_blog = db.relationship('AwesomeThreatIntelBlog', back_populates='rss_feeds')

    def __init__(self, **kwargs):
        super(RSSFeed, self).__init__(**kwargs)
        if not self.id:
            self.id = uuid4()

    @staticmethod
    def fetch_feed_info(url: str) -> Tuple[str, str, Optional[str]]:
        """
        Fetch RSS feed information from the given URL.

        Args:
            url (str): The URL of the RSS feed.

        Returns:
            Tuple[str, str, Optional[str]]: A tuple containing the title, description, and last build date.
        """
        return fetch_feed_info(url)
