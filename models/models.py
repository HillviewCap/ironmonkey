from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional, Tuple
from uuid import UUID as PyUUID, uuid4
import uuid
import uuid
from pydantic import BaseModel, Field
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash
import xml.etree.ElementTree as ET
import httpx
import feedparser
from bs4 import BeautifulSoup
import logging_config
from sqlalchemy.dialects.postgresql import UUID

db = SQLAlchemy()

__all__ = ['db', 'User', 'SearchParams', 'RSSFeed', 'Threat', 'ParsedContent', 'Category']

class SearchParams:
    def __init__(
        self,
        query: str = "",
        start_date: date = None,
        end_date: date = None,
        source_types: List[str] = None,
        keywords: List[str] = None,
    ):
        self.query = query
        self.start_date = start_date
        self.end_date = end_date
        self.source_types = source_types or []
        self.keywords = keywords or []


class User(UserMixin, db.Model):
    """User model for authentication and authorization."""

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def get_id(self) -> str:
        """Return the user ID as a string."""
        return str(self.id)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password, password)


class RSSFeed(db.Model):
    """Model for storing RSS feed information."""

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    last_build_date = db.Column(db.String(100), nullable=True)

    @staticmethod
    def fetch_feed_info(url: str) -> Tuple[str, str, Optional[str]]:
        """
        Fetch RSS feed information from the given URL.

        Args:
            url (str): The URL of the RSS feed.

        Returns:
            Tuple[str, str, Optional[str]]: A tuple containing the title, description, and last build date.
        """
        title, description, last_build_date = (
            "Unknown Title",
            "No description available",
            None,
        )

        try:
            feed = feedparser.parse(url)
            title = feed.feed.get("title", "Unknown Title")
            description = feed.feed.get("description", "No description available")
            last_build_date = feed.feed.get("updated")
        except Exception as e:
            logging_config.logger.error(f"Error parsing feed with feedparser: {str(e)}")

        if title == "Unknown Title" or description == "No description available":
            try:
                with httpx.Client() as client:
                    response = client.get(url)
                soup = BeautifulSoup(response.content, "lxml")
                if title == "Unknown Title":
                    title_tag = soup.find("title")
                    title = title_tag.text if title_tag else "Unknown Title"
                if description == "No description available":
                    description_tag = soup.find("meta", attrs={"name": "description"})
                    description = (
                        description_tag["content"]
                        if description_tag
                        else "No description available"
                    )
            except Exception as e:
                logging_config.logger.error(
                    f"Error scraping feed with BeautifulSoup: {str(e)}"
                )

        return title, description, last_build_date


class SearchParams(BaseModel):
    query: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class SearchResult(BaseModel):
    id: PyUUID = Field(..., alias="id")
    title: str
    description: str
    source_type: str
    date: datetime
    url: str

    class Config:
        arbitrary_types_allowed = True


class Threat(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    source_type = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    url = db.Column(db.String(255), nullable=False)


class ParsedContent(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    @classmethod
    def deduplicate(cls):
        """
        Deduplicates the parsed articles based on the URL.
        Keeps the earliest entry for each URL and deletes the rest.
        Returns the number of deleted entries.
        """
        subquery = db.session.query(
            cls.url,
            db.func.min(cls.created_at).label('earliest_date')
        ).group_by(cls.url).subquery()

        to_delete = cls.query.join(
            subquery,
            cls.url == subquery.c.url
        ).filter(cls.created_at > subquery.c.earliest_date)

        deleted_count = to_delete.delete(synchronize_session='fetch')
        db.session.commit()

        return deleted_count
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)  # This will store the Jina summary from Ollama
    summary = db.Column(db.Text, nullable=True)  # This will store the generated summary
    feed_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("rss_feed.id"), nullable=False
    )
    feed = db.relationship("RSSFeed", backref=db.backref("parsed_contents", lazy=True))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pub_date = db.Column(db.String(100), nullable=True)
    creator = db.Column(db.String(255), nullable=True)

    @classmethod
    def get_by_id(cls, content_id):
        if isinstance(content_id, str):
            try:
                content_id = uuid.UUID(content_id)
            except ValueError:
                return None
        return cls.query.filter(cls.id == content_id).first()

    @classmethod
    def get_document_by_id(cls, document_id):
        if isinstance(document_id, str):
            try:
                document_id = uuid.UUID(document_id)
            except ValueError:
                return None
        return cls.query.filter(cls.id == document_id).first()


class Category(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(200), nullable=False)
    scheme = db.Column(db.String(200), nullable=True)  # For feedparser category scheme
    term = db.Column(db.String(200), nullable=True)  # For feedparser category term
    parsed_content_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("parsed_content.id")
    )
    parsed_content = db.relationship("ParsedContent", backref=db.backref("categories", lazy=True))

    @classmethod
    def create_from_feedparser(cls, category, parsed_content_id):
        if isinstance(category, str):
            return cls(name=category, parsed_content_id=parsed_content_id)
        elif isinstance(category, dict):
            return cls(
                name=category.get('term', ''),
                scheme=category.get('scheme'),
                term=category.get('term'),
                parsed_content_id=parsed_content_id
            )
        else:
            raise ValueError("Unsupported category format")
