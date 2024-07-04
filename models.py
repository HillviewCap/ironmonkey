from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID as PyUUID
from pydantic import BaseModel, Field
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash

db = SQLAlchemy()

import uuid
from sqlalchemy.dialects.postgresql import UUID

class User(UserMixin, db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def get_id(self):
        return str(self.id)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

class SearchParams(BaseModel):
    query: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None

class SearchResult(BaseModel):
    id: PyUUID = Field(..., alias='id')
    title: str
    description: str
    source_type: str
    date: datetime
    url: str

    class Config:
        arbitrary_types_allowed = True
