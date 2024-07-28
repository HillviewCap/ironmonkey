from __future__ import annotations

from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from app import db

class Category(db.Model):
    """Represents a category for parsed content."""

    __tablename__ = 'category'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(255), nullable=False, unique=True)
    scheme = db.Column(db.String(200), nullable=True)  # For feedparser category scheme
    term = db.Column(db.String(200), nullable=True)  # For feedparser category term

    def __repr__(self) -> str:
        return f"<Category {self.name}>"

    @classmethod
    def create_from_feedparser(cls, category: str | dict) -> 'Category':
        """
        Create a Category instance from feedparser data.

        Args:
            category: The category data from feedparser.

        Returns:
            A new Category instance.

        Raises:
            ValueError: If the category format is unsupported.
        """
        if isinstance(category, str):
            return cls(name=category)
        elif isinstance(category, dict):
            return cls(
                name=category.get('term', ''),
                scheme=category.get('scheme'),
                term=category.get('term')
            )
        else:
            raise ValueError("Unsupported category format")
