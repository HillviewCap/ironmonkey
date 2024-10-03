from __future__ import annotations

from uuid import UUID
from typing import Tuple, Dict, Any, List

from flask import (
    Blueprint,
    request,
    jsonify,
    current_app,
    abort,
    render_template,
    flash,
    redirect,
    url_for,
)
from flask_login import login_required
from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Response

from app import db
from app.services.rss_feed_service import RSSFeedService
from app.services.parsed_content_service import ParsedContentService
from app.forms.rss_forms import AddRSSFeedForm, ImportCSVForm, EditRSSFeedForm
from app.models.relational.awesome_threat_intel_blog import AwesomeThreatIntelBlog
from app.models.relational.rss_feed import RSSFeed
from app.services.awesome_threat_intel_service import AwesomeThreatIntelService
from sqlalchemy.exc import IntegrityError

rss_manager_bp: Blueprint = Blueprint("rss_manager", __name__)
rss_feed_service: RSSFeedService = RSSFeedService()
parsed_content_service: ParsedContentService = ParsedContentService()


@rss_manager_bp.route("/rss/feeds")
@login_required
def get_rss_feeds() -> str:
    """
    Retrieve all RSS feeds and render the RSS manager page.

    Returns:
        str: Rendered HTML template for the RSS manager page.
    """
    feeds: List[RSSFeed] = rss_feed_service.get_all_feeds()
    form: AddRSSFeedForm = AddRSSFeedForm()
    csv_form: ImportCSVForm = ImportCSVForm()
    categories: List[str] = [
        blog.blog_category
        for blog in db.session.query(AwesomeThreatIntelBlog.blog_category).distinct()
    ]
    types: List[str] = [
        blog.type for blog in db.session.query(AwesomeThreatIntelBlog.type).distinct()
    ]
    return render_template(
        "rss_manager.html",
        feeds=feeds,
        form=form,
        csv_form=csv_form,
        categories=categories,
        types=types,
    )


@rss_manager_bp.route("/rss/feed", methods=["POST"])
@login_required
async def create_rss_feed() -> Tuple[Response, int]:
    """
    Create a new RSS feed.

    Returns:
        Tuple[Response, int]: A tuple containing a JSON response with the new feed data or error
        message, and an HTTP status code.

    Raises:
        BadRequest: If the request data is missing or invalid.
    """
    current_app.logger.info("Received request to create RSS feed")
    data: Dict[str, Any] = request.get_json()
    current_app.logger.debug(f"Received data: {data}")

    if not data:
        current_app.logger.error("No JSON data received")
        return jsonify({"error": "No JSON data received"}), 400
    if "url" not in data:
        current_app.logger.error("Missing URL in request data")
        return jsonify({"error": "Missing URL in request data"}), 400
    if "category" not in data:
        current_app.logger.error("Missing category in request data")
        return jsonify({"error": "Missing category in request data"}), 400

    try:
        current_app.logger.info(
            f"Attempting to create feed with URL: {data['url']} and category: {data['category']}"
        )
        new_feed: RSSFeed = await rss_feed_service.create_feed(data)
        current_app.logger.info(f"Created new feed: {new_feed.id}")

        current_app.logger.info(f"Attempting to parse new feed: {new_feed.id}")
        await rss_feed_service.parse_feed(new_feed.id)
        current_app.logger.info(f"Successfully parsed new feed: {new_feed.id}")

        current_app.logger.info("Fetching all feeds")
        feeds: List[RSSFeed] = rss_feed_service.get_all_feeds()
        current_app.logger.info(f"Fetched {len(feeds)} feeds")

        response_data = {
            "feed": new_feed.to_dict(),
            "feeds": [feed.to_dict() for feed in feeds],
        }
        current_app.logger.info(
            f"Sending response with new feed and {len(feeds)} total feeds"
        )
        return jsonify(response_data), 201
    except ValueError as e:
        current_app.logger.error(f"ValueError in create_rss_feed: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(
            f"Unexpected error in create_rss_feed: {str(e)}", exc_info=True
        )
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@rss_manager_bp.route("/rss/feed/<uuid:feed_id>", methods=["PUT"])
@login_required
def update_rss_feed(feed_id):
    """
    Update an existing RSS feed.

    Args:
        feed_id (uuid.UUID): The UUID of the RSS feed to update.

    Returns:
        tuple: A tuple containing a JSON response with the updated feed data or
               error message, and an HTTP status code.

    Raises:
        404: If the RSS feed with the given ID is not found.
    """
    data = request.get_json()
    try:
        updated_feed = rss_feed_service.update_feed(feed_id, data)
        if not updated_feed:
            abort(404, description="RSS feed not found")
        return jsonify(updated_feed.to_dict()), 200
    except Exception as e:
        current_app.logger.error(f"Error updating RSS feed: {str(e)}")
        return jsonify({"error": "Failed to update RSS feed"}), 500


@rss_manager_bp.route("/rss/feed/<uuid:feed_id>", methods=["POST", "DELETE"])
@login_required
def delete_rss_feed(feed_id):
    """
    Delete an RSS feed.

    Args:
        feed_id (uuid.UUID): The UUID of the RSS feed to delete.

    Returns:
        werkzeug.wrappers.Response: A redirect response to the RSS feed manager page.
    """
    try:
        rss_feed_service.delete_feed(feed_id)
        flash("RSS feed deleted successfully", "success")
    except Exception as e:
        current_app.logger.error(f"Error deleting RSS feed: {str(e)}")
        flash("Failed to delete RSS feed", "error")
    return redirect(url_for("rss_manager.get_rss_feeds"))


@rss_manager_bp.route("/update_awesome_threat_intel", methods=["POST"])
@login_required
def update_awesome_threat_intel():
    """
    Update Awesome Threat Intel Blogs and redirect to RSS feed manager page.

    This function triggers the update process for Awesome Threat Intel Blogs
    from a CSV file. It uses the AwesomeThreatIntelService to perform the update.

    Returns:
        werkzeug.wrappers.Response: A redirect response to the RSS feed manager page.

    Raises:
        Exception: If an error occurs during the update process, it's logged
                   and a flash message is displayed to the user.
    """
    try:
        AwesomeThreatIntelService.update_from_csv()
        flash("Awesome Threat Intel Blogs have been updated.", "success")
    except Exception as e:
        current_app.logger.error(f"Error updating Awesome Threat Intel Blogs: {str(e)}")
        flash("An error occurred while updating Awesome Threat Intel Blogs.", "error")
    return redirect(url_for("rss_manager.get_rss_feeds"))


@rss_manager_bp.route("/rss/feed/edit/<uuid:feed_id>", methods=["GET", "POST"])
@login_required
def edit_feed(feed_id):
    """
    Edit an existing RSS feed.

    This function handles both GET and POST requests for editing an RSS feed.
    For GET requests, it renders a form for editing. For POST requests, it
    processes the form submission and updates the feed.

    Args:
        feed_id (uuid.UUID): The UUID of the RSS feed to edit.

    Returns:
        str: Rendered HTML template for editing the feed (GET) or a redirect
             response to the RSS feed manager page (POST).

    Raises:
        404: If the RSS feed with the given ID is not found.

    Note:
        This function uses Flask-WTF for form handling and validation.
    """
    feed = RSSFeed.query.get_or_404(feed_id)
    form = EditRSSFeedForm(obj=feed)

    if form.validate_on_submit():
        form.populate_obj(feed)
        db.session.commit()
        flash("RSS feed updated successfully", "success")
        return redirect(url_for("rss_manager.get_rss_feeds"))

    return render_template("edit_rss_feed.html", form=form, feed=feed)


@rss_manager_bp.route("/get_awesome_threat_intel_blogs", methods=["GET"])
@login_required
def get_awesome_threat_intel_blogs():
    """
    Retrieve all Awesome Threat Intel Blogs.

    This function fetches Awesome Threat Intel Blogs from the database
    and returns them as a JSON response, formatted for GridJS.

    Returns:
        tuple: A tuple containing a JSON response with the blogs data or error
               message, and an HTTP status code.

    Note:
        - The function requires the user to be logged in.
        - Each blog is converted to a dictionary with specific fields.
        - The response includes whether each blog is already in RSS feeds.

    Raises:
        Exception: If an error occurs during the database query or JSON conversion,
                   it's logged and an error response is returned.
    """
    try:
        current_app.logger.info("Fetching all Awesome Threat Intel Blogs")
        blogs = AwesomeThreatIntelBlog.query.all()
        current_app.logger.info(f"Fetched {len(blogs)} blogs")

        # Fetch all RSS feed URLs in one query
        rss_feed_urls = set(
            feed.url for feed in RSSFeed.query.with_entities(RSSFeed.url).all()
        )

        blog_data = [{
            'blog': blog.blog,
            'blog_category': blog.blog_category,
            'type': blog.type,
            'blog_link': blog.blog_link,
            'feed_link': blog.feed_link,
            'is_in_rss_feeds': blog.feed_link in rss_feed_urls if blog.feed_link else False
        } for blog in blogs]

        current_app.logger.info(f"Returning {len(blog_data)} blogs")
        return jsonify(blog_data), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching awesome blogs: {str(e)}")
        return jsonify({"error": "Failed to fetch awesome blogs"}), 500

@rss_manager_bp.route("/add_to_rss_feeds", methods=["POST"])
@login_required
def add_to_rss_feeds():
    """
    Add a blog to RSS feeds.

    This function adds a blog from Awesome Threat Intel Blogs to the RSS feeds.

    Returns:
        tuple: A tuple containing a JSON response with a success or error message,
               and an HTTP status code.

    Note:
        - The function requires the user to be logged in.
        - It expects a JSON payload with a 'blog' field containing the blog name.

    Raises:
        BadRequest: If the request data is missing or invalid.
        IntegrityError: If there's a database integrity error (e.g., duplicate entry).
    """
    try:
        data = request.get_json()
        if not data or 'blog' not in data:
            raise BadRequest("Missing 'blog' in request data")

        blog_name = data['blog']
        blog = AwesomeThreatIntelBlog.query.filter_by(blog=blog_name).first()
        if not blog or not blog.feed_link:
            return jsonify({"error": "Blog not found or has no feed link"}), 404

        existing_feed = RSSFeed.query.filter_by(url=blog.feed_link).first()
        if existing_feed:
            return jsonify({"error": "Blog already exists in RSS feeds"}), 400

        new_feed = RSSFeed(url=blog.feed_link, category=blog.blog_category)
        db.session.add(new_feed)
        db.session.commit()
        return jsonify({"message": "Blog added to RSS feeds successfully"}), 200
    except BadRequest as e:
        current_app.logger.error(f"Bad request: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"Database integrity error: {str(e)}")
        return jsonify({"error": "Failed to add blog due to database constraint"}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error in add_to_rss_feeds: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
