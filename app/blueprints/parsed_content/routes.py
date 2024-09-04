from flask import render_template, Blueprint, abort, request, current_app
from .services import ParsedContentService
from app.models.relational.parsed_content import ParsedContent
from uuid import UUID

parsed_content_bp = Blueprint('parsed_content', __name__)

@parsed_content_bp.route('/')
def parsed_content():
    category = request.args.get('category')
    content_service = ParsedContentService()
    latest_content = content_service.get_latest_parsed_content(category=category)
    content_stats = content_service.get_content_stats()
    return render_template('parsed_content/index.html', content=latest_content['content'], stats=content_stats, selected_category=category)

@parsed_content_bp.route('/item/<string:content_id>', methods=['GET'])
def view_item(content_id):
    current_app.logger.info(f"Attempting to retrieve content with ID: {content_id}")
    try:
        # Convert string to UUID
        content_uuid = UUID(content_id)
        current_app.logger.info(f"UUID conversion successful: {content_uuid}")
        
        item_dict = ParsedContentService.get_content_by_id(content_uuid)
        current_app.logger.info(f"Result from get_content_by_id: {item_dict}")
        
        if item_dict is None:
            current_app.logger.warning(f"Content with ID {content_id} not found in the database")
            return render_template('errors/404.html'), 404

        return render_template('parsed_content/view_item.html', item=item_dict)
    except ValueError as ve:
        current_app.logger.error(f"Invalid UUID format for content ID: {content_id}. Error: {str(ve)}")
        return render_template('errors/400.html'), 400
    except Exception as e:
        current_app.logger.error(f"Error processing content ID {content_id}: {str(e)}")
        return render_template('errors/500.html'), 500

@parsed_content_bp.route('/content/item/<string:content_id>', methods=['GET'])
def legacy_view_item(content_id):
    current_app.logger.info(f"Legacy route accessed for content ID: {content_id}")
    return view_item(content_id)
