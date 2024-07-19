import os
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Load environment variables
load_dotenv()

migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'

def create_app(config_name='default'):
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(app.instance_path, 'threats.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'default')
    app.config['FLASK_PORT'] = int(os.environ.get('FLASK_PORT', 5000))
    app.config['DEBUG'] = os.environ.get('DEBUG', 'false').lower() == 'true'

    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    with app.app_context():
        db.create_all()

    @login.user_loader
    def load_user(user_id):
        from app.models.relational.user import User
        return User.query.get(user_id)

    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from app.models.relational import db
from app.utils.logging_config import setup_logger
from app.blueprints.main import main as main_bp
from app.blueprints.auth.routes import auth
from app.blueprints.rss_manager.routes import rss_manager
from app.blueprints.admin.routes import admin_bp
from app.blueprints.search.routes import search_bp
from app.blueprints.api.routes import api_bp
from app.utils.ollama_api import OllamaAPI
from config import config

def create_app(config_name='default'):
    app = Flask(__name__, instance_relative_config=True, static_url_path="/static")
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize extensions
    db.init_app(app)
    CSRFProtect(app)
    Migrate(app, db)

    # Setup logging
    setup_logger("app", "app.log")

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth)
    app.register_blueprint(rss_manager)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Initialize Ollama API
    app.ollama_api = OllamaAPI()

    return app
