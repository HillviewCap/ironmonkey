from __future__ import annotations

from datetime import datetime
from uuid import UUID as PyUUID
from pydantic import BaseModel, Field

from ...extensions import db
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
    """
    Represents a search result.
    """

    id: PyUUID = Field(..., alias="id")
    title: str
    description: str
    source_type: str
    date: datetime
    url: str

    class Config:
        arbitrary_types_allowed = True
