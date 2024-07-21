from flask import Blueprint, render_template, abort
from app.models.relational.parsed_content import ParsedContent

parsed_content_bp = Blueprint('parsed_content', __name__)

@parsed_content_bp.route('/view/<uuid:content_id>')
def view(content_id):
    """
    Render the view page for a specific parsed content item.

    This function retrieves the parsed content with the given UUID and renders
    a template to display it. If the content is not found, it returns a 404 error.

    Args:
        content_id (uuid.UUID): The UUID of the parsed content to display.

    Returns:
        str: Rendered HTML template for the parsed content view.

    Raises:
        404: If the parsed content with the given UUID is not found.
    """
    content = ParsedContent.get_by_id(content_id)
    if content:
        return render_template('parsed_content/view.html', content=content)
    else:
        abort(404)
