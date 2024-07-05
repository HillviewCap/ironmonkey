from flask import Flask
from models import db, User, RSSFeed, ParsedContent, Entity, Uris, Type, EntityType, Mention, Location, Category, Sentiment, Topic
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()
