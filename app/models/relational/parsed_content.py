from datetime import datetime
from uuid import uuid4
import hashlib
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Table
from app import db
from flask import flash

parsed_content_categories = Table('parsed_content_categories', db.Model.metadata,
    Column('parsed_content_id', UUID(as_uuid=True), ForeignKey('parsed_content.id')),
    Column('category_id', UUID(as_uuid=True), ForeignKey('category.id'))
)

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
    categories = db.relationship('Category', secondary=parsed_content_categories, backref=db.backref('parsed_contents', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('url', 'feed_id', name='uix_url_feed'),)

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

        if deleted_count > 0:
            flash(f"Deduplication complete. {deleted_count} duplicate items removed.", "success")
        else:
            flash("No duplicate items found during deduplication.", "info")

        return deleted_count

    @classmethod
    def get_by_id(cls, content_id):
        try: 
            content_id = UUID(content_id) if isinstance(content_id, str) else content_id
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

    def to_dict(self):
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
