from flask import render_template, Blueprint
from .services import ParsedContentService

parsed_content_bp = Blueprint('parsed_content', __name__)

@parsed_content_bp.route('/')
def parsed_content():
    content_service = ParsedContentService()
    latest_content = content_service.get_latest_parsed_content()
    content_stats = content_service.get_content_stats()
    return render_template('parsed_content/index.html', content=latest_content, stats=content_stats)
