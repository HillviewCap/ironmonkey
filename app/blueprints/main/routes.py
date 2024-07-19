from flask import render_template, send_from_directory, redirect, url_for, abort, current_app
from flask_login import current_user, login_required
import os
from app.models.relational.parsed_content import ParsedContent
from . import bp

@bp.route('/')
def index():
    current_app.logger.info("Entering index route")
    try:
        if current_user.is_authenticated:
            recent_items = (
                ParsedContent.query
                .filter(
                    ParsedContent.title.isnot(None),
                    ParsedContent.description.isnot(None),
                )
                .order_by(ParsedContent.published.desc())
                .limit(10)
                .all()
            )
            return render_template('index.html', recent_items=recent_items)
        else:
            return render_template('index.html')
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        abort(500)  # Return a 500 Internal Server Error

@bp.route('/item/<uuid:item_id>')
@login_required
def view_item(item_id):
    item = ParsedContent.query.get(item_id)
    if item is None:
        abort(404)
    return render_template('view_item.html', item=item)

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(bp.root_path, '..', '..', 'static', 'images'),
                               'favicon.ico', mimetype='image/x-icon')

@bp.errorhandler(500)
def internal_error(error):
    current_app.logger.error('Server Error: %s', (error))
    return render_template('errors/500.html'), 500
