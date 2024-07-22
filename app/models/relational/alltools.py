from __future__ import annotations

from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID
from app import db
from typing import List
import uuid

class AllTools(db.Model):
    """
    Represents the AllTools table in the database.
    """
    __tablename__ = 'alltools'

    uuid: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authors: Mapped[str] = Column(Text)
    category: Mapped[str] = Column(String)
    name: Mapped[str] = Column(String)
    type: Mapped[str] = Column(String)
    source: Mapped[str] = Column(String)
    description: Mapped[str] = Column(Text)
    tlp: Mapped[str] = Column(String)
    license: Mapped[str] = Column(String)
    last_db_change: Mapped[str] = Column(String)

    values: Mapped[List[AllToolsValues]] = relationship("AllToolsValues", back_populates="alltool")

    __table_args__ = (Index('idx_alltools_uuid', uuid),)

class AllToolsValues(db.Model):
    """
    Represents the AllToolsValues table in the database.
    """
    __tablename__ = 'alltools_values'

    uuid: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool: Mapped[str] = Column(String)
    description: Mapped[str] = Column(Text)
    category: Mapped[str] = Column(String)
    type: Mapped[str] = Column(String)
    information: Mapped[str] = Column(Text)
    last_card_change: Mapped[str] = Column(String)
    alltools_uuid: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey('alltools.uuid'))

    alltool: Mapped[AllTools] = relationship("AllTools", back_populates="values")
    names: Mapped[List[AllToolsValuesNames]] = relationship("AllToolsValuesNames", back_populates="alltools_value")

    __table_args__ = (Index('idx_alltools_values_uuid', uuid),)

class AllToolsValuesNames(db.Model):
    """
    Represents the AllToolsValuesNames table in the database.
    """
    __tablename__ = 'alltools_values_names'

    uuid: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = Column(String)
    alltools_values_uuid: Mapped[UUID] = Column(UUID(as_uuid=True), ForeignKey('alltools_values.uuid'))

    alltools_value: Mapped[AllToolsValues] = relationship("AllToolsValues", back_populates="names")
