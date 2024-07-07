from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    sentiment = Column(Float)

    entities = relationship("Entity", backref="document")


class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    name = Column(String)
    diffbotUri = Column(String)
    confidence = Column(Float)
    salience = Column(Float)
    sentiment = Column(Float)
    isCustom = Column(Boolean)

    mentions = relationship("EntityMention", backref="entity")
    types = relationship("EntityType", backref="entity")
    uris = relationship("EntityUri", backref="entity")


class EntityMention(Base):
    __tablename__ = "entity_mentions"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"))
    text = Column(String)
    beginOffset = Column(Integer)
    endOffset = Column(Integer)
    confidence = Column(Float)


class EntityType(Base):
    __tablename__ = "entity_types"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"))
    name = Column(String)
    diffbotUri = Column(String)
    dbpediaUri = Column(String)


class EntityUri(Base):
    __tablename__ = "entity_uris"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"))
    uri = Column(String)


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    categoryId = Column(String)
    name = Column(String)
    path = Column(String)
    confidence = Column(Float)
    isPrimary = Column(Boolean)
