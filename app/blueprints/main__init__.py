"""
This module defines the main blueprint for the application.

It includes routes for the index page and error handling.
"""

from flask import Blueprint, render_template, current_app, abort
from flask_login import current_user, login_required
from app.models.relational import db, ParsedContent

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """
    Render the index page.

    If the user is authenticated, it displays the 10 most recent parsed content items.
    Otherwise, it renders the default index page.

    Returns:
        str: Rendered HTML template for the index page.
    """
    current_app.logger.info("Entering index route")
    try:
        if current_user.is_authenticated:
            recent_items = (
                db.session.query(ParsedContent)
                .filter(
                    ParsedContent.title.isnot(None),
                    ParsedContent.description.isnot(None),
                )
                .order_by(ParsedContent.published.desc())
                .limit(6)
                .all()
            )
            return render_template('index.html', recent_items=recent_items)
        else:
            return render_template('index.html')
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        abort(500)  # Return a 500 Internal Server Error

@bp.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server Error.

    Args:
        error: The error that occurred.

    Returns:
        tuple: A tuple containing the rendered error template and the HTTP status code.
    """
    current_app.logger.error('Server Error: %s', (error))
    return render_template('errors/500.html'), 500

def init_app(app):
    """
    Initialize the blueprint with the Flask application.

    Args:
        app: The Flask application instance.
    """
    app.register_blueprint(bp)

# Explicitly export bp
__all__ = ['bp']
