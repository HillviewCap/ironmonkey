from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID as PyUUID, uuid4
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

db = SQLAlchemy()
from sqlalchemy.dialects.postgresql import UUID


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
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    links = db.Column(db.JSON, nullable=True)
    feed_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("rss_feed.id"), nullable=False
    )
    feed = db.relationship("RSSFeed", backref=db.backref("parsed_contents", lazy=True))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    entities = db.relationship("Entity", back_populates="parsed_content")
    categories = db.relationship("Category", back_populates="parsed_content")

    @classmethod
    def get_by_id(cls, content_id):
        if isinstance(content_id, str):
            try:
                content_id = uuid.UUID(content_id)
            except ValueError:
                return None
        return cls.query.get(content_id)


class Entity(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(200), nullable=False)
    diffbot_uri = db.Column(db.String(500))
    confidence = db.Column(db.Float)
    salience = db.Column(db.Float)
    is_custom = db.Column(db.Boolean, default=False)
    parsed_content_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("parsed_content.id")
    )
    parsed_content = db.relationship("ParsedContent", back_populates="entities")
    uris = db.relationship("Uris", back_populates="entity")
    types = db.relationship("EntityType", back_populates="entity")
    mentions = db.relationship("Mention", back_populates="entity")
    locations = db.relationship("Location", back_populates="entity")


class Uris(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_id = db.Column(UUID(as_uuid=True), db.ForeignKey("entity.id"))
    uri = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(100))
    entity = db.relationship("Entity", back_populates="uris")


class Type(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(200), nullable=False)
    diffbot_uri = db.Column(db.String(500))
    dbpedia_uri = db.Column(db.String(500))
    entities = db.relationship("EntityType", back_populates="type")


class EntityType(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_id = db.Column(UUID(as_uuid=True), db.ForeignKey("entity.id"))
    type_id = db.Column(UUID(as_uuid=True), db.ForeignKey("type.id"))
    entity = db.relationship("Entity", back_populates="types")
    type = db.relationship("Type", back_populates="entities")


class Mention(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_id = db.Column(UUID(as_uuid=True), db.ForeignKey("entity.id"))
    text = db.Column(db.Text, nullable=False)
    begin_offset = db.Column(db.Integer)
    end_offset = db.Column(db.Integer)
    confidence = db.Column(db.Float)
    entity = db.relationship("Entity", back_populates="mentions")


class Location(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_id = db.Column(UUID(as_uuid=True), db.ForeignKey("entity.id"))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    precision = db.Column(db.Float)
    entity = db.relationship("Entity", back_populates="locations")


class Category(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = db.Column(db.String(100))
    id_category = db.Column(db.String(100))
    name = db.Column(db.String(200))
    path = db.Column(db.String(500))
    score = db.Column(db.Float)  # Add this field for Diffbot's category score
    parsed_content_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("parsed_content.id")
    )
    parsed_content = db.relationship("ParsedContent", back_populates="categories")


class Sentiment(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parsed_content_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("parsed_content.id")
    )
    parsed_content = db.relationship(
        "ParsedContent", backref=db.backref("sentiment", uselist=False)
    )
    type = db.Column(db.String(50))  # positive, negative, or neutral
    score = db.Column(db.Float)


class Topic(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parsed_content_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("parsed_content.id")
    )
    parsed_content = db.relationship(
        "ParsedContent", backref=db.backref("topics", lazy=True)
    )
    name = db.Column(db.String(200))
    score = db.Column(db.Float)
