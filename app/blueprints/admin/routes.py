from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.models import db, User, ParsedContent, RSSFeed
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/")
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

@admin_bp.route("/deduplicate", methods=["POST"])
@login_required
def deduplicate_parsed_content():
    try:
        deleted_count = ParsedContent.deduplicate()
        flash(f"Successfully removed {deleted_count} duplicate entries.", "success")
    except Exception as e:
        current_app.logger.error(f"Error during deduplication: {str(e)}")
        flash("An error occurred during deduplication.", "error")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/add_parsed_content", methods=["POST"])
@login_required
def add_parsed_content():
    try:
        new_content = ParsedContent(
            title=request.form["title"],
            url=request.form["url"],
            date=datetime.strptime(request.form["date"], "%Y-%m-%d").date(),
            source_type=request.form["source_type"],
        )
        db.session.add(new_content)
        db.session.commit()
        flash("New content added successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding new content: {str(e)}")
        flash("An error occurred while adding new content.", "error")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/edit_parsed_content/<uuid:content_id>", methods=["GET", "POST"])
@login_required
def edit_parsed_content(content_id):
    content = ParsedContent.query.get_or_404(content_id)
    if request.method == "POST":
        try:
            content.title = request.form["title"]
            content.url = request.form["url"]
            content.date = datetime.strptime(
                request.form["date"], "%Y-%m-%d"
            ).date()
            content.source_type = request.form["source_type"]
            db.session.commit()
            flash("Content updated successfully.", "success")
            return redirect(url_for("admin.admin"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating content: {str(e)}")
            flash("An error occurred while updating content.", "error")
    return render_template("edit_parsed_content.html", content=content)

@admin_bp.route("/delete_parsed_content/<uuid:content_id>", methods=["POST"])
@login_required
def delete_parsed_content(content_id):
    content = ParsedContent.query.get_or_404(content_id)
    try:
        db.session.delete(content)
        db.session.commit()
        flash("Content deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting content: {str(e)}")
        flash("An error occurred while deleting content.", "error")
    return redirect(url_for("admin.admin"))
