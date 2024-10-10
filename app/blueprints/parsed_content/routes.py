from flask import render_template, abort
from datetime import datetime, time
from .services import ParsedContentService
from . import bp
from app.models.relational.parsed_content import ParsedContent

@bp.route('/')
def parsed_content():
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, time.min)
    end_of_day = datetime.combine(today, time.max)

    content = ParsedContent.query.filter(
        ParsedContent.pub_date.between(start_of_day, end_of_day)
    ).order_by(ParsedContent.pub_date.desc()).all()

    parsed_content_service = ParsedContentService()
    stats = parsed_content_service.calculate_stats(content)

    return render_template('parsed_content/index.html', content=content, stats=stats)

@bp.route('/item/<uuid:item_id>')
def view_item(item_id):
    item = ParsedContent.get_by_id(item_id)
    if not item:
        abort(404)
    return render_template('parsed_content/view_item.html', item=item)
