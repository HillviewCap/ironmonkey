from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Text, DateTime
from app import db

class Threat(db.Model):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source_type = Column(String(100), nullable=False)
    date = Column(DateTime, nullable=False)
    url = Column(String(255), nullable=False)
