from app.models.relational.parsed_content import ParsedContent
from app.models.relational.rss_feed import RSSFeed
from app.extensions import db
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func

class ParsedContentService:
    @staticmethod
    def get_latest_parsed_content(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve the latest parsed content entries.
        
        :param limit: The maximum number of entries to retrieve
        :return: A list of dictionaries containing parsed content data
        """
        latest_content = ParsedContent.query.order_by(ParsedContent.created_at.desc()).limit(limit).all()
        return [content.to_dict() for content in latest_content]

    @staticmethod
    def get_content_stats() -> Dict[str, Any]:
        """
        Retrieve statistics about the parsed content.

        :return: A dictionary containing various statistics
        """
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        # Number of articles today
        articles_today = ParsedContent.query.filter(func.date(ParsedContent.created_at) == today).count()

        # Top 3 sites with article count for today
        top_sites = db.session.query(
            RSSFeed.feed_name,
            func.count(ParsedContent.id).label('article_count')
        ).join(RSSFeed, ParsedContent.feed_id == RSSFeed.id)\
         .filter(func.date(ParsedContent.created_at) == today)\
         .group_by(RSSFeed.feed_name)\
         .order_by(func.count(ParsedContent.id).desc())\
         .limit(3)\
         .all()

        # Top 3 authors with article count for today
        top_authors = db.session.query(
            ParsedContent.creator,
            func.count(ParsedContent.id).label('article_count')
        ).filter(func.date(ParsedContent.created_at) == today)\
         .group_by(ParsedContent.creator)\
         .order_by(func.count(ParsedContent.id).desc())\
         .limit(3)\
         .all()

        return {
            'articles_today': articles_today,
            'top_sites': top_sites,
            'top_authors': top_authors
        }
