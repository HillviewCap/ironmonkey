import os
from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from dotenv import load_dotenv

from .extensions import db
from app.utils.logging_config import setup_logger
from app.blueprints.main import main as main_bp, init_app as init_main_bp
from app.blueprints.auth import auth
from app.blueprints.rss_manager.routes import rss_manager
from app.blueprints.admin.routes import admin_bp
from app.blueprints.search.routes import search_bp
from app.blueprints.api.routes import api_bp
from app.utils.ollama_api import OllamaAPI
from app.utils.scheduler import setup_scheduler

# Load environment variables
load_dotenv()

# Configure logging
logger = setup_logger("app", "app.log")

migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__, instance_relative_config=True, static_url_path="/static")
    
    # Load configuration from environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'production')
    app.config['FLASK_PORT'] = int(os.getenv('FLASK_PORT', 5000))
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
    app.register_blueprint(auth)
    app.register_blueprint(rss_manager)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Initialize Ollama API
    app.ollama_api = OllamaAPI()

    # Setup scheduler
    app.scheduler = setup_scheduler(app)

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.relational.user import User
        return User.query.get(user_id)

    return app
