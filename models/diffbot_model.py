from sqlalchemy import Column, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(String)
    sentiment = Column(Float)

    entities = relationship("Entity", backref="document")
    categories = relationship("Category", backref="document")


class Entity(Base):
    __tablename__ = "entities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    name = Column(String)
    diffbot_uri = Column(String)
    confidence = Column(Float)
    salience = Column(Float)
    sentiment = Column(Float)
    is_custom = Column(Boolean)

    mentions = relationship("EntityMention", backref="entity")
    types = relationship("EntityType", backref="entity")
    uris = relationship("EntityUri", backref="entity")


class EntityMention(Base):
    __tablename__ = "entity_mentions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"))
    text = Column(String)
    begin_offset = Column(Float)
    end_offset = Column(Float)
    confidence = Column(Float)


class EntityType(Base):
    __tablename__ = "entity_types"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"))
    name = Column(String)
    diffbot_uri = Column(String)
    dbpedia_uri = Column(String)


class EntityUri(Base):
    __tablename__ = "entity_uris"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"))
    uri = Column(String)


class Category(Base):
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    category_id = Column(String)
    name = Column(String)
    path = Column(String)
    confidence = Column(Float)
    is_primary = Column(Boolean)
