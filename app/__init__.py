"""
This module initializes the Flask application and sets up all necessary configurations and extensions.
"""

import os
from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

from .extensions import db
from app.utils.logging_config import setup_logger
from app.blueprints.main.routes import bp as main_bp
from app.blueprints.auth.routes import bp as auth_bp
from app.blueprints.rss_manager.routes import rss_manager_bp
from app.blueprints.admin.routes import admin_bp
from app.blueprints.search.routes import search_bp
from app.blueprints.api.routes import api_bp
from app.blueprints.parsed_content.routes import parsed_content_bp
from app.utils.ollama_client import OllamaAPI
from app.services.scheduler_service import SchedulerService

load_dotenv()

# Configure logging
logger = setup_logger("app", "app.log")

migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_object):
    """
    Create and configure an instance of the Flask application.

    Args:
        config_object: The configuration object to use.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True, static_url_path="/static", template_folder="templates")

    # Load the config
    app.config.from_object(config_object)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Log the instance path and database URI
    logger.debug(f"Instance path: {app.instance_path}")
    logger.debug(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(rss_manager_bp, url_prefix='/rss')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(parsed_content_bp, url_prefix='/content')

    # Initialize Ollama API
    app.ollama_api = OllamaAPI()

    with app.app_context():
        # Setup scheduler
        app.scheduler = SchedulerService(app)
        app.scheduler.setup_scheduler()

    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a user given the user ID.

        Args:
            user_id (str): The ID of the user to load.

        Returns:
            User: The User object if found, else None.
        """
        from app.models.relational.user import User
        from uuid import UUID
        try:
            # Convert the string to a UUID object
            uuid_obj = UUID(user_id)
            return User.query.get(uuid_obj)
        except (ValueError, AttributeError):
            return None

    return app
