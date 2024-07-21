"""
This module serves as the entry point for running the Flask application.

It handles the initialization of the application, database setup, and provides
a shell context for interactive sessions.
"""

import os
import logging
from dotenv import load_dotenv
from app import create_app
from app.extensions import db
from app.models.relational.user import User
from app.models.init_db import init_db
from config import get_config

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = os.getenv('FLASK_ENV', 'development')
config_obj = get_config(env)
app = create_app(config_obj)
logger.info("Application created")

with app.app_context():
    try:
        init_db(app)  # Initialize the database within the application context
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing the database: {e}")

@app.shell_context_processor
def make_shell_context():
    """
    Provide a shell context for Flask shell sessions.

    Returns:
        dict: A dictionary containing objects to be included in the shell context.
    """
    return {'db': db, 'User': User}

def main():
    """
    Main function to run the Flask application.

    This function sets up the environment and starts the Flask development server.
    """
    try:
        # Set debug mode explicitly
        app.debug = True
        app.run(
            host='0.0.0.0',
            port=app.config['FLASK_PORT'],
            use_reloader=True
        )
        logger.info("Application started in debug mode")
    except Exception as e:
        logger.error(f"Error starting the application: {e}")

if __name__ == '__main__':
    main()
