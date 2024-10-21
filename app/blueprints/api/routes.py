"""
This module contains the API routes for the application.

It defines various endpoints for retrieving content, feeds, users,
and for summarizing content using the Ollama API.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.models.relational import db, ParsedContent, RSSFeed, User

try:
    from app.utils.ollama_client import OllamaAPI
except ImportError:
    OllamaAPI = None
from typing import Dict, Any

api_bp = Blueprint('api', __name__)

@api_bp.route('/content', methods=['GET'])
@login_required
def get_content() -> Dict[str, Any]:
    """
    Retrieve all parsed content.

    Returns:
        Dict[str, Any]: A JSON response containing all parsed content.
    """
    content = ParsedContent.query.all()
    return jsonify([c.to_dict() for c in content])

@api_bp.route('/feeds', methods=['GET'])
@login_required
def get_feeds() -> Dict[str, Any]:
    """
    Retrieve all RSS feeds.

    Returns:
        Dict[str, Any]: A JSON response containing all RSS feeds.
    """
    feeds = RSSFeed.query.all()
    return jsonify([f.to_dict() for f in feeds])

@api_bp.route('/users', methods=['GET'])
@login_required
def get_users() -> Dict[str, Any]:
    """
    Retrieve all users.

    Returns:
        Dict[str, Any]: A JSON response containing all users.
    """
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@api_bp.route('/summarize', methods=['POST'])
@login_required
def summarize_content() -> Dict[str, Any]:
    """
    Summarize the content for a given content_id using Ollama API.

    Expects a JSON payload with a 'content_id' key.

    Returns:
        Dict[str, Any]: A JSON response containing the generated summary or an error message.
    """
    content_id = request.json.get('content_id')
    if not content_id:
        return jsonify({'error': 'content_id is required'}), 400

    content = ParsedContent.query.get(content_id)
    if not content:
        return jsonify({'error': 'Content not found'}), 404

    ollama_api = OllamaAPI()
    summary = ollama_api.generate("threat_intel_summary", content.content)
    
    content.summary = summary
    db.session.commit()

    return jsonify({'summary': summary})
from flask import jsonify
from app.blueprints.api import bp

@bp.route('/example', methods=['GET'])
def example():
    """
    An example API route.

    Returns:
        dict: A JSON response with a message.
    """
    return jsonify({"message": "This is an example API route"})

# Add other API routes here
from flask import Blueprint, jsonify
from flask_login import login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.services.news_rollup_service import NewsRollupService
import logging

api_bp = Blueprint('api', __name__)
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger('app')

@api_bp.route('/generate_rollups', methods=['GET'])
@login_required
@limiter.limit("5 per minute")
async def generate_rollups():
    service = NewsRollupService()
    try:
        rollups = await service.generate_all_rollups()
        return jsonify(rollups), 200
    except Exception as e:
        logger.error(f"Error generating rollups: {str(e)}")
        return jsonify({"error": "Failed to generate rollups"}), 500

@api_bp.route('/generate_rollup/<rollup_type>', methods=['GET'])
@login_required
@limiter.limit("10 per minute")
async def generate_single_rollup(rollup_type):
    service = NewsRollupService()
    try:
        rollup = await service.generate_rollup(rollup_type)
        return jsonify({rollup_type: rollup}), 200
    except ValueError as e:
        logger.error(f"Invalid rollup type: {str(e)}")
        return jsonify({"error": "Invalid rollup type"}), 400
    except Exception as e:
        logger.error(f"Error generating rollup: {str(e)}")
        return jsonify({"error": "Failed to generate rollup"}), 500
