from flask import render_template, Blueprint, abort
from .services import ParsedContentService

parsed_content_bp = Blueprint('parsed_content', __name__)

@parsed_content_bp.route('/')
def parsed_content():
    content_service = ParsedContentService()
    latest_content = content_service.get_latest_parsed_content()
    content_stats = content_service.get_content_stats()
    return render_template('parsed_content/index.html', content=latest_content['content'], stats=content_stats)

@parsed_content_bp.route('/item/<content_id>', methods=['GET'])
def view_item(content_id):
    content_service = ParsedContentService()
    item = content_service.get_content_by_id(content_id)
    if item is None:
        abort(404)  # Return a 404 error if the item is not found
    return render_template('view_item.html', item=item)
