from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class AllGroups(Base):
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

    values = relationship("AllGroupsValues", back_populates="allgroup")

class AllGroupsValues(Base):
    __tablename__ = 'allgroups_values'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor = Column(String)
    country = Column(String)
    description = Column(Text)
    information = Column(Text)
    last_card_change = Column(String)
    allgroups_uuid = Column(UUID(as_uuid=True), ForeignKey('allgroups.uuid'))

    allgroup = relationship("AllGroups", back_populates="values")
    names = relationship("AllGroupsValuesNames", back_populates="allgroups_value")

class AllGroupsValuesNames(Base):
    __tablename__ = 'allgroups_values_names'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    name_giver = Column(String)
    allgroups_values_uuid = Column(UUID(as_uuid=True), ForeignKey('allgroups_values.uuid'))

    allgroups_value = relationship("AllGroupsValues", back_populates="names")

# Add indexes for frequently queried columns
from sqlalchemy import Index
Index('idx_allgroups_uuid', AllGroups.uuid)
Index('idx_allgroups_values_uuid', AllGroupsValues.uuid)
