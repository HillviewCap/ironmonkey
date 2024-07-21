from __future__ import annotations

from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, ForeignKey
from app import db

class Category(db.Model):
    """
    Represents a category for parsed content.
    """
    __tablename__ = 'category'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    scheme = Column(String(200), nullable=True)  # For feedparser category scheme
    term = Column(String(200), nullable=True)  # For feedparser category term
    parsed_content_id = Column(UUID(as_uuid=True), ForeignKey("parsed_content.id"))
    parsed_content = db.relationship("ParsedContent", backref=db.backref("categories", lazy=True))

    def __repr__(self):
        return f"<Category {self.name}>"

    @classmethod
    def create_from_feedparser(cls, category: str | dict, parsed_content_id: UUID) -> Category:
        """
        Create a Category instance from feedparser data.

        Args:
            category: The category data from feedparser.
            parsed_content_id: The ID of the associated ParsedContent.

        Returns:
            A new Category instance.

        Raises:
            ValueError: If the category format is unsupported.
        """
        if isinstance(category, str):
            return cls(name=category, parsed_content_id=parsed_content_id)
        elif isinstance(category, dict):
            return cls(
                name=category.get('term', ''),
                scheme=category.get('scheme'),
                term=category.get('term'),
                parsed_content_id=parsed_content_id
            )
        else:
            raise ValueError("Unsupported category format")
