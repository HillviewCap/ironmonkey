from flask import Blueprint, jsonify
import logging

logger = logging.getLogger('app')

error_bp = Blueprint('errors', __name__)

@error_bp.app_errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify(error=str(e)), 500
