from flask import Flask
from models import db, User, RSSFeed, ParsedContent, Category, Threat, SearchParams
from models.diffbot_model import Base as DiffbotBase, Document, Entity, EntityMention, EntityType, EntityUri, Category as DiffbotCategory
from config import Config
from sqlalchemy import create_engine, text

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def init_db():
    app = create_app()
    with app.app_context():
        # Create tables for models defined with Flask-SQLAlchemy
        db.create_all()
        
        # Create tables for models defined with SQLAlchemy (diffbot_model)
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        DiffbotBase.metadata.create_all(engine)
        
        # Add the summary column to ParsedContent if it doesn't exist
        with engine.connect() as connection:
            result = connection.execute(
                text("PRAGMA table_info(parsed_content)")
            ).fetchall()
            columns = [row["name"] for row in result]
            if "summary" not in columns:
                connection.execute("ALTER TABLE parsed_content ADD COLUMN summary TEXT")
        
        print("All database tables created and updated successfully.")

if __name__ == "__main__":
    init_db()
