from flask import render_template, Blueprint, abort, request
from .services import ParsedContentService

parsed_content_bp = Blueprint('parsed_content', __name__)

@parsed_content_bp.route('/')
def parsed_content():
    category = request.args.get('category')
    content_service = ParsedContentService()
    latest_content = content_service.get_latest_parsed_content(category=category)
    content_stats = content_service.get_content_stats()
    return render_template('parsed_content/index.html', content=latest_content['content'], stats=content_stats, selected_category=category)

@parsed_content_bp.route('/item/<content_id>', methods=['GET'])
def view_item(content_id):
    try:
        item = ParsedContentService.get_content_by_id(str(content_id))
        if item is None:
            abort(404)  # Return a 404 error if the item is not found
        return render_template('parsed_content/view_item.html', item=item)
    except ValueError:
        abort(400)  # Return a 400 error if the content_id is not a valid UUID
