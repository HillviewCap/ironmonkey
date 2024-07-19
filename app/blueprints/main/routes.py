from flask import render_template, current_app
from flask_login import current_user, login_required
from app.models.relational import db, ParsedContent
from app.blueprints.main import bp

@bp.route('/')
@login_required
def index():
    recent_items = (
        db.session.query(ParsedContent)
        .filter(
            ParsedContent.title.isnot(None),
            ParsedContent.description.isnot(None),
        )
        .order_by(ParsedContent.created_at.desc())
        .limit(6)
        .all()
    )
    return render_template("index.html", recent_items=recent_items)
from flask import render_template, current_app, abort
from flask_login import current_user
from app.models import ParsedContent
from app import db
from . import bp

@bp.route('/')
def index():
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
                .limit(10)
                .all()
            )
            return render_template('index.html', recent_items=recent_items)
        else:
            return render_template('index.html')
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        abort(500)  # Return a 500 Internal Server Error

# Add other main routes here

@bp.errorhandler(500)
def internal_error(error):
    current_app.logger.error('Server Error: %s', (error))
    return render_template('errors/500.html'), 500
