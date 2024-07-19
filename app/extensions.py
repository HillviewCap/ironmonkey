"""
This module contains Flask extensions used throughout the application.
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy without binding it to a specific Flask application
db = SQLAlchemy()

def init_db(app):
    """
    Initialize the SQLAlchemy database with the given Flask application.

    Args:
        app (Flask): The Flask application instance to initialize the database with.
    """
    db.init_app(app)
