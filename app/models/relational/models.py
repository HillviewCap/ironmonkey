from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID, uuid4
import hashlib
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from pydantic import BaseModel, Field
from app import db
from .user import User
from .search_params import SearchParams
from .rss_feed import RSSFeed
from .threat import Threat
from .parsed_content import ParsedContent

__all__ = ['User', 'SearchParams', 'RSSFeed', 'Threat', 'ParsedContent', 'Category', 'AwesomeThreatIntelBlog', 'SearchResult']

class SearchResult(BaseModel):
    id: PyUUID = Field(..., alias="id")
    title: str
    description: str
    source_type: str
    date: datetime
    url: str

    class Config:
        arbitrary_types_allowed = True


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
