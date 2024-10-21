import os
import json
import warnings
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv
from flask import Flask, jsonify

from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from .extensions import init_extensions, limiter, db
from app.utils.logging_config import setup_logger
from app.utils.db_connection_manager import init_db_connection_manager
from app.utils.db_utils import setup_db_pool
from config import get_config

from app.utils.filters import from_json, json_loads_filter

# Suppress Pydantic deprecation warning
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
from app.blueprints.main.routes import bp as main_bp
from app.blueprints.auth.routes import bp as auth_bp
from app.blueprints.rss_manager.routes import rss_manager_bp
from app.blueprints.admin.routes import admin_bp
from app.blueprints.search.routes import search_bp
from app.blueprints.api.routes import api_bp
from app.blueprints.parsed_content import bp as parsed_content_bp
from app.blueprints.apt.routes import bp as apt_bp
from app.blueprints.dashboard import dashboard_bp

from flask_login import login_required
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.category import Category
from app.models.relational.user import User
from app.models.relational.rss_feed import RSSFeed
from app.models.relational.content_tag import ContentTag
from app.services.initializer import initialize_services
from app.services.apt_update_service import update_databases
from .error_handlers import error_bp
from app.cli.auto_tag_command import init_app as init_auto_tag_command

load_dotenv()

# Configure logging
logger = setup_logger("app", "app.log")

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

def create_app(config_name=None):
    """
    Create and configure an instance of the Flask application.

    Args:
        config_name: The name of the configuration to use. If None, uses the default configuration.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_url_path="/static",
        template_folder="templates",
    )

    app.jinja_env.filters['from_json'] = from_json

    # Use the configured logger in the app
    app.logger = logger
    app.config.from_object(get_config(config_name))

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Ensure database directory exists if using SQLite
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
        db_path = Path(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        db_dir = db_path.parent
        logger.info(f"Attempting to ensure database directory at: {db_dir}")
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database directory ensured at: {db_dir}")
        logger.info(f"Database directory ensured at: {db_dir}")
    else:
        logger.info("Non-SQLite database detected, skipping database directory creation.")
    logger.info(f"Debug mode set to: {app.config['DEBUG']}")
    logger.info(f"Instance path: {app.instance_path}")
    logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.info(f"Flask port: {app.config['PORT']}")

    # Initialize extensions
    csrf.init_app(app)
    login_manager.init_app(app)


    # Register filters
    app.jinja_env.filters['from_json'] = from_json
    app.add_template_filter(json_loads_filter, name='json_loads')

    # Initialize extensions
    init_extensions(app)

    # Initialize database and connection manager
    with app.app_context():
        from app.models.relational.parsed_content import ParsedContent
        from app.models.relational.category import Category
        from app.models.relational.user import User
        from app.models.relational.rss_feed import RSSFeed
        from app.models.relational.content_tag import ContentTag
        
        init_db_connection_manager(app)
        setup_db_pool()
        logger.info("Database tables created/updated and connection manager initialized")

    # Register blueprints
    blueprints = [
        (main_bp, None),
        (auth_bp, "/auth"),
        (rss_manager_bp, "/rss"),
        (admin_bp, "/admin"),
        (search_bp, "/search"),
        (api_bp, "/api"),
        (parsed_content_bp, "/parsed_content"),
        (apt_bp, "/apt"),
        (dashboard_bp, "/dashboard"),
    ]

    registered_blueprints = set()
    for blueprint, url_prefix in blueprints:
        if blueprint.name not in registered_blueprints:
            if blueprint.name in ['apt', 'parsed_content']:
                for endpoint, view_func in blueprint.view_functions.items():
                    blueprint.view_functions[endpoint] = login_required(view_func)
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            logger.info(
                f"Registered blueprint: {blueprint.name} with url_prefix: {url_prefix}"
            )
            registered_blueprints.add(blueprint.name)
        else:
            logger.warning(f"Blueprint {blueprint.name} already registered, skipping.")


    # Register error handler blueprint
    app.register_blueprint(error_bp)

    # Call initialize_services after all blueprints are registered
    with app.app_context():
        initialize_services()
    init_auto_tag_command(app)
    logger.info("Auto-tag command initialized")

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
            return db.session.get(User, uuid_obj)
        except (ValueError, AttributeError):
            return None

    # Check if there are any users in the database
    @app.before_request
    def check_for_users():
        from app.models.relational.user import User
        from flask import redirect, url_for, request

        # Exclude static files, auth routes, and API routes from this check
        if (request.endpoint and 
            'static' not in request.endpoint and 
            not request.endpoint.startswith('auth.') and
            not request.endpoint.startswith('api.')):
            user_count = db.session.query(User).count()
            if user_count == 0:
                return redirect(url_for('auth.register'))



    return app
