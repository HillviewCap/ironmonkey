"""
This module initializes the Flask application and sets up all necessary configurations and extensions.
"""

import os
from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from dotenv import load_dotenv

from .extensions import db
from app.utils.logging_config import setup_logger
from app.blueprints.main.routes import bp as main_bp
from app.blueprints.auth.routes import bp as auth_bp
from app.blueprints.rss_manager.routes import rss_manager_bp
from app.blueprints.admin.routes import admin_bp
from app.blueprints.search.routes import search_bp
from app.blueprints.api.routes import api_bp
from app.utils.ollama_client import OllamaAPI
from app.services.scheduler_service import SchedulerService

# Configure logging
logger = setup_logger("app", "app.log")

migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(env=None):
    """
    Create and configure an instance of the Flask application.

    Args:
        env (str, optional): The environment to use for configuration. Defaults to None.

    Returns:
        Flask: The configured Flask application instance.
    """
    # Load environment variables
    load_dotenv()
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    app = Flask(__name__, instance_relative_config=True, static_url_path="/static", template_folder="templates")
    
    # Load configuration from environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'threats.db')}"
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'production')
    app.config['FLASK_PORT'] = int(os.getenv('FLASK_PORT', '5000'))
    app.config['RSS_CHECK_INTERVAL'] = int(os.getenv('RSS_CHECK_INTERVAL', 30))
    app.config['SUMMARY_CHECK_INTERVAL'] = int(os.getenv('SUMMARY_CHECK_INTERVAL', 60))
    app.config['SUMMARY_API_CHOICE'] = os.getenv('SUMMARY_API_CHOICE', 'groq')

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

    # Initialize Ollama API
    app.ollama_api = OllamaAPI()

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

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
        return User.get(user_id)

    return app
