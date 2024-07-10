import os
import requests
import feedparser
import hashlib
from flask import Flask
from models import db, User, RSSFeed, ParsedContent, Category, Threat, SearchParams
from models.diffbot_model import Base as DiffbotBase, Document, Entity, EntityMention, EntityType, EntityUri, Category as DiffbotCategory
from config import Config
from sqlalchemy import create_engine, text

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Set the database path to be in the instance folder
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'iron_monkey.db')}"
    
    db.init_app(app)
    return app

def init_db(app=None):
    if app is None:
        app = create_app()
    
    with app.app_context():
        # Create tables for models defined with Flask-SQLAlchemy
        db.create_all()
        
        # Create tables for models defined with SQLAlchemy (diffbot_model)
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        DiffbotBase.metadata.create_all(engine)
        
        # Add the summary and art_hash columns to ParsedContent if they don't exist
        with engine.connect() as connection:
            result = connection.execute(
                text("PRAGMA table_info(parsed_content)")
            )
            columns = {row[1]: row[2] for row in result.fetchall()}
            if "summary" not in columns:
                connection.execute(text("ALTER TABLE parsed_content ADD COLUMN summary TEXT"))
            if "art_hash" not in columns:
                connection.execute(text("ALTER TABLE parsed_content ADD COLUMN art_hash VARCHAR(64)"))
            elif columns["art_hash"] != "VARCHAR(64)":
                connection.execute(text("ALTER TABLE parsed_content DROP COLUMN art_hash"))
                connection.execute(text("ALTER TABLE parsed_content ADD COLUMN art_hash VARCHAR(64)"))
        
        print(f"All database tables created and updated successfully in {app.instance_path}")

        # Run the category association fix
        fix_orphaned_categories(app)

def fix_orphaned_categories(app):
    with app.app_context():
        print("Starting category association fix...")
        
        # Step 1: Clear the category database
        Category.query.delete()
        db.session.commit()
        print("Cleared existing categories.")

        # Step 2: Re-associate categories
        parsed_contents = ParsedContent.query.all()
        for content in parsed_contents:
            feed = RSSFeed.query.get(content.feed_id)
            if feed:
                try:
                    # Fetch the feed data
                    response = requests.get(feed.url, timeout=30)
                    feed_data = feedparser.parse(response.text)
                    
                    # Find the matching entry
                    for entry in feed_data.entries:
                        entry_hash = hashlib.sha256(f"{entry.link}{entry.get('title', '')}".encode()).hexdigest()
                        if entry_hash == content.art_hash:
                            # Re-create categories for this content
                            for category in entry.get('tags', []):
                                db_category = Category.create_from_feedparser(category, content.id)
                                db.session.add(db_category)
                            break
                except Exception as e:
                    print(f"Error processing feed {feed.url}: {str(e)}")
                    continue

        db.session.commit()
        print("Category association fix completed.")

if __name__ == "__main__":
    init_db()
