from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field

class SearchParams(BaseModel):
    query: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    source_types: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
