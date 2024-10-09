from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, validates

Base = declarative_base()

class RSSFeed(Base):
    """Model for storing RSS feed information."""

    __tablename__ = 'rss_feed'

    id = Column(String(36), primary_key=True)
    url = Column(String(2048), unique=True, nullable=False)
    title = Column(String(255))
    description = Column(Text)
    last_build_date = Column(DateTime)
    etag = Column(String(255))
    last_modified = Column(String(255))
    last_checked = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                else:
                    value = value.astimezone(timezone.utc)
            setattr(self, key, value)

    @validates('last_build_date', 'last_checked')
    def validate_datetime(self, key, value):
        if value is not None:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    return value.replace(tzinfo=timezone.utc)
                return value.astimezone(timezone.utc)
        return value
