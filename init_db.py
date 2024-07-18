import os
import requests
import feedparser
import hashlib
from flask import Flask
from models import db, User, RSSFeed, ParsedContent, Category, Threat, SearchParams, AwesomeThreatIntelBlog
from models.diffbot_model import Base as DiffbotBase, Document, Entity, EntityMention, EntityType, EntityUri, Category as DiffbotCategory
from models.alltools import Base as AllToolsBase, AllTools, AllToolsValues, AllToolsValuesNames
from models.allgroups import Base as AllGroupsBase, AllGroups, AllGroupsValues, AllGroupsValuesNames
from config import Config
from sqlalchemy import create_engine, text
from .update_databases import update_databases

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
        
        # Create tables for models defined with SQLAlchemy (diffbot_model, alltools, allgroups)
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        DiffbotBase.metadata.create_all(engine)
        AllToolsBase.metadata.create_all(engine)
        AllGroupsBase.metadata.create_all(engine)
        
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
            
            # Add the awesome_blog_id column to RSSFeed if it doesn't exist
            result = connection.execute(
                text("PRAGMA table_info(rss_feed)")
            )
            columns = {row[1]: row[2] for row in result.fetchall()}
            if "awesome_blog_id" not in columns:
                connection.execute(text("ALTER TABLE rss_feed ADD COLUMN awesome_blog_id VARCHAR(36)"))
        
        print(f"All database tables created and updated successfully in {app.instance_path}")
        
        # Update the databases with the latest data
        update_databases()

if __name__ == "__main__":
    init_db()
