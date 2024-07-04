from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.UUID(as_uuid=True), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

class SearchParams(BaseModel):
    query: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None

class SearchResult(BaseModel):
    id: UUID
    title: str
    description: str
    source_type: str
    date: datetime
    url: str
