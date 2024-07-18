from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class AllTools(Base):
    __tablename__ = 'alltools'

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

    values = relationship("AllToolsValues", back_populates="alltool")

class AllToolsValues(Base):
    __tablename__ = 'alltools_values'

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool = Column(String)
    description = Column(Text)
    category = Column(String)
    type = Column(String)
    information = Column(Text)
    last_card_change = Column(String)
    alltools_uuid = Column(String(36), ForeignKey('alltools.uuid'))

    alltool = relationship("AllTools", back_populates="values")
    names = relationship("AllToolsValuesNames", back_populates="alltools_value")

class AllToolsValuesNames(Base):
    __tablename__ = 'alltools_values_names'

    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    alltools_values_uuid = Column(String(36), ForeignKey('alltools_values.uuid'))

    alltools_value = relationship("AllToolsValues", back_populates="names")

# Add indexes for frequently queried columns
from sqlalchemy import Index
Index('idx_alltools_uuid', AllTools.uuid)
Index('idx_alltools_values_uuid', AllToolsValues.uuid)
