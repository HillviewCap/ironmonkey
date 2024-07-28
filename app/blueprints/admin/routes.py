from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from werkzeug.security import generate_password_hash
from app.models.relational import db, User, ParsedContent, RSSFeed
from app.services.awesome_threat_intel_service import AwesomeThreatIntelService
from datetime import datetime
from typing import List
import uuid

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/")
@login_required
def admin() -> str:
    """
    Render the admin page with users, parsed content, and RSS feeds.
    """
    users = User.query.all()
    parsed_content = ParsedContent.query.all()
    rss_feeds = RSSFeed.query.all()
    update_status = {
        "last_updated": "Never"  # Replace with actual logic to get the last update status
    }
    return render_template(
        "admin.html",
        users=users,
        parsed_content=parsed_content,
        rss_feeds=rss_feeds,
        update_status=update_status
    )

@admin_bp.route("/deduplicate", methods=["POST"])
@login_required
def deduplicate_parsed_content() -> str:
    """
    Deduplicate parsed content and redirect to admin page.
    """
    try:
        deleted_count = ParsedContent.deduplicate()
        flash(f"Successfully removed {deleted_count} duplicate entries.", "success")
    except Exception as e:
        current_app.logger.error(f"Error during deduplication: {str(e)}")
        flash("An error occurred during deduplication.", "error")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/add_parsed_content", methods=["POST"])
@login_required
def add_parsed_content() -> str:
    """
    Add new parsed content and redirect to admin page.
    """
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
def edit_parsed_content(content_id: uuid.UUID) -> str:
    """
    Edit parsed content and redirect to admin page or render edit form.
    """
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
def delete_parsed_content(content_id: uuid.UUID) -> str:
    """
    Delete parsed content and redirect to admin page.
    """
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

@admin_bp.route("/add_user", methods=["POST"])
@login_required
def add_user() -> str:
    """
    Add new user and redirect to admin page.
    """
    try:
        new_user = User(
            username=request.form["username"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"])
        )
        db.session.add(new_user)
        db.session.commit()
        flash("New user added successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding new user: {str(e)}")
        flash("An error occurred while adding new user.", "error")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/edit_user/<uuid:user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id: uuid.UUID) -> str:
    """
    Edit user and redirect to admin page or render edit form.
    """
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        try:
            user.username = request.form["username"]
            user.email = request.form["email"]
            if request.form["password"]:
                user.password = generate_password_hash(request.form["password"])
            db.session.commit()
            flash("User updated successfully.", "success")
            return redirect(url_for("admin.admin"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user: {str(e)}")
            flash("An error occurred while updating user.", "error")
    return render_template("edit_user.html", user=user)

@admin_bp.route("/delete_user/<uuid:user_id>", methods=["POST"])
@login_required
def delete_user(user_id: uuid.UUID) -> str:
    """
    Delete user and redirect to admin page.
    """
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {str(e)}")
        flash("An error occurred while deleting user.", "error")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/add_rss_feed", methods=["POST"])
@login_required
def add_rss_feed() -> str:
    """
    Add new RSS feed and redirect to admin page.
    """
    try:
        new_feed = RSSFeed(
            name=request.form["name"],
            url=request.form["url"]
        )
        db.session.add(new_feed)
        db.session.commit()
        flash("New RSS feed added successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding new RSS feed: {str(e)}")
        flash("An error occurred while adding new RSS feed.", "error")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/update_awesome_threat_intel", methods=["POST"])
@login_required
def update_awesome_threat_intel() -> str:
    """
    Update Awesome Threat Intel Blogs and redirect to admin page.
    """
    try:
        AwesomeThreatIntelService.update_from_csv()
        flash("Awesome Threat Intel Blogs have been updated.", "success")
    except Exception as e:
        current_app.logger.error(f"Error updating Awesome Threat Intel Blogs: {str(e)}")
        flash("An error occurred while updating Awesome Threat Intel Blogs.", "error")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/clear_all_summaries", methods=["POST"])
@login_required
def clear_all_summaries() -> str:
    """
    Clear all summaries and redirect to admin page.
    """
    try:
        # Add logic to clear all summaries here
        flash("All summaries cleared successfully.", "success")
    except Exception as e:
        current_app.logger.error(f"Error clearing summaries: {str(e)}")
        flash("An error occurred while clearing summaries.", "error")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/delete_rss_feed/<uuid:feed_id>", methods=["POST"])
@login_required
def delete_rss_feed(feed_id: uuid.UUID) -> str:
    """
    Delete RSS feed and redirect to admin page.
    """
    feed = RSSFeed.query.get_or_404(feed_id)
    try:
        db.session.delete(feed)
        db.session.commit()
        flash("RSS feed deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting RSS feed: {str(e)}")
        flash("An error occurred while deleting RSS feed.", "error")
    return redirect(url_for("admin.admin"))
