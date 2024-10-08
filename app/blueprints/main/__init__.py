from flask import Blueprint, render_template, current_app
from flask_login import login_required
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.rss_feed import RSSFeed
from sqlalchemy import desc
from datetime import datetime, time

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    recent_items = (
        ParsedContent.query
        .join(RSSFeed)
        .with_entities(ParsedContent, RSSFeed.title.label('feed_title'))
        .order_by(desc(ParsedContent.pub_date))
        .limit(6)
        .all()
    )

    current_time = datetime.now().time()
    midday_time = time(12, 0)
    end_of_day_time = time(18, 0)

    return render_template('index.html', 
                           recent_items=recent_items, 
                           current_time=current_time,
                           midday_time=midday_time,
                           end_of_day_time=end_of_day_time)

from . import routes

# Apply login_required to all routes in this blueprint
@bp.before_request
@login_required
def before_request():
    pass

__all__ = ['bp']
