from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
import random

Base = declarative_base()

class Threat(Base):
    __tablename__ = 'threats'

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    source_type = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    url = Column(String, nullable=False)

engine = create_engine('sqlite:///threats.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

source_types = ['news', 'blog', 'report']
keywords = ['malware', 'phishing', 'ransomware', 'data breach', 'zero-day']

for i in range(100):
    threat = Threat(
        id=f"THREAT-{i+1:03d}",
        title=f"Sample Threat {i+1}",
        description=f"This is a sample threat description containing keywords like {random.choice(keywords)} and {random.choice(keywords)}.",
        source_type=random.choice(source_types),
        date=datetime.now() - timedelta(days=random.randint(0, 365)),
        url=f"https://example.com/threat-{i+1}"
    )
    session.add(threat)

session.commit()
session.close()

print("Sample data created successfully.")
