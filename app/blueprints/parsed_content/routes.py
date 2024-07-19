from flask import Blueprint, render_template, abort
from app.models.relational.parsed_content import ParsedContent

parsed_content_bp = Blueprint('parsed_content', __name__)

@parsed_content_bp.route('/view/<uuid:content_id>')
def view(content_id):
    content = ParsedContent.get_by_id(content_id)
    if content:
        return render_template('parsed_content/view.html', content=content)
    else:
        abort(404)
