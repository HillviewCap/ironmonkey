from flask import jsonify
from app import app
import logging

logger = logging.getLogger('app')

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}")
    return jsonify(error=str(e)), 500
