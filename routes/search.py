from __future__ import annotations

from flask import Blueprint, render_template, request, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectMultipleField
from wtforms.validators import DataRequired
from models import db, ParsedContent
from sqlalchemy import or_
from datetime import datetime
import bleach

search_bp = Blueprint('search', __name__)

class SearchForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])
    start_date = DateField('Start Date')
    end_date = DateField('End Date')
    source_types = SelectMultipleField('Source Types')
    keywords = StringField('Keywords')

def build_search_query(search_params):
    query = db.session.query(ParsedContent)

    query = query.filter(
        or_(
            ParsedContent.title.ilike(f"%{bleach.clean(search_params.query)}%"),
            ParsedContent.content.ilike(f"%{bleach.clean(search_params.query)}%"),
        )
    )

    if search_params.start_date:
        query = query.filter(ParsedContent.date >= search_params.start_date)

    if search_params.end_date:
        query = query.filter(ParsedContent.date <= search_params.end_date)

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

@search_bp.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    form.source_types.choices = [('blog', 'Blog'), ('news', 'News'), ('report', 'Report')]  # Add more as needed

    if form.validate_on_submit():
        search_params = {
            'query': form.query.data,
            'start_date': form.start_date.data,
            'end_date': form.end_date.data,
            'source_types': form.source_types.data,
            'keywords': form.keywords.data.split(',') if form.keywords.data else []
        }

        query = build_search_query(search_params)
        page = request.args.get('page', 1, type=int)
        per_page = 10
        paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)
        total_results = query.count()

        current_app.logger.info(f"Search completed. Total results: {total_results}")

        return render_template(
            'search_results.html',
            form=form,
            results=paginated_results,
            total_results=total_results,
            search_params=search_params
        )

    return render_template('search.html', form=form)
