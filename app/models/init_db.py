import os
import requests
import feedparser
import hashlib
from flask import Flask
from models import db, User, RSSFeed, ParsedContent, Category, Threat, SearchParams, AwesomeThreatIntelBlog
from models.relational.diffbot_model import Base as DiffbotBase, Document, Entity, EntityMention, EntityType, EntityUri, Category as DiffbotCategory
from models.relational.alltools import Base as AllToolsBase, AllTools, AllToolsValues, AllToolsValuesNames
from models.relational.allgroups import Base as AllGroupsBase, AllGroups, AllGroupsValues, AllGroupsValuesNames
from sqlalchemy import create_engine, text, inspect
from tgcapt import update_databases as update_databases_module
import json
import logging
from dotenv import load_dotenv

def create_app():
    load_dotenv()  # Load environment variables from .env file
    app = Flask(__name__)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Set the database URI from the environment variable
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    
    db.init_app(app)
    return app

def init_db(app):
    with app.app_context():
        database_url = f"sqlite:///{os.path.join(app.instance_path, 'threats.db')}"
        engine = create_engine(database_url)
        
        try:
            # Create tables for models defined with Flask-SQLAlchemy
            db.create_all()
            
            # Create tables for models defined with SQLAlchemy (diffbot_model)
            DiffbotBase.metadata.create_all(engine)

            # Check if AllTools and AllGroups tables exist, create them if they don't
            inspector = inspect(engine)
            if not inspector.has_table("alltools"):
                AllToolsBase.metadata.create_all(engine)
                print("AllTools tables created successfully.")
                logging.info("AllTools tables created successfully.")
            if not inspector.has_table("allgroups"):
                AllGroupsBase.metadata.create_all(engine)
                print("AllGroups tables created successfully.")
                logging.info("AllGroups tables created successfully.")

            # Verify that all required tables were created
            required_tables = ['user', 'alltools', 'alltools_values', 'alltools_values_names', 'allgroups', 'allgroups_values', 'allgroups_values_names']
            for table_name in required_tables:
                if not inspector.has_table(table_name):
                    print(f"Error: Table '{table_name}' was not created.")
                    logging.error(f"Table '{table_name}' was not created.")
                else:
                    print(f"Table '{table_name}' exists.")
                    logging.info(f"Table '{table_name}' exists.")
        except Exception as e:
            print(f"An error occurred while creating tables: {str(e)}")
            logging.error(f"An error occurred while creating tables: {str(e)}")
            return
        
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
            
            # Add missing columns to allgroups_values if they don't exist
            result = connection.execute(
                text("PRAGMA table_info(allgroups_values)")
            )
            columns = {row[1]: row[2] for row in result.fetchall()}
            missing_columns = {
                "motivation": "TEXT",
                "first_seen": "TEXT",
                "observed_sectors": "TEXT",
                "observed_countries": "TEXT",
                "tools": "TEXT",
                "operations": "TEXT",
                "sponsor": "TEXT",
                "counter_operations": "TEXT",
                "mitre_attack": "TEXT",
                "playbook": "TEXT"
            }
            for column, column_type in missing_columns.items():
                if column not in columns:
                    connection.execute(text(f"ALTER TABLE allgroups_values ADD COLUMN {column} {column_type}"))
                    print(f"Added column '{column}' to allgroups_values table.")
                    logging.info(f"Added column '{column}' to allgroups_values table.")
        
        print(f"All database tables created and updated successfully in {app.instance_path}")
        
        # Update the databases with the latest data
        try:
            logging.info("Starting update_databases()")
            json_data = update_databases_module.update_databases()
            logging.info("update_databases() completed successfully")
            logging.info(f"JSON data (first 1000 characters): {json.dumps(json_data)[:1000]}")
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error in update_databases: {str(e)}")
            logging.error(f"Error occurred at line {e.lineno}, column {e.colno}")
            logging.error(f"JSON snippet around error: {e.doc[max(0, e.pos-50):e.pos+50]}")
            print(f"An error occurred while parsing JSON: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error in update_databases: {str(e)}")
            print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    init_db()
