from __future__ import annotations
from datetime import datetime
from uuid import uuid4
import hashlib
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Table
from app.extensions import db
from flask import flash
from .category import Category
from typing import List, Dict, Any, Optional, Union

parsed_content_categories = Table(
    'parsed_content_categories',
    db.Model.metadata,
    Column('parsed_content_id', UUID(as_uuid=True), ForeignKey('parsed_content.id')),
    Column('category_id', UUID(as_uuid=True), ForeignKey('category.id'))
)

class ParsedContent(db.Model):
    """Model representing parsed content from RSS feeds."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Jina summary from Ollama
    summary = Column(Text, nullable=True)  # Generated summary
    feed_id = Column(UUID(as_uuid=True), ForeignKey("rss_feed.id"), nullable=False)
    feed = db.relationship("RSSFeed", back_populates="parsed_items")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    pub_date = Column(String(100), nullable=True)
    creator = Column(String(255), nullable=True)
    categories = db.relationship('Category', secondary=parsed_content_categories, backref=db.backref('parsed_contents', lazy='dynamic'))
    art_hash = Column(String(64), nullable=True)

    __table_args__ = (db.UniqueConstraint('url', 'feed_id', name='uix_url_feed'),)

    @classmethod
    def deduplicate(cls) -> int:
        """
        Deduplicate parsed articles based on URL.

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

        if deleted_count > 0:
            flash(f"Deduplication complete. {deleted_count} duplicate items removed.", "success")
        else:
            flash("No duplicate items found during deduplication.", "info")

        return deleted_count

    @classmethod
    def get_by_id(cls, content_id: Union[str, UUID]) -> Optional[ParsedContent]:
        """Retrieve a ParsedContent instance by its ID."""
        try:
            if isinstance(content_id, UUID):
                content_id = str(content_id)
            elif isinstance(content_id, str):
                # Remove hyphens if present
                content_id = content_id.replace('-', '')
                # Validate if it's a valid UUID string
                UUID(content_id)
            else:
                raise ValueError("Invalid content_id type")
            return cls.query.filter(cls.id == content_id).first()
        except ValueError:
            return None

    @classmethod
    def get_document_by_id(cls, document_id: str) -> Optional[ParsedContent]:
        """Alias for get_by_id method."""
        return cls.get_by_id(document_id)

    @classmethod
    def hash_existing_articles(cls) -> int:
        """Hash existing articles and return the count of hashed articles."""
        articles = cls.query.all()
        hashed_count = 0
        for article in articles:
            article.art_hash = hashlib.sha256(f"{article.url}{article.title}".encode()).hexdigest()
            hashed_count += 1
        db.session.commit()
        return hashed_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert the ParsedContent instance to a dictionary."""
        return {
            'id': str(self.id),
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'content': self.content,
            'summary': self.summary,
            'feed_id': str(self.feed_id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'pub_date': self.pub_date,
            'creator': self.creator,
            'art_hash': self.art_hash
        }
