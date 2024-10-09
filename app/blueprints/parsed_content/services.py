from app.models.relational.parsed_content import ParsedContent
from app.models.relational.rss_feed import RSSFeed
from app.extensions import db
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, desc

class ParsedContentService:
    @staticmethod
    def get_content_by_id(content_id: str) -> Optional[Dict[str, Any]]:
        content = ParsedContent.get_by_id(content_id)
        if content:
            return {
                'rss_feed_title': content.rss_feed.title,
                'title': content.title,
                'creator': content.creator,
                'pub_date': content.pub_date,
                'category': content.category.name if content.category else None,
                'url': content.url,
                'description': content.description,
                'summary': content.summary
            }
        return None

    @staticmethod
    def get_latest_parsed_content(limit: int = 20, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve the latest parsed content entries and content stats.
        
        :param limit: The maximum number of entries to retrieve
        :param category: Optional category to filter the content
        :return: A dictionary containing parsed content data and content stats
        """
        query = ParsedContent.query.order_by(desc(ParsedContent.pub_date))
        
        if category:
            query = query.filter(ParsedContent.category.has(name=category))
        
        latest_content = query.limit(limit).all()
        content_stats = ParsedContentService.get_content_stats()
        return {
            'content': [content.to_dict() for content in latest_content],
            'stats': content_stats
        }

    @staticmethod
    def get_content_stats() -> Dict[str, Any]:
        """
        Retrieve statistics about the parsed content.

        :return: A dictionary containing various statistics
        """
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        # Number of articles published today
        articles_today = ParsedContent.query.filter(
            ParsedContent.pub_date.between(today_start, today_end)
        ).count()

        # Top 3 sites with article count for today
        top_sites = db.session.query(
            RSSFeed.title,
            func.count(ParsedContent.id).label('article_count')
        ).join(RSSFeed, ParsedContent.feed_id == RSSFeed.id)\
         .filter(ParsedContent.pub_date.between(today_start, today_end))\
         .group_by(RSSFeed.title)\
         .order_by(func.count(ParsedContent.id).desc())\
         .limit(3)\
         .all()

        # Top 3 authors with article count for today
        top_authors = db.session.query(
            ParsedContent.creator,
            func.count(ParsedContent.id).label('article_count')
        ).filter(ParsedContent.pub_date.between(today_start, today_end))\
         .group_by(ParsedContent.creator)\
         .order_by(func.count(ParsedContent.id).desc())\
         .limit(3)\
         .all()

        return {
            'articles_today': articles_today,
            'top_sites': top_sites,
            'top_authors': top_authors
        }
