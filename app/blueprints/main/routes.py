from flask import render_template, current_app
from flask_login import current_user, login_required
from . import main
from app.models.relational import db, ParsedContent

@main.route('/')
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
from flask import render_template, current_app
from app.blueprints.main import bp
from app.models import ParsedContent
from app import db

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
        return render_error_page()

# Add other main routes here
