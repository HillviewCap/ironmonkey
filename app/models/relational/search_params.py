from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, validator

class SearchParams(BaseModel):
    """Model for search parameters."""

    query: str = Field(default="", description="Search query string")
    start_date: Optional[date] = Field(default=None, description="Start date for the search range")
    end_date: Optional[date] = Field(default=None, description="End date for the search range")
    source_types: List[str] = Field(default_factory=list, description="List of source types to search")
    keywords: List[str] = Field(default_factory=list, description="List of keywords to search for")

    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v and values['start_date'] and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    class Config:
        schema_extra = {
            "example": {
                "query": "cybersecurity threats",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "source_types": ["blog", "news"],
                "keywords": ["ransomware", "phishing"]
            }
        }
