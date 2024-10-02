from app.models.relational.parsed_content import ParsedContent
from app.extensions import db
from typing import List, Dict, Any
import uuid

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
    def delete_parsed_content_by_feed_id(feed_id: uuid.UUID) -> None:
        """
        Delete all parsed content associated with a specific RSS feed.

        :param feed_id: The UUID of the RSS feed
        """
        ParsedContent.query.filter_by(rss_feed_id=feed_id).delete()
        db.session.commit()
