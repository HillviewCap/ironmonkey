from flask import Blueprint, request, jsonify, current_app, abort, render_template, flash, redirect, url_for
from flask_login import login_required
from werkzeug.exceptions import BadRequest
from app.services.rss_feed_service import RSSFeedService
from app.services.parsed_content_service import ParsedContentService
from app.utils.rss_validator import validate_rss_url, extract_feed_info
from app.forms.rss_forms import AddRSSFeedForm, ImportCSVForm
from app.models.relational.awesome_threat_intel_blog import AwesomeThreatIntelBlog

rss_manager_bp = Blueprint('rss_manager', __name__)
rss_feed_service = RSSFeedService()
parsed_content_service = ParsedContentService()

@rss_manager_bp.route('/rss/feeds')
@login_required
def get_rss_feeds():
    feeds = rss_feed_service.get_all_feeds()
    form = AddRSSFeedForm()
    csv_form = ImportCSVForm()
    return render_template('rss_manager.html', feeds=feeds, form=form, csv_form=csv_form)

@rss_manager_bp.route('/rss/feed/<uuid:feed_id>')
@login_required
def get_rss_feed(feed_id):
    feed = rss_feed_service.get_feed_by_id(feed_id)
    if not feed:
        abort(404, description="RSS feed not found")
    return jsonify(feed.to_dict()), 200

@rss_manager_bp.route('/rss/feed', methods=['POST'])
@login_required
def create_rss_feed():
    data = request.get_json()
    if not data or 'url' not in data:
        raise BadRequest("Missing URL in request data")

    if not validate_rss_url(data['url']):
        raise BadRequest("Invalid RSS feed URL")

    try:
        feed_info = extract_feed_info(data['url'])
        new_feed = rss_feed_service.create_feed({**data, **feed_info})
        return jsonify(new_feed.to_dict()), 201
    except Exception as e:
        current_app.logger.error(f"Error creating RSS feed: {str(e)}")
        return jsonify({"error": "Failed to create RSS feed"}), 500

@rss_manager_bp.route('/rss/feed/<uuid:feed_id>', methods=['PUT'])
@login_required
def update_rss_feed(feed_id):
    data = request.get_json()
    try:
        updated_feed = rss_feed_service.update_feed(feed_id, data)
        if not updated_feed:
            abort(404, description="RSS feed not found")
        return jsonify(updated_feed.to_dict()), 200
    except Exception as e:
        current_app.logger.error(f"Error updating RSS feed: {str(e)}")
        return jsonify({"error": "Failed to update RSS feed"}), 500

@rss_manager_bp.route('/rss/feed/<uuid:feed_id>', methods=['DELETE'])
@login_required
def delete_rss_feed(feed_id):
    try:
        if rss_feed_service.delete_feed(feed_id):
            return jsonify({"message": "RSS feed deleted successfully"}), 200
        else:
            abort(404, description="RSS feed not found")
    except Exception as e:
        current_app.logger.error(f"Error deleting RSS feed: {str(e)}")
        return jsonify({"error": "Failed to delete RSS feed"}), 500

@rss_manager_bp.route('/rss/parse/<uuid:feed_id>', methods=['POST'])
@login_required
def parse_rss_feed(feed_id):
    try:
        parsed_content = rss_feed_service.parse_feed(feed_id)
        return jsonify({"message": "RSS feed parsed successfully", "parsed_content": [content.to_dict() for content in parsed_content]}), 200
    except Exception as e:
        current_app.logger.error(f"Error parsing RSS feed: {str(e)}")
        return jsonify({"error": "Failed to parse RSS feed"}), 500

@rss_manager_bp.route('/rss/parsed_content/<uuid:feed_id>')
@login_required
def get_parsed_content(feed_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    filters = request.args.to_dict()
    filters.pop('page', None)
    filters.pop('per_page', None)
    filters['feed_id'] = feed_id

    content, total = parsed_content_service.get_parsed_content(filters, page, per_page)
    return render_template('parsed_content.html', content=content, total=total, page=page, per_page=per_page, feed_id=feed_id)

