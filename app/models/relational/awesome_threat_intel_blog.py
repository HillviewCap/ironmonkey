from __future__ import annotations

from datetime import datetime
from uuid import uuid4
import csv
import os
from flask import current_app
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime
from app import db
from app.models.relational.rss_feed import RSSFeed

class AwesomeThreatIntelBlog(db.Model):
    """
    Represents an Awesome Threat Intel Blog entry.
    """
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
    def link_with_rss_feed(cls) -> None:
        """
        Link AwesomeThreatIntelBlog entries with corresponding RSSFeed entries.
        """
        awesome_blogs = cls.query.all()
        for blog in awesome_blogs:
            rss_feed = RSSFeed.query.filter_by(url=blog.feed_link).first()
            if rss_feed:
                rss_feed.awesome_blog = blog
        db.session.commit()

    @classmethod
    def update_or_create(cls, blog: str, blog_category: str, type: str, blog_link: str, feed_link: str, feed_type: str) -> None:
        """
        Update an existing AwesomeThreatIntelBlog entry or create a new one.

        Args:
            blog: The blog name.
            blog_category: The blog category.
            type: The blog type.
            blog_link: The blog link.
            feed_link: The feed link.
            feed_type: The feed type.
        """
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
    def import_from_csv(cls, csv_file_path: str) -> str:
        """
        Import AwesomeThreatIntelBlog entries from a CSV file.

        Args:
            csv_file_path: The path to the CSV file.

        Returns:
            A message indicating the import status.
        """
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
