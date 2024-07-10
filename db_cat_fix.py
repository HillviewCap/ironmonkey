import os
import requests
import feedparser
import hashlib
from flask import Flask
from models import db, RSSFeed, ParsedContent, Category
from config import Config

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
    app = create_app()
    fix_orphaned_categories(app)
