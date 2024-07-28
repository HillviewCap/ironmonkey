from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configure your app here (e.g., load config, register blueprints, etc.)
    
    db.init_app(app)

    with app.app_context():
        from app.services.awesome_threat_intel_service import AwesomeThreatIntelService
        AwesomeThreatIntelService.initialize_awesome_feeds()

    return app
