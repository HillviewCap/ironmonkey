from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AllGroups(Base):
    __tablename__ = 'allgroups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    authors = Column(Text)
    category = Column(String)
    name = Column(String)
    type = Column(String)
    source = Column(String)
    description = Column(Text)
    tlp = Column(String)
    license = Column(String)
    uuid = Column(String)
    last_db_change = Column(String)

    values = relationship("AllGroupsValues", back_populates="allgroup")

class AllGroupsValues(Base):
    __tablename__ = 'allgroups_values'

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String)
    country = Column(String)
    description = Column(Text)
    information = Column(Text)
    uuid = Column(String)
    last_card_change = Column(String)
    allgroups_id = Column(Integer, ForeignKey('allgroups.id'))

    allgroup = relationship("AllGroups", back_populates="values")
    names = relationship("AllGroupsValuesNames", back_populates="allgroups_value")

class AllGroupsValuesNames(Base):
    __tablename__ = 'allgroups_values_names'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    name_giver = Column(String)
    allgroups_values_id = Column(Integer, ForeignKey('allgroups_values.id'))

    allgroups_value = relationship("AllGroupsValues", back_populates="names")

# You might want to add indexes here for frequently queried columns
# For example:
# from sqlalchemy import Index
# Index('idx_allgroups_uuid', AllGroups.uuid)
# Index('idx_allgroups_values_uuid', AllGroupsValues.uuid)
