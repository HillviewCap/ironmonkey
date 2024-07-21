from flask import Blueprint, render_template, abort, request, redirect, url_for, jsonify
from app.models.relational.parsed_content import ParsedContent
from app.services.parsed_content_service import ParsedContentService

parsed_content_bp = Blueprint('parsed_content', __name__)

@parsed_content_bp.route('/summarize_content', methods=['POST'])
def summarize_content():
    content_id = request.json.get('content_id')
    # Implement your summarization logic here
    # For now, we'll just return a dummy response
    return jsonify({'summary': 'This is a dummy summary.'})

@parsed_content_bp.route('/clear_all_summaries', methods=['POST'])
def clear_all_summaries():
    # Implement your logic to clear all summaries here
    # For now, we'll just return a dummy response
    return jsonify({'message': 'All summaries have been cleared.'})

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
    content = ParsedContentService.get_content_by_id(content_id)
    if content:
        return render_template('parsed_content/view.html', content=content)
    else:
        abort(404)

@parsed_content_bp.route('/add', methods=['POST'])
def add_parsed_content():
    """
    Add a new parsed content item.

    This function handles the POST request to add a new parsed content item.
    It retrieves the form data, creates a new parsed content item, and redirects to the admin page.

    Returns:
        redirect: Redirects to the admin page after adding the content.
    """
    content_data = {
        'title': request.form['title'],
        'url': request.form['url'],
        'description': request.form['description'],
        'pub_date': request.form['date'],
        'source_type': request.form['source_type'],
        'content': ''  # You might want to add a field for content in your form
    }
    ParsedContentService.create_parsed_content(content_data)
    return redirect(url_for('admin.manage_parsed_content'))

@parsed_content_bp.route('/edit/<uuid:content_id>', methods=['GET', 'POST'])
def edit_parsed_content(content_id):
    """
    Edit an existing parsed content item.

    This function handles both GET and POST requests to edit a parsed content item.
    For GET requests, it renders the edit form. For POST requests, it updates the content.

    Args:
        content_id (uuid.UUID): The UUID of the parsed content to edit.

    Returns:
        str: Rendered HTML template for editing or redirect to admin page after updating.
    """
    content = ParsedContentService.get_content_by_id(content_id)
    if not content:
        abort(404)

    if request.method == 'POST':
        content_data = {
            'title': request.form['title'],
            'url': request.form['url'],
            'description': request.form['description'],
            'pub_date': request.form['date'],
            'source_type': request.form['source_type'],
            'content': content.content  # Preserve existing content
        }
        ParsedContentService.update_parsed_content(content_id, content_data)
        return redirect(url_for('admin.manage_parsed_content'))

    return render_template('parsed_content/edit.html', content=content)

@parsed_content_bp.route('/delete/<uuid:content_id>', methods=['POST'])
def delete_parsed_content(content_id):
    """
    Delete a parsed content item.

    This function handles the POST request to delete a parsed content item.

    Args:
        content_id (uuid.UUID): The UUID of the parsed content to delete.

    Returns:
        redirect: Redirects to the admin page after deleting the content.
    """
    ParsedContentService.delete_parsed_content(content_id)
    return redirect(url_for('admin.manage_parsed_content'))
