from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AllTools(Base):
    __tablename__ = 'alltools'

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

    values = relationship("AllToolsValues", back_populates="alltool")

class AllToolsValues(Base):
    __tablename__ = 'alltools_values'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool = Column(String)
    description = Column(Text)
    category = Column(String)
    type = Column(String)
    information = Column(Text)
    uuid = Column(String)
    last_card_change = Column(String)
    alltools_id = Column(Integer, ForeignKey('alltools.id'))

    alltool = relationship("AllTools", back_populates="values")
    names = relationship("AllToolsValuesNames", back_populates="alltools_value")

class AllToolsValuesNames(Base):
    __tablename__ = 'alltools_values_names'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    alltools_values_id = Column(Integer, ForeignKey('alltools_values.id'))

    alltools_value = relationship("AllToolsValues", back_populates="names")

# You might want to add indexes here for frequently queried columns
# For example:
# from sqlalchemy import Index
# Index('idx_alltools_uuid', AllTools.uuid)
# Index('idx_alltools_values_uuid', AllToolsValues.uuid)
