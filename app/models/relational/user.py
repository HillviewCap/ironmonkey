from __future__ import annotations

from uuid import UUID as PyUUID, uuid4
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String
from app import db

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    def get_id(self) -> str:
        """Return the user ID as a string."""
        return str(self.id)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password, password)
