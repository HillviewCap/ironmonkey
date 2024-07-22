from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from app.extensions import db
from app.models.relational.user import User
from app.models.relational.search_params import SearchParams
from app.models.relational.rss_feed import RSSFeed
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.category import Category
from app.models.relational.awesome_threat_intel_blog import AwesomeThreatIntelBlog

__all__ = [
    "User",
    "SearchParams",
    "RSSFeed",
    "ParsedContent",
    "Category",
    "AwesomeThreatIntelBlog",
    "SearchResult",
]


class SearchResult(BaseModel):
    """Represents a search result."""

    id: UUID = Field(..., description="Unique identifier for the search result")
    title: str = Field(..., description="Title of the search result")
    description: str = Field(..., description="Description of the search result")
    source_type: str = Field(..., description="Type of the source (e.g., 'blog', 'news')")
    date: datetime = Field(..., description="Date of the search result")
    url: str = Field(..., description="URL of the search result")

    class Config:
        orm_mode = True
