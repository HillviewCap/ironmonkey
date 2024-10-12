import json
from flask import render_template, abort, jsonify, request, current_app
from datetime import datetime, time
from .services import ParsedContentService
from . import bp
from app.models.relational.parsed_content import ParsedContent

@bp.route('/')
def parsed_content():
    # Get the 'date' parameter from the query string, defaulting to today's date if not provided
    date_str = request.args.get('date', datetime.utcnow().date().isoformat())
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        # If date parsing fails, default to today's date
        selected_date = datetime.utcnow().date()
    start_of_day = datetime.combine(selected_date, time.min)
    end_of_day = datetime.combine(selected_date, time.max)

    content = ParsedContent.query.filter(
        ParsedContent.pub_date.between(start_of_day, end_of_day)
    ).order_by(ParsedContent.pub_date.desc()).all()

    parsed_content_service = ParsedContentService()
    stats = parsed_content_service.calculate_stats(content)

    return render_template('parsed_content/index.html', content=content, stats=stats, selected_date=selected_date.isoformat())

@bp.route('/list')
def list_content():
    selected_date = request.args.get('date', datetime.utcnow().date().isoformat())
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    start_of_day = datetime.combine(selected_date, time.min)
    end_of_day = datetime.combine(selected_date, time.max)

    content = ParsedContent.query.filter(
        ParsedContent.pub_date.between(start_of_day, end_of_day)
    ).order_by(ParsedContent.pub_date.desc()).all()

    parsed_content_service = ParsedContentService()
    stats = parsed_content_service.calculate_stats(content)

    return jsonify({
        'content': [item.to_dict() for item in content],
        'stats': stats
    })

import json

def is_valid_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError:
        return False
    return True
def view_item(item_id):
    item_instance = ParsedContent.get_by_id(item_id)
    if not item_instance:
        abort(404)
    # Get content with entities tagged
    item = item_instance.get_tagged_content()
    # Initialize summary_data
    summary_data = None
    if item.get('summary'):
        try:
            summary_data = json.loads(item['summary'])
        except json.JSONDecodeError as e:
            current_app.logger.error(
                f"Error parsing summary JSON for item {item_id}: {str(e)}"
            )
            current_app.logger.debug(f"Invalid JSON content: {item['summary']}")
            summary_data = None

    return render_template(
        'parsed_content/view_item.html',
        item=item,
        summary_data=summary_data
    )
