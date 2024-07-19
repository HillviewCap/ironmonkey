from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from app.extensions import db, init_db

migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if app.config['TESTING']:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    init_db(app)
    migrate.init_app(app, db)
    login.init_app(app)

    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    login.init_app(app)

    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

from app import models
