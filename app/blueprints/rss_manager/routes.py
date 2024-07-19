from flask import Blueprint, render_template, request, jsonify, current_app, abort
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
from app.models.relational import RssFeed, RssEntry
from app.services.data_processing import import_awesome_threat_intel_blogs

rss_manager = Blueprint('rss_manager', __name__)

@rss_manager.route('/rss_feeds')
@login_required
def rss_feeds():
    feeds = RssFeed.query.all()
    return render_template('rss_feeds.html', feeds=feeds)

@rss_manager.route('/rss_entries')
@login_required
def rss_entries():
    entries = RssEntry.query.order_by(RssEntry.published.desc()).limit(100).all()
    return render_template('rss_entries.html', entries=entries)

@rss_manager.route('/import_awesome_threat_intel_blogs', methods=['POST'])
@login_required
def import_awesome_threat_intel_blogs_route():
    try:
        import_awesome_threat_intel_blogs()
        return jsonify({"message": "Import successful"}), 200
    except Exception as e:
        current_app.logger.error(f"Error importing awesome threat intel blogs: {str(e)}")
        return jsonify({"error": "Import failed"}), 500

@rss_manager.route('/add_rss_feed', methods=['POST'])
@login_required
def add_rss_feed():
    data = request.get_json()
    if not data or 'url' not in data:
        raise BadRequest("Missing URL in request data")

    try:
        new_feed = RssFeed(url=data['url'])
        db.session.add(new_feed)
        db.session.commit()
        return jsonify({"message": "RSS feed added successfully"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {str(e)}")
        return jsonify({"error": "Failed to add RSS feed"}), 500

@rss_manager.route('/delete_rss_feed/<int:feed_id>', methods=['DELETE'])
@login_required
def delete_rss_feed(feed_id):
    feed = RssFeed.query.get_or_404(feed_id)
    try:
        db.session.delete(feed)
        db.session.commit()
        return jsonify({"message": "RSS feed deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {str(e)}")
        return jsonify({"error": "Failed to delete RSS feed"}), 500
