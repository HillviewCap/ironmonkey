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
