import os
import json
import warnings
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_migrate import Migrate

from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .extensions import init_extensions, db
from app.utils.logging_config import setup_logger
from app.utils.db_connection_manager import init_db_connection_manager
from app.utils.db_utils import setup_db_pool

def from_json(value):
    try:
        return json.loads(value)
    except:
        return None

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

from flask_login import login_required
from app.utils.ollama_client import OllamaAPI
from app.services.scheduler_service import SchedulerService
from app.services.apt_update_service import update_databases
from app.services.news_rollup_service import NewsRollupService
from app.cli.auto_tag_command import init_app as init_auto_tag_command

load_dotenv()

# Configure logging
logger = setup_logger("app", "app.log")

migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"
limiter = Limiter(key_func=get_remote_address)

def create_app(config_object=None):
    """
    Create and configure an instance of the Flask application.

    Args:
        config_object: The configuration object to use. If None, uses the default configuration.

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

    # Add this to ensure the app's logger uses the custom logger's handlers and level
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)
    if config_object is None:
        app.config.from_object("config.DevelopmentConfig")
    else:
        app.config.from_object(config_object)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Log configuration details
    logger.info(f"Debug mode set to: {app.config['DEBUG']}")
    logger.info(f"Instance path: {app.instance_path}")
    logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    logger.info(f"Flask port: {app.config['PORT']}")

    # Initialize extensions
    init_extensions(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Initialize Flask-Migrate
    migrate.init_app(app, db)

    # Register json_loads filter
    @app.template_filter("json_loads")
    def json_loads_filter(s):
        if not s:
            return []
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return []

    # Initialize database and connection manager
    with app.app_context():
        from app.models.relational.parsed_content import ParsedContent
        from app.models.relational.category import Category
        from app.models.relational.user import User
        from app.models.relational.rss_feed import RSSFeed
        from app.models.relational.content_tag import ContentTag
        
        # Reflect the current state of the database
        db.reflect()
        
        # Create or update tables
        db.create_all()
        
        # Check if the last_checked column exists in the RSSFeed table
        inspector = db.inspect(db.engine)
        if 'last_checked' not in [c['name'] for c in inspector.get_columns('rss_feed')]:
            # Add the last_checked column if it doesn't exist
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE rss_feed ADD COLUMN last_checked DATETIME"))
        
        # Check if the role column exists in the User table
        if 'role' not in [c['name'] for c in inspector.get_columns('user')]:
            # Add the role column if it doesn't exist
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE user ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user'"))
        
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

    # Initialize services
    def initialize_services():
        with app.app_context():
            # Initialize Ollama API
            app.ollama_api = OllamaAPI()

            # Setup scheduler
            app.scheduler = SchedulerService(app)
            app.scheduler.setup_scheduler()

            # Initialize Awesome Threat Intel Blogs
            from app.services.awesome_threat_intel_service import AwesomeThreatIntelService
            AwesomeThreatIntelService.cleanup_awesome_threat_intel_blog_ids()
            AwesomeThreatIntelService.initialize_awesome_feeds()

            # Update APT databases
            update_databases()
            logger.info("APT databases updated at application startup")

            # Update the Threat Group Cards JSON files
            from app.utils.threat_group_cards_updater import update_threat_group_cards
            update_threat_group_cards()
            logger.info("Threat Group Cards JSON files updated at application startup")

    # Call initialize_services after all blueprints are registered
    with app.app_context():
        initialize_services()

    # Initialize auto-tag command
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

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}")
        return jsonify(error=str(e)), 500

    @app.route('/generate_rollups', methods=['GET'])
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

    @app.route('/generate_rollup/<rollup_type>', methods=['GET'])
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

    return app
