from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class SearchParams(BaseModel):
    query: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_types: Optional[List[str]] = None
    keywords: Optional[List[str]] = None

class SearchResult(BaseModel):
    id: str
    title: str
    description: str
    source_type: str
    date: datetime
    url: str
