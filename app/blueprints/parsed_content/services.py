from app.models.relational.parsed_content import ParsedContent
from typing import List, Dict, Any

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
