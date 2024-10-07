from __future__ import annotations
from uuid import uuid4
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, JSON
from app.extensions import db
from datetime import datetime
from typing import Optional

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""

    __tablename__ = 'user'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    theme = Column(String(20), nullable=False, default='light')
    language = Column(String(10), nullable=False, default='en')
    notification_preferences = Column(JSON, nullable=False, default={})
    custom_categories = Column(JSON, nullable=False, default=[])

    # Relationships
    rss_feeds = db.relationship('RSSFeed', back_populates='user', cascade='all, delete-orphan')
    parsed_contents = db.relationship('ParsedContent', back_populates='user', cascade='all, delete-orphan')

    def get_id(self) -> str:
        """Return the user ID as a string."""
        return str(self.id)

    def set_password(self, password: str) -> None:
        """Set the user's password."""
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password, password)

    @classmethod
    def get(cls, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        return cls.query.get(user_id)

    def update_preferences(self, **kwargs):
        """Update user preferences."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()

    def to_dict(self) -> dict:
        """Convert the User instance to a dictionary."""
        return {
            'id': str(self.id),
            'email': self.email,
            'theme': self.theme,
            'language': self.language,
            'notification_preferences': self.notification_preferences,
            'custom_categories': self.custom_categories,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
