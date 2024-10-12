from flask import Blueprint, render_template, abort
from app.models.relational.parsed_content import ParsedContent

parsed_content_bp = Blueprint('parsed_content', __name__)

@parsed_content_bp.route('/item/<uuid:content_id>')
def view_item(content_id):
    item = ParsedContent.get_by_id(content_id)
    if item:
        tagged_content = item.get_tagged_content()
        return render_template('parsed_content/view_item.html', item=tagged_content)
    else:
        abort(404, description="Content not found.")
