"""
This module serves as the entry point for running the Flask application.

It handles the initialization of the application, database setup, and provides
a shell context for interactive sessions.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from app import create_app
from app.extensions import db
from app.models.relational.user import User
from config import get_config

# Check if .env file exists
if not os.path.exists('.env'):
    print("Error: .env file not found. Please create a .env file with the necessary environment variables.")
    sys.exit(1)

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = os.getenv("FLASK_ENV", "development")
config_obj = get_config(env)
app = create_app(config_obj)
logger.info("Application created")


@app.shell_context_processor
def make_shell_context():
    """
    Provide a shell context for Flask shell sessions.

    Returns:
        dict: A dictionary containing objects to be included in the shell context.
    """
    return {"db": db, "User": User}


def main():
    """
    Main function to run the Flask application.

    This function sets up the environment and starts the Flask development server.
    """
    try:
        # Use Flask's CLI configuration if available
        if os.getenv('FLASK_RUN_FROM_CLI') == 'true':
            logger.info("Running from Flask CLI")
            return
        
        # Otherwise, use the manual configuration
        app.run(
            host=app.config.get("HOST", "0.0.0.0"),
            port=int(app.config.get("FLASK_PORT", 5000)),
            use_reloader=app.config.get("USE_RELOADER", True),
            debug=app.config.get("DEBUG", True),
        )
        logger.info(f"Application started in debug mode: {app.debug}")
    except Exception as e:
        logger.error(f"Error starting the application: {e}")


if __name__ == "__main__":
    main()
