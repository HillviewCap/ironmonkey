from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID as PyUUID, uuid4
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

    def get_id(self) -> Optional[str]:
        """Return the user ID as a string."""
        return str(self.id) if self.id else None

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
        title, description, last_build_date = 'Unknown Title', 'No description available', None
        
        try:
            feed = feedparser.parse(url)
            title = feed.feed.get('title', 'Unknown Title')
            description = feed.feed.get('description', 'No description available')
            last_build_date = feed.feed.get('updated')
        except Exception as e:
            logging_config.logger.error(f'Error parsing feed with feedparser: {str(e)}')

        if title == 'Unknown Title' or description == 'No description available':
            try:
                with httpx.Client() as client:
                    response = client.get(url)
                soup = BeautifulSoup(response.content, 'lxml')
                if title == 'Unknown Title':
                    title_tag = soup.find('title')
                    title = title_tag.text if title_tag else 'Unknown Title'
                if description == 'No description available':
                    description_tag = soup.find('meta', attrs={'name': 'description'})
                    description = description_tag['content'] if description_tag else 'No description available'
            except Exception as e:
                logging_config.logger.error(f'Error scraping feed with BeautifulSoup: {str(e)}')

        return title, description, last_build_date

class SearchParams(BaseModel):
    query: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None

class SearchResult(BaseModel):
    id: PyUUID = Field(..., alias='id')
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
