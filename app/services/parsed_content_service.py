"""
This module provides services for managing parsed content in the application.

It includes functionality for creating, retrieving, updating, and deleting
parsed content items, as well as handling pagination and filtering.
"""

from __future__ import annotations

import uuid
from typing import List, Dict, Tuple, Union
from uuid import UUID
from sqlalchemy import desc
from flask import current_app

from app.models.relational import ParsedContent, Category
from app.utils.content_sanitizer import sanitize_html_content
from app.utils.logging_config import setup_logger
from app.extensions import db

logger = setup_logger('parsed_content_service', 'parsed_content_service.log')

class ParsedContentService:
    """
    A service class for managing parsed content operations.

    This class provides static methods for various operations related to
    parsed content, including retrieval, creation, updating, and deletion.
    """
    @staticmethod
    def get_all_contents(search_query: str = '', feed_id: Union[str, UUID] = None, order_by: str = 'pub_date', order: str = 'desc') -> List[ParsedContent]:
        """
        Retrieve all parsed content, optionally filtered by a search query and feed_id, and ordered.

        Args:
            search_query (str): Optional search query to filter the content.
            feed_id (Union[str, UUID]): Optional feed_id to filter the content.
            order_by (str): Field to order by. Defaults to 'pub_date'.
            order (str): Order direction, 'asc' or 'desc'. Defaults to 'desc'.

        Returns:
            List[ParsedContent]: A list containing all parsed content objects.
        """
        query = ParsedContent.query

        if feed_id:
            if isinstance(feed_id, str):
                try:
                    feed_id = UUID(feed_id)
                except ValueError:
                    # Handle invalid UUID string
                    return []
            query = query.filter(ParsedContent.feed_id == feed_id)

        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                (ParsedContent.title.ilike(search)) |
                (ParsedContent.description.ilike(search)) |
                (ParsedContent.content.ilike(search))
            )

        # Apply ordering
        if order == 'desc':
            query = query.order_by(desc(getattr(ParsedContent, order_by)))
        else:
            query = query.order_by(getattr(ParsedContent, order_by))

        return query.all()

    @staticmethod
    def get_total_count(search_query: str = '') -> int:
        """
        Get the total count of parsed content, optionally filtered by a search query.

        Args:
            search_query (str): Optional search query to filter the content.

        Returns:
            int: The total count of parsed content items.
        """
        query = ParsedContent.query

        if search_query:
            search = f"%{search_query}%"
            query = query.filter(
                (ParsedContent.title.ilike(search)) |
                (ParsedContent.description.ilike(search)) |
                (ParsedContent.content.ilike(search))
            )

        return query.count()

    @staticmethod
    def get_content_by_id(content_id: uuid.UUID) -> ParsedContent:
        """
        Retrieve a parsed content item by its ID.

        Args:
            content_id (uuid.UUID): The unique identifier of the parsed content.

        Returns:
            ParsedContent: The parsed content object with the given ID.
        """
        return ParsedContent.query.get(content_id)

    @staticmethod
    def create_parsed_content(content_data: Dict[str, any]) -> ParsedContent:
        """
        Create a new parsed content item.

        Args:
            content_data (Dict[str, any]): A dictionary containing the parsed content details.

        Returns:
            ParsedContent: The newly created parsed content object.
        """
        content = ParsedContent(
            id=uuid.uuid4(),
            title=content_data['title'],
            url=content_data['url'],
            content=sanitize_html_content(content_data['content']),
            description=content_data.get('description'),
            pub_date=content_data.get('pub_date'),
            creator=content_data.get('creator'),
            feed_id=content_data.get('feed_id')
        )

        # Handle categories
        categories = content_data.get('categories', [])
        for category_data in categories:
            category = Category.create_from_feedparser(category_data)
            content.categories.append(category)

        db.session.add(content)
        db.session.commit()
        logger.info(f"Created new parsed content: {content.title} with {len(content.categories)} categories")
        return content

    @staticmethod
    def update_parsed_content(content_id: uuid.UUID, content_data: Dict[str, any]) -> ParsedContent:
        """
        Update an existing parsed content item.

        Args:
            content_id (uuid.UUID): The unique identifier of the parsed content.
            content_data (Dict[str, any]): A dictionary containing the updated content details.

        Returns:
            ParsedContent: The updated parsed content object.
        """
        content = ParsedContent.query.get(content_id)
        if not content:
            raise ValueError(f"Parsed content with ID {content_id} not found.")

        content.title = content_data.get('title', content.title)
        content.url = content_data.get('url', content.url)
        content.content = sanitize_html_content(content_data.get('content', content.content))
        content.description = content_data.get('description', content.description)
        content.pub_date = content_data.get('pub_date', content.pub_date)
        content.creator = content_data.get('creator', content.creator)

        db.session.commit()
        logger.info(f"Updated parsed content: {content.title}")
        return content

    @staticmethod
    def delete_parsed_content(content_id: uuid.UUID) -> None:
        """
        Delete a parsed content item.

        Args:
            content_id (uuid.UUID): The unique identifier of the parsed content.

        Raises:
            ValueError: If the parsed content with the given ID is not found.
        """
        content = ParsedContent.query.get(content_id)
        if not content:
            raise ValueError(f"Parsed content with ID {content_id} not found.")

        db.session.delete(content)
        db.session.commit()
        logger.info(f"Deleted parsed content: {content.title}")

    @staticmethod
    def delete_parsed_content_by_feed_id(feed_id: uuid.UUID) -> None:
        """
        Delete all parsed content associated with a specific RSS feed.

        Args:
            feed_id (uuid.UUID): The unique identifier of the RSS feed.
        """
        deleted = ParsedContent.query.filter_by(feed_id=feed_id).delete()
        db.session.commit()
        logger.info(f"Deleted {deleted} parsed content items associated with feed ID {feed_id}")
