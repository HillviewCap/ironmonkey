"""
This module contains Flask extensions used throughout the application.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.storage import MemoryStorage

# Initialize SQLAlchemy without binding it to a specific Flask application
db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

def init_extensions(app):
    """
    Initialize Flask extensions with the given Flask application.

    Args:
        app (Flask): The Flask application instance to initialize the extensions with.
    """
    db.init_app(app)
    limiter.init_app(app)
