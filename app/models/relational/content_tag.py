from __future__ import annotations
from sqlalchemy import Column, ForeignKey, String, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid

class ContentTag(db.Model):
    __tablename__ = 'content_tags'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_content_id = Column(UUID(as_uuid=True), ForeignKey('parsed_content.id'), nullable=False)
    entity_type = Column(String, nullable=False)  # 'actor' or 'tool'
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_name = Column(String, nullable=False)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)

    parsed_content = relationship("ParsedContent", back_populates="tags")

    def get_tagged_content(self):
        from app.utils.auto_tagger import tag_content
        content = self.to_dict()
        if content.get('description'):
            content['description'] = tag_content(content['description'])
        if content.get('summary'):
            content['summary'] = tag_content(content['summary'])
        return content

    __table_args__ = (
        Index('idx_content_tags_parsed_content_id', parsed_content_id),
        Index('idx_content_tags_entity_type_id', entity_type, entity_id),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id),
            'entity_name': self.entity_name,
            'start_char': self.start_char,
            'end_char': self.end_char
        }
