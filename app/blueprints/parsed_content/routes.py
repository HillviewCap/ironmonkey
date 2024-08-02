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

@parsed_content_bp.route('/item/<uuid:content_id>', methods=['GET'])
def view_item(content_id):
    item = ParsedContent.get_by_id(content_id)
    if item is None:
        abort(404, description="Content not found")
    try:
        item_dict = ParsedContentService.get_content_by_id(str(content_id))
        return render_template('parsed_content/view_item.html', item=item_dict)
    except Exception as e:
        abort(400, description=str(e))
