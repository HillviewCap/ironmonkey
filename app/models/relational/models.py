from __future__ import annotations

from datetime import datetime
from typing import Tuple, Optional
from uuid import UUID as PyUUID, uuid4
import hashlib
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from pydantic import BaseModel, Field
from app.utils.http_client import fetch_feed_info
from app import db
from .user import User
from .search_params import SearchParams

__all__ = ['User', 'SearchParams', 'RSSFeed', 'Threat', 'ParsedContent', 'Category', 'AwesomeThreatIntelBlog', 'SearchResult']

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
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source_type = Column(String(100), nullable=False)
    date = Column(DateTime, nullable=False)
    url = Column(String(255), nullable=False)


class ParsedContent(db.Model):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # This will store the Jina summary from Ollama
    summary = Column(Text, nullable=True)  # This will store the generated summary
    feed_id = Column(UUID(as_uuid=True), ForeignKey("rss_feed.id"), nullable=False)
    feed = db.relationship("RSSFeed", back_populates="parsed_items")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    pub_date = Column(String(100), nullable=True)
    creator = Column(String(255), nullable=True)
    art_hash = Column(String(64), unique=True, index=True)

    @classmethod
    def deduplicate(cls):
        """
        Deduplicates the parsed articles based on the URL.
        Keeps the earliest entry for each URL and deletes the rest.
        Returns the number of deleted entries.
        """
        url_earliest_dates = db.session.query(
            cls.url,
            db.func.min(cls.created_at).label('earliest_date')
        ).group_by(cls.url).all()

        deleted_count = 0

        for url, earliest_date in url_earliest_dates:
            duplicates = cls.query.filter(
                cls.url == url,
                cls.created_at > earliest_date
            ).all()

            for duplicate in duplicates:
                db.session.delete(duplicate)
                deleted_count += 1

        db.session.commit()

        from flask import flash
        if deleted_count > 0:
            flash(f"Deduplication complete. {deleted_count} duplicate items removed.", "success")
        else:
            flash("No duplicate items found during deduplication.", "info")

        return deleted_count

    @classmethod
    def get_by_id(cls, content_id):
        try: 
            content_id = PyUUID(content_id) if isinstance(content_id, str) else content_id
            return cls.query.filter(cls.id == content_id).first()
        except ValueError:
            return None

    @classmethod
    def get_document_by_id(cls, document_id):
        return cls.get_by_id(document_id)

    @classmethod
    def hash_existing_articles(cls):
        articles = cls.query.all()
        hashed_count = 0
        for article in articles:
            article.art_hash = hashlib.sha256(f"{article.url}{article.title}".encode()).hexdigest()
            hashed_count += 1
        db.session.commit()
        return hashed_count


class Category(db.Model):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    scheme = Column(String(200), nullable=True)  # For feedparser category scheme
    term = Column(String(200), nullable=True)  # For feedparser category term
    parsed_content_id = Column(UUID(as_uuid=True), ForeignKey("parsed_content.id"))
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

class AwesomeThreatIntelBlog(db.Model):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    blog = Column(String(255), nullable=False)
    blog_category = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    blog_link = Column(String(255), nullable=False)
    feed_link = Column(String(255), nullable=True)
    feed_type = Column(String(50), nullable=True)
    last_checked = Column(DateTime, nullable=True)

    rss_feeds = db.relationship('RSSFeed', back_populates='awesome_blog')

    @classmethod
    def link_with_rss_feed(cls):
        awesome_blogs = cls.query.all()
        for blog in awesome_blogs:
            rss_feed = RSSFeed.query.filter_by(url=blog.feed_link).first()
            if rss_feed:
                rss_feed.awesome_blog = blog
        db.session.commit()

    @classmethod
    def update_or_create(cls, blog, blog_category, type, blog_link, feed_link, feed_type):
        existing = cls.query.filter_by(blog_link=blog_link).first()
        if existing:
            existing.blog = blog
            existing.blog_category = blog_category
            existing.type = type
            existing.feed_link = feed_link
            existing.feed_type = feed_type
            existing.last_checked = datetime.utcnow()
        else:
            new_entry = cls(
                blog=blog,
                blog_category=blog_category,
                type=type,
                blog_link=blog_link,
                feed_link=feed_link,
                feed_type=feed_type,
                last_checked=datetime.utcnow()
            )
            db.session.add(new_entry)
        db.session.commit()

    @classmethod
    def import_from_csv(cls, csv_file_path):
        import csv
        import os
        from flask import current_app

        full_path = os.path.join(current_app.root_path, 'static', 'Awesome Threat Intel Blogs - MASTER.csv')

        with open(full_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                cls.update_or_create(
                    blog=row['Blog'],
                    blog_category=row['Blog Category'],
                    type=row['Type'],
                    blog_link=row['Blog Link'],
                    feed_link=row['Feed Link'],
                    feed_type=row['Feed Type']
                )
        
        return "CSV import completed successfully."
