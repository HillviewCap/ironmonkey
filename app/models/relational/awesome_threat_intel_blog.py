from __future__ import annotations

from datetime import datetime
from uuid import uuid4
import csv
import os
from flask import current_app
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, DateTime
from app import db
from app.models.relational.rss_feed import RSSFeed

class AwesomeThreatIntelBlog(db.Model):
    """
    Represents an Awesome Threat Intel Blog entry.
    """
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    blog = db.Column(String(255), nullable=False)
    blog_category = db.Column(String(100), nullable=False)
    type = db.Column(String(50), nullable=False)
    blog_link = db.Column(String(255), nullable=False, index=True)
    feed_link = db.Column(String(255), nullable=True)
    feed_type = db.Column(String(50), nullable=True)
    last_checked = db.Column(DateTime, nullable=True)

    rss_feeds = db.relationship('RSSFeed', back_populates='awesome_blog')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'blog': self.blog,
            'blog_category': self.blog_category,
            'type': self.type,
            'blog_link': self.blog_link,
            'feed_link': self.feed_link
        }

    def __repr__(self) -> str:
        return f"<AwesomeThreatIntelBlog {self.blog}>"

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
        else:
            new_entry = cls(
                blog=blog,
                blog_category=blog_category,
                type=type,
                blog_link=blog_link,
                feed_link=feed_link,
                feed_type=feed_type
            )
            db.session.add(new_entry)

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

    @classmethod
    def get_blog_categories(cls) -> list[str]:
        """
        Get all unique blog categories.

        Returns:
            A list of unique blog categories.
        """
        return [category[0] for category in db.session.query(cls.blog_category).distinct().all()]

    @classmethod
    def get_feed_types(cls) -> list[str]:
        """
        Get all unique feed types.

        Returns:
            A list of unique feed types.
        """
        return [feed_type[0] for feed_type in db.session.query(cls.feed_type).distinct().all()]

    @classmethod
    def filter_feeds(cls, blog_category: str | None = None, feed_type: str | None = None) -> list[AwesomeThreatIntelBlog]:
        """
        Filter feeds based on blog category and feed type.

        Args:
            blog_category: The blog category to filter by.
            feed_type: The feed type to filter by.

        Returns:
            A list of filtered AwesomeThreatIntelBlog entries.
        """
        query = cls.query
        if blog_category:
            query = query.filter_by(blog_category=blog_category)
        if feed_type:
            query = query.filter_by(feed_type=feed_type)
        return query.all()

    @classmethod
    def get_all_blogs(cls) -> list[AwesomeThreatIntelBlog]:
        """
        Get all Awesome Threat Intel Blogs.

        Returns:
            A list of all AwesomeThreatIntelBlog entries.
        """
        return cls.query.all()

    @classmethod
    def add_to_rss_feeds(cls, feed_ids: list[UUID]) -> int:
        """
        Add selected feeds to the RSSFeed table.

        Args:
            feed_ids: A list of AwesomeThreatIntelBlog IDs to add to RSSFeed.

        Returns:
            The number of feeds added to RSSFeed.
        """
        feeds_to_add = cls.query.filter(cls.id.in_(feed_ids)).all()
        added_count = 0
        for feed in feeds_to_add:
            existing_rss_feed = RSSFeed.query.filter_by(url=feed.feed_link).first()
            if not existing_rss_feed:
                new_rss_feed = RSSFeed(
                    name=feed.blog,
                    url=feed.feed_link,
                    awesome_blog_id=feed.id
                )
                db.session.add(new_rss_feed)
                added_count += 1
        db.session.commit()
        return added_count
