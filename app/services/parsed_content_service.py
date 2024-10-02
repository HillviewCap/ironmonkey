from app.models.relational.parsed_content import ParsedContent, parsed_content_categories
from app.extensions import db
from sqlalchemy import delete
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
        Delete all parsed content and associated category data for a specific RSS feed.

        :param feed_id: The UUID of the RSS feed
        """
        with db.session.begin():
            # Get all ParsedContent IDs associated with the feed
            parsed_content_ids = db.session.query(ParsedContent.id).filter_by(feed_id=feed_id).all()
            parsed_content_ids = [id for (id,) in parsed_content_ids]

            if parsed_content_ids:
                # Delete associated entries in the parsed_content_categories table
                db.session.execute(delete(parsed_content_categories).where(
                    parsed_content_categories.c.parsed_content_id.in_(parsed_content_ids)
                ))

            # Delete ParsedContent entries
            ParsedContent.query.filter_by(feed_id=feed_id).delete(synchronize_session='fetch')
