from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class AllGroups(Base):
    __tablename__ = 'allgroups'

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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
    allgroups_uuid = Column(String(36), ForeignKey('allgroups.uuid'))

    allgroup = relationship("AllGroups", back_populates="values")
    names = relationship("AllGroupsValuesNames", back_populates="allgroups_value")

class AllGroupsValuesNames(Base):
    __tablename__ = 'allgroups_values_names'

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    name_giver = Column(String)
    allgroups_values_uuid = Column(String(36), ForeignKey('allgroups_values.uuid'))

    allgroups_value = relationship("AllGroupsValues", back_populates="names")

# Add indexes for frequently queried columns
from sqlalchemy import Index
Index('idx_allgroups_uuid', AllGroups.uuid)
Index('idx_allgroups_values_uuid', AllGroupsValues.uuid)
