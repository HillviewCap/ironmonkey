from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID as PyUUID, uuid4
from pydantic import BaseModel, Field
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash
import xml.etree.ElementTree as ET
import httpx
from bs4 import BeautifulSoup
import requests

db = SQLAlchemy()
from sqlalchemy.dialects.postgresql import UUID

class User(UserMixin, db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def get_id(self):
        return str(self.id) if self.id else None

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

class RSSFeed(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    last_build_date = db.Column(db.String(100), nullable=True)

    @staticmethod
    def fetch_feed_info(url: str) -> tuple[str, str, str]:
        try:
            feed = feedparser.parse(url)
            title = feed.feed.title if 'title' in feed.feed else 'Unknown Title'
            description = feed.feed.description if 'description' in feed.feed else 'No description available'
            last_build_date = feed.feed.updated if 'updated' in feed.feed else None
        except Exception as e:
            logging_config.logger.error(f'Error parsing feed with feedparser: {str(e)}')
            title, description, last_build_date = 'Unknown Title', 'No description available', None

        if title == 'Unknown Title' or description == 'No description available':
            try:
                response = requests.get(url)
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
