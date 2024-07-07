from flask import Flask
from models import db, User, RSSFeed, ParsedContent, Category, Threat
from models.diffbot_model import Document, Entity, EntityMention, EntityType, EntityUri, Category as DiffbotCategory
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def init_db():
    app = create_app()
    with app.app_context():
        # Import all models here to ensure they are registered with SQLAlchemy
        from models import User, RSSFeed, ParsedContent, Category, Threat
        from models.diffbot_model import Document, Entity, EntityMention, EntityType, EntityUri, Category as DiffbotCategory
        # Create all tables
        db.create_all()
        print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()
