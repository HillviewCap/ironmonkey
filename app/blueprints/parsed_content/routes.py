from flask import render_template, Blueprint, abort, request, current_app
from .services import ParsedContentService
from app.models.relational.parsed_content import ParsedContent

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
    current_app.logger.info(f"Attempting to retrieve content with ID: {content_id}")
    try:
        item = ParsedContent.get_by_id(content_id)
        if item is None:
            current_app.logger.warning(f"Content with ID {content_id} not found in the database")
            abort(404, description="Content not found")
        
        item_dict = ParsedContentService.get_content_by_id(str(content_id))
        if item_dict is None:
            current_app.logger.error(f"ParsedContentService returned None for content ID: {content_id}")
            abort(500, description="Error retrieving content details")
        
        return render_template('parsed_content/view_item.html', item=item_dict)
    except Exception as e:
        current_app.logger.error(f"Error processing content ID {content_id}: {str(e)}")
        abort(500, description=f"Error processing content: {str(e)}")
