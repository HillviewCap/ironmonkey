from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required
from models import db, User, ParsedContent, RSSFeed

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def admin():
    users = User.query.all()
    parsed_content = ParsedContent.query.all()
    rss_feeds = RSSFeed.query.all()
    return render_template(
        "admin.html",
        users=users,
        parsed_content=parsed_content,
        rss_feeds=rss_feeds,
    )

@admin_bp.route('/deduplicate', methods=['POST'])
@login_required
def deduplicate_parsed_content():
    try:
        deleted_count = ParsedContent.deduplicate()
        flash(f"Successfully removed {deleted_count} duplicate entries.", "success")
    except Exception as e:
        current_app.logger.error(f"Error during deduplication: {str(e)}")
        flash("An error occurred during deduplication.", "error")
    return redirect(url_for('admin.admin'))
