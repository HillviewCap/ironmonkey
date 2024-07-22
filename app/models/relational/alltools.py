from __future__ import annotations

from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app import db
from typing import List
import uuid

class AllTools(db.Model):
    """
    Represents the AllTools table in the database.
    """
    __tablename__ = 'alltools'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authors = Column(Text)
    category = Column(String)
    name = Column(String)
    type = Column(String)
    source = Column(String)
    description = Column(Text)
    tlp = Column(String)
    license = Column(String)
    last_db_change = Column(String)

    values: List[AllToolsValues] = relationship("AllToolsValues", back_populates="alltool")

    __table_args__ = (Index('idx_alltools_uuid', uuid),)

class AllToolsValues(db.Model):
    """
    Represents the AllToolsValues table in the database.
    """
    __tablename__ = 'alltools_values'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool = Column(String)
    description = Column(Text)
    category = Column(String)
    type = Column(String)
    information = Column(Text)
    last_card_change = Column(String)
    alltools_uuid = Column(UUID(as_uuid=True), ForeignKey('alltools.uuid'))

    alltool: AllTools = relationship("AllTools", back_populates="values")
    names: List[AllToolsValuesNames] = relationship("AllToolsValuesNames", back_populates="alltools_value")

    __table_args__ = (Index('idx_alltools_values_uuid', uuid),)

class AllToolsValuesNames(db.Model):
    """
    Represents the AllToolsValuesNames table in the database.
    """
    __tablename__ = 'alltools_values_names'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    alltools_values_uuid = Column(UUID(as_uuid=True), ForeignKey('alltools_values.uuid'))

    alltools_value: AllToolsValues = relationship("AllToolsValues", back_populates="names")
