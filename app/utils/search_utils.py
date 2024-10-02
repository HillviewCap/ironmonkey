from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from sqlalchemy import or_
from app.models.relational import ParsedContent, db
import bleach

@dataclass
class SearchParams:
    query: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_types: List[str] = None
    keywords: List[str] = None

def get_search_params(form):
    return SearchParams(
        query=form.data.get("query", ""),
        start_date=(
            datetime.strptime(form.data.get("start_date"), "%Y-%m-%d").date()
            if form.data.get("start_date")
            else None
        ),
        end_date=(
            datetime.strptime(form.data.get("end_date"), "%Y-%m-%d").date()
            if form.data.get("end_date")
            else None
        ),
        source_types=form.data.get("source_types", []),
        keywords=(
            form.data.get("keywords", "").split(",")
            if form.data.get("keywords")
            else []
        ),
    )

def build_search_query(search_params: SearchParams):
    query = db.session.query(ParsedContent)

    query = query.filter(
        or_(
            ParsedContent.title.ilike(f"%{bleach.clean(search_params.query)}%"),
            ParsedContent.content.ilike(f"%{bleach.clean(search_params.query)}%"),
        )
    )

    if search_params.start_date:
        query = query.filter(ParsedContent.created_at >= search_params.start_date)

    if search_params.end_date:
        query = query.filter(ParsedContent.created_at <= search_params.end_date)

    if search_params.source_types:
        query = query.filter(
            ParsedContent.source_type.in_(
                [bleach.clean(st) for st in search_params.source_types]
            )
        )

    if search_params.keywords:
        for keyword in search_params.keywords:
            query = query.filter(
                or_(
                    ParsedContent.title.ilike(f"%{bleach.clean(keyword)}%"),
                    ParsedContent.content.ilike(f"%{bleach.clean(keyword)}%"),
                )
            )

    return query

def perform_search(search_params: SearchParams, page: int = 1, per_page: int = 10, order_by=None):
    query = build_search_query(search_params)

    if order_by:
        query = query.order_by(order_by)

    try:
        paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)
        total_results = query.count()
        return paginated_results, total_results
    except Exception as e:
        # Log the error here
        return None, 0
