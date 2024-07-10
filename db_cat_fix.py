import os
import requests
import feedparser
import hashlib
from flask import Flask
from models import db, RSSFeed, ParsedContent, Category
from config import Config
from logging_config import logger
from sqlalchemy.exc import SQLAlchemyError

def update_missing_hashes(app):
    with app.app_context():
        try:
            items_without_hash = ParsedContent.query.filter(ParsedContent.art_hash == None).all()
            total_items = len(items_without_hash)
            print(f"Found {total_items} items without hash.")
            updated_count = 0
            
            for item in items_without_hash:
                if item.link and item.title:
                    new_hash = hashlib.sha256(f"{item.link}{item.title}".encode()).hexdigest()
                    item.art_hash = new_hash
                    updated_count += 1
                    print(f"Updated item {item.id} with hash: {new_hash}")
                else:
                    print(f"Skipped item {item.id} due to missing link or title")
            
            db.session.commit()
            print(f"Updated {updated_count} out of {total_items} items with missing hashes.")
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"An error occurred while updating hashes: {str(e)}")
        
        # Double-check after update
        remaining_items = ParsedContent.query.filter(ParsedContent.art_hash == None).count()
        print(f"Remaining items without hash after update: {remaining_items}")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Set the database path to be in the instance folder, pointing to threats.db
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'threats.db')}"
    
    db.init_app(app)
    return app

def init_app(app):
    with app.app_context():
        db.create_all()  # This will create all tables defined in your models
        hashed_count = ParsedContent.hash_existing_articles()
        logger.info(f"Hashed {hashed_count} existing articles")

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
            feed = db.session.get(RSSFeed, content.feed_id)
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
    app = create_app()
    init_app(app)  # Initialize the database
    update_missing_hashes(app)  # Update missing hashes
    fix_orphaned_categories(app)
