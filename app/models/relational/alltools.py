from __future__ import annotations

from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app import db
from typing import List
import uuid

class AllTools(db.Model):
    """
    Represents the AllTools table in the database.
    """
    __tablename__ = 'alltools'

    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authors: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    tlp: Mapped[str] = mapped_column(String)
    license: Mapped[str] = mapped_column(String)
    last_db_change: Mapped[str] = mapped_column(String)

    values: Mapped[List["AllToolsValues"]] = relationship("AllToolsValues", back_populates="alltool")

    __table_args__ = (Index('idx_alltools_uuid', uuid),)

class AllToolsValues(db.Model):
    """
    Represents the AllToolsValues table in the database.
    """
    __tablename__ = 'alltools_values'

    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    information: Mapped[str] = mapped_column(Text)
    last_card_change: Mapped[str] = mapped_column(String)
    alltools_uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('alltools.uuid'))

    alltool: Mapped["AllTools"] = relationship("AllTools", back_populates="values")
    names: Mapped[List["AllToolsValuesNames"]] = relationship("AllToolsValuesNames", back_populates="alltools_value")

    __table_args__ = (Index('idx_alltools_values_uuid', uuid),)

class AllToolsValuesNames(db.Model):
    """
    Represents the AllToolsValuesNames table in the database.
    """
    __tablename__ = 'alltools_values_names'

    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    alltools_values_uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('alltools_values.uuid'))

    alltools_value: Mapped["AllToolsValues"] = relationship("AllToolsValues", back_populates="names")
