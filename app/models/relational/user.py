from __future__ import annotations
from uuid import uuid4
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime
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

    def to_dict(self) -> dict:
        """Convert the User instance to a dictionary."""
        return {
            'id': str(self.id),
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
