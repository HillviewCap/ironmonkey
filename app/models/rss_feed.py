from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RSSFeed(Base):
    """Model for storing RSS feed information."""

    __tablename__ = 'rss_feeds'

    id = Column(String(36), primary_key=True)
    url = Column(String(2048), unique=True, nullable=False)
    title = Column(String(255))
    description = Column(Text)
    last_build_date = Column(DateTime)
    etag = Column(String(255))
    last_modified = Column(String(255))
    last_checked = Column(DateTime, default=datetime.utcnow)
