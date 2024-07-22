from __future__ import annotations

from sqlalchemy import Column, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app import db
from typing import List
import uuid

class AllGroups(db.Model):
    """
    Represents the AllGroups table in the database.
    """
    __tablename__ = 'allgroups'

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

    values: List[AllGroupsValues] = relationship("AllGroupsValues", back_populates="allgroup")

    __table_args__ = (Index('idx_allgroups_uuid', uuid),)

class AllGroupsValues(db.Model):
    """
    Represents the AllGroupsValues table in the database.
    """
    __tablename__ = 'allgroups_values'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor = Column(String)
    country = Column(Text)
    description = Column(Text)
    information = Column(Text)
    last_card_change = Column(String)
    motivation = Column(Text)
    first_seen = Column(String)
    observed_sectors = Column(Text)
    observed_countries = Column(Text)
    tools = Column(Text)
    operations = Column(Text)
    sponsor = Column(Text)
    counter_operations = Column(Text)
    mitre_attack = Column(Text)
    playbook = Column(Text)
    allgroups_uuid = Column(UUID(as_uuid=True), ForeignKey('allgroups.uuid'))

    allgroup: AllGroups = relationship("AllGroups", back_populates="values")
    names: List[AllGroupsValuesNames] = relationship("AllGroupsValuesNames", back_populates="allgroups_value")

    __table_args__ = (Index('idx_allgroups_values_uuid', uuid),)

class AllGroupsValuesNames(db.Model):
    """
    Represents the AllGroupsValuesNames table in the database.
    """
    __tablename__ = 'allgroups_values_names'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    name_giver = Column(String)
    allgroups_values_uuid = Column(UUID(as_uuid=True), ForeignKey('allgroups_values.uuid'))

    allgroups_value: AllGroupsValues = relationship("AllGroupsValues", back_populates="names")
