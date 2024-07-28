from __future__ import annotations

from uuid import UUID
from typing import Tuple, Dict, Any, List
from typing import Tuple, Dict, Any, List

from flask import Blueprint, request, jsonify, current_app, abort, render_template, flash, redirect, url_for
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

rss_manager_bp: Blueprint = Blueprint('rss_manager', __name__)
rss_feed_service: RSSFeedService = RSSFeedService()
parsed_content_service: ParsedContentService = ParsedContentService()

@rss_manager_bp.route('/rss/feeds')
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
    categories: List[str] = [blog.blog_category for blog in db.session.query(AwesomeThreatIntelBlog.blog_category).distinct()]
    types: List[str] = [blog.type for blog in db.session.query(AwesomeThreatIntelBlog.type).distinct()]
    return render_template('rss_manager.html', feeds=feeds, form=form, csv_form=csv_form, categories=categories, types=types)

@rss_manager_bp.route('/rss/feed/<uuid:feed_id>')
@login_required
def get_rss_feed(feed_id: UUID) -> Tuple[Response, int]:
    """
    Retrieve a specific RSS feed by its ID.

    Args:
        feed_id (UUID): The UUID of the RSS feed to retrieve.

    Returns:
        Tuple[Response, int]: A tuple containing a JSON response with the feed data and HTTP status code.

    Raises:
        404: If the RSS feed with the given ID is not found.
    """
    feed: RSSFeed = rss_feed_service.get_feed_by_id(feed_id)
    if not feed:
        abort(404, description="RSS feed not found")
    return jsonify(feed.to_dict()), 200

@rss_manager_bp.route('/rss/feed', methods=['POST'])
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
    if 'url' not in data:
        current_app.logger.error("Missing URL in request data")
        return jsonify({"error": "Missing URL in request data"}), 400
    if 'category' not in data:
        current_app.logger.error("Missing category in request data")
        return jsonify({"error": "Missing category in request data"}), 400

    try:
        current_app.logger.info(f"Attempting to create feed with URL: {data['url']} and category: {data['category']}")
        new_feed: RSSFeed = await rss_feed_service.create_feed(data)
        current_app.logger.info(f"Created new feed: {new_feed.id}")
        
        current_app.logger.info(f"Attempting to parse new feed: {new_feed.id}")
        await rss_feed_service.parse_feed(new_feed.id)
        current_app.logger.info(f"Successfully parsed new feed: {new_feed.id}")
        
        current_app.logger.info("Fetching all feeds")
        feeds: List[RSSFeed] = rss_feed_service.get_all_feeds()
        current_app.logger.info(f"Fetched {len(feeds)} feeds")
        
        response_data = {"feed": new_feed.to_dict(), "feeds": [feed.to_dict() for feed in feeds]}
        current_app.logger.info(f"Sending response with new feed and {len(feeds)} total feeds")
        return jsonify(response_data), 201
    except ValueError as e:
        current_app.logger.error(f"ValueError in create_rss_feed: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error in create_rss_feed: {str(e)}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@rss_manager_bp.route('/feed/awesome', methods=['POST'])
@login_required
async def create_rss_feed_from_awesome() -> Tuple[Response, int]:
    """
    Create a new RSS feed from an Awesome Threat Intel Blog.

    This function handles the creation of a new RSS feed from an Awesome Threat Intel Blog ID.

    Returns:
        tuple: A tuple containing a JSON response with the new feed data or error
               message, and an HTTP status code.

    Raises:
        BadRequest: If the request data is missing or invalid.
    """
    data = request.get_json()
    if not data or 'blog_id' not in data:
        raise BadRequest("Missing blog_id in request data")

    try:
        blog_id = UUID(data['blog_id'])
        awesome_blog = AwesomeThreatIntelBlog.query.get(blog_id)
        if not awesome_blog:
            raise ValueError("Awesome Threat Intel Blog not found")

        feed_data = {
            'url': awesome_blog.feed_link,
            'category': awesome_blog.blog_category
        }
        new_feed = await rss_feed_service.create_feed(feed_data)

        feeds = rss_feed_service.get_all_feeds()
        return jsonify({'message': 'Awesome feed added successfully', 'feeds': [feed.to_dict() for feed in feeds]}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating RSS feed from Awesome Threat Intel Blog: {str(e)}")
        return jsonify({"error": "Failed to create RSS feed"}), 500

@rss_manager_bp.route('/rss/feed/<uuid:feed_id>', methods=['PUT'])
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

@rss_manager_bp.route('/rss/feed/<uuid:feed_id>', methods=['POST', 'DELETE'])
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
    return redirect(url_for('rss_manager.get_rss_feeds'))

@rss_manager_bp.route('/rss/parse/<uuid:feed_id>', methods=['POST'])
@login_required
async def parse_rss_feed(feed_id):
    """
    Parse an RSS feed.

    Args:
        feed_id (uuid.UUID): The UUID of the RSS feed to parse.

    Returns:
        tuple: A tuple containing a JSON response with the parsed content or
               error message, and an HTTP status code.
    """
    try:
        parsed_content = await rss_feed_service.parse_feed(feed_id)
        return jsonify({"message": "RSS feed parsed successfully", "parsed_content": [content.to_dict() for content in parsed_content]}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error parsing RSS feed: {str(e)}")
        return jsonify({"error": "Failed to parse RSS feed"}), 500

@rss_manager_bp.route('/rss/parsed_content/<uuid:feed_id>')
@login_required
def get_parsed_content(feed_id):
    """
    Retrieve parsed content for a specific RSS feed.

    Args:
        feed_id (uuid.UUID): The UUID of the RSS feed to get parsed content for.

    Returns:
        str: Rendered HTML template with the parsed content.
    """
    return render_template('parsed_content.html', feed_id=feed_id)

@rss_manager_bp.route('/rss/parsed_content_data/<uuid:feed_id>')
@login_required
def get_parsed_content_data(feed_id):
    """
    Retrieve parsed content data for a specific RSS feed.

    Args:
        feed_id (uuid.UUID): The UUID of the RSS feed to get parsed content for.

    Returns:
        json: JSON response with parsed content data.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    filters = request.args.to_dict()
    filters.pop('page', None)
    filters.pop('per_page', None)
    filters['feed_id'] = feed_id

    content, total = parsed_content_service.get_parsed_content(filters, page, per_page)
    
    return jsonify({
        'data': [item.to_dict() for item in content],
        'total': total
    })

@rss_manager_bp.route('/update_awesome_threat_intel', methods=['POST'])
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

@rss_manager_bp.route('/add_awesome_feed', methods=['POST'])
@login_required
async def add_awesome_feed():
    """
    Add an Awesome Threat Intel Blog as an RSS feed.

    This function handles the addition of an Awesome Threat Intel Blog to the user's RSS feeds.
    It checks if the blog exists, has a feed link, and is not already in the user's feeds.
    It then uses the rss_feed_service to create and parse the feed.

    Returns:
        tuple: A tuple containing a JSON response with the result of the operation
               and an HTTP status code.

    Raises:
        BadRequest: If the blog ID is missing or invalid.
        Exception: For any other unexpected errors during the process.
    """
    try:
        data = request.get_json()
        if not data or 'blog_id' not in data:
            raise BadRequest("Missing blog_id in request data")

        blog_id = data['blog_id']
        current_app.logger.debug(f"Received blog_id: {blog_id}")

        # Convert blog_id to UUID if it's a string
        if isinstance(blog_id, str):
            try:
                blog_id = UUID(blog_id)
            except ValueError as e:
                current_app.logger.error(f"Invalid blog_id format: {str(e)}")
                return jsonify({'error': 'Invalid blog_id format'}), 400

        current_app.logger.debug(f"Converted blog_id: {blog_id}")

        awesome_blog = AwesomeThreatIntelBlog.query.get(blog_id)
        if not awesome_blog:
            current_app.logger.error(f"Awesome blog not found for id: {blog_id}")
            return jsonify({'error': 'Awesome blog not found'}), 404

        if not awesome_blog.feed_link:
            current_app.logger.error(f"Blog {blog_id} does not have an RSS feed")
            return jsonify({'error': 'This blog does not have an RSS feed'}), 400

        existing_feed = RSSFeed.query.filter_by(url=awesome_blog.feed_link).first()
        if existing_feed:
            current_app.logger.info(f"Feed already exists for blog {blog_id}")
            return jsonify({'error': 'This feed already exists in your RSS feeds'}), 400

        feed_data = {
            'url': awesome_blog.feed_link,
            'category': awesome_blog.blog_category,
            'name': awesome_blog.blog
        }
        new_feed = await rss_feed_service.create_feed(feed_data)
        current_app.logger.info(f"Created new feed: {new_feed.id}")

        # Parse the new feed
        try:
            await rss_feed_service.parse_feed(new_feed.id)
            current_app.logger.info(f"Successfully parsed new feed: {new_feed.id}")
        except Exception as parse_error:
            current_app.logger.error(f"Error parsing new feed: {str(parse_error)}")
            # Even if parsing fails, we keep the feed

        feeds = RSSFeed.query.all()
        return jsonify({'message': 'Awesome feed added successfully', 'feeds': [feed.to_dict() for feed in feeds]}), 200
    except BadRequest as e:
        current_app.logger.error(f"BadRequest error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except IntegrityError:
        current_app.logger.error("IntegrityError: Feed already exists")
        db.session.rollback()
        return jsonify({'error': 'This feed already exists in your RSS feeds'}), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error adding awesome feed: {str(e)}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred while adding the awesome feed'}), 500

@rss_manager_bp.route('/rss/feed/edit/<uuid:feed_id>', methods=['GET', 'POST'])
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
        flash('RSS feed updated successfully', 'success')
        return redirect(url_for('rss_manager.get_rss_feeds'))
    
    return render_template('edit_rss_feed.html', form=form, feed=feed)

@rss_manager_bp.route('/awesome_blogs', methods=['GET'])
@login_required
def get_awesome_blogs():
    """
    Retrieve all Awesome Threat Intel Blogs.

    This function fetches all Awesome Threat Intel Blogs from the database
    and returns them as a JSON response, formatted for GridJS.

    Returns:
        tuple: A tuple containing a JSON response with the blogs data or error
               message, and an HTTP status code.

    Note:
        - The function requires the user to be logged in.
        - It uses the AwesomeThreatIntelBlog model to fetch the data.
        - Each blog is converted to a dictionary using the to_dict() method.
        - The response includes the blog information.

    Raises:
        Exception: If an error occurs during the database query or JSON conversion,
                   it's logged and an error response is returned.
    """
    try:
        blogs = AwesomeThreatIntelBlog.query.all()
        
        # Fetch all RSS feed URLs in one query
        rss_feed_urls = set(feed.url for feed in RSSFeed.query.with_entities(RSSFeed.url).all())
        
        blog_data = []
        for blog in blogs:
            blog_dict = blog.to_dict()
            blog_dict['is_in_rss_feeds'] = blog.feed_link in rss_feed_urls if blog.feed_link else False
            blog_data.append(blog_dict)

        return jsonify(blog_data), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching awesome blogs: {str(e)}")
        return jsonify({"error": "Failed to fetch awesome blogs"}), 500
