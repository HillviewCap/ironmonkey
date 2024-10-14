from app.models.relational.parsed_content import ParsedContent
from app.models.relational.rss_feed import RSSFeed
from app.models.relational.content_tag import ContentTag
from app.extensions import db
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

class ParsedContentService:
    @staticmethod
    def get_content_by_id(content_id: str) -> Optional[Dict[str, Any]]:
        content = ParsedContent.get_by_id(content_id)
        if content:
            return {
                'rss_feed_title': content.feed.title if content.feed else None,
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
    def get_latest_parsed_content(
        limit: int = 20,
        category: Optional[str] = None,
        date: Optional[datetime.date] = None
    ) -> Dict[str, Any]:
        """
        Retrieve the latest parsed content entries and content stats.
        
        :param limit: The maximum number of entries to retrieve
        :param category: Optional category to filter the content
        :param date: Optional date to filter the content
        :return: A dictionary containing parsed content data and content stats
        """
        query = ParsedContent.query.options(joinedload(ParsedContent.feed)).order_by(desc(ParsedContent.pub_date))
        
        if category:
            query = query.filter(ParsedContent.category.has(name=category))
        
        if date:
            date_start = datetime.combine(date, datetime.min.time())
            date_end = datetime.combine(date, datetime.max.time())
            query = query.filter(ParsedContent.pub_date.between(date_start, date_end))
        
        latest_content = query.limit(limit).all()
        content_stats = ParsedContentService.get_content_stats(date)
        return {
            'content': [content.to_dict() for content in latest_content],
            'stats': content_stats
        }

    @staticmethod
    def get_content_stats(date: Optional[datetime.date] = None) -> Dict[str, Any]:
        """
        Retrieve statistics about the parsed content for a specific date.

        :param date: The date for which to retrieve statistics. Defaults to today if None.
        :return: A dictionary containing various statistics including actor occurrences.
        """
        if date is None:
            date = datetime.utcnow().date()
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())

        # Number of articles published on the specified date
        articles_today = ParsedContent.query.filter(
            ParsedContent.pub_date.between(date_start, date_end)
        ).count()

        # Top 3 sites with article count for the specified date
        top_sites = db.session.query(
            RSSFeed.title,
            func.count(ParsedContent.id).label('article_count')
        ).join(RSSFeed, ParsedContent.feed_id == RSSFeed.id)\
         .filter(ParsedContent.pub_date.between(date_start, date_end))\
         .group_by(RSSFeed.title)\
         .order_by(func.count(ParsedContent.id).desc())\
         .limit(3)\
         .all()

        # Top 3 authors with article count for the specified date
        top_authors = db.session.query(
            ParsedContent.creator,
            func.count(ParsedContent.id).label('article_count')
        ).filter(ParsedContent.pub_date.between(date_start, date_end))\
         .group_by(ParsedContent.creator)\
         .order_by(func.count(ParsedContent.id).desc())\
         .limit(3)\
         .all()

        # Actor occurrences for the specified date
        actor_occurrences = db.session.query(
            ContentTag.entity_name.label('entity_name'),
            func.count(ContentTag.id).label('occurrence_count')
        ).join(ParsedContent, ContentTag.parsed_content_id == ParsedContent.id)\
         .filter(
             ContentTag.entity_type == 'actor',
             ParsedContent.pub_date.between(date_start, date_end)
         )\
         .group_by(ContentTag.entity_name)\
         .order_by(func.count(ContentTag.id).desc())\
         .all()

        return {
            'articles_today': articles_today,
            'top_sites': [(site[0], site[1]) for site in top_sites],
            'top_authors': [(author[0], author[1]) for author in top_authors],
            'actor_occurrences': [
                {'entity_name': actor.entity_name, 'occurrence_count': actor.occurrence_count}
                for actor in actor_occurrences
            ]
        }
class ParsedContentService:
    def calculate_stats(self, content):
        # Implement your statistics calculation here
        articles_today = len(content)
        
        # Example implementation for top sites and authors
        site_counts = {}
        author_counts = {}
        for item in content:
            site = item.feed.title if item.feed else 'Unknown'
            site_counts[site] = site_counts.get(site, 0) + 1
            
            author = item.creator or 'Unknown'
            author_counts[author] = author_counts.get(author, 0) + 1
        
        top_sites = sorted(site_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'articles_today': articles_today,
            'top_sites': top_sites,
            'top_authors': top_authors
        }
