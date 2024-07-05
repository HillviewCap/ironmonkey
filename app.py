from __future__ import annotations

import logging_config
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
from models import SearchParams, SearchResult, User, db, RSSFeed, Threat, ParsedContent
from datetime import datetime, date
from flask_login import login_required, current_user
from auth import init_auth, login, logout, register
import os
from dotenv import load_dotenv
from werkzeug.exceptions import BadRequest
import bleach
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm
from typing import List, Dict
import httpx
import asyncio
import logging
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
from config import Config

app.config.from_object(Config)
Config.init_app(app)

# Log the database URI and file path
logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
logger.info(f"Database file path: {db_path}")

try:
    db.init_app(app)
    logger.info("SQLAlchemy initialized successfully")
except Exception as e:
    logger.error(f"Error initializing SQLAlchemy: {str(e)}")

csrf = CSRFProtect(app)
init_auth(app)
migrate = Migrate(app, db)

# Check if the database file exists and is accessible
if os.path.exists(db_path):
    logger.info(f"Database file exists at {db_path}")
    if os.access(db_path, os.R_OK | os.W_OK):
        logger.info("Database file is readable and writable")
    else:
        logger.error("Database file exists but is not accessible (check permissions)")
else:
    logger.warning(f"Database file does not exist at {db_path}")

app.route('/login', methods=['GET', 'POST'])(login)
app.route('/logout')(logout)
app.route('/register', methods=['GET', 'POST'])(register)

from rss_manager import rss_manager
app.register_blueprint(rss_manager)

def init_db():
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    logger.info(f"Database path: {db_path}")
    if os.path.exists(db_path):
        logger.info("Database already exists, skipping initialization")
    else:
        logger.info("Database does not exist, creating it")
        try:
            with app.app_context():
                logger.info("Starting database initialization")
                db.create_all()
                logger.info("Database initialization completed")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error during database initialization: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during database initialization: {str(e)}")

try:
    init_db()  # Call init_db() to create tables if they don't exist
    logger.info("Database initialization function completed")
except Exception as e:
    logger.error(f"Error during database initialization: {str(e)}")

from auth import index
from flask import current_app

@app.route('/')
def root():
    current_app.logger.info("Entering root route")
    try:
        current_app.logger.debug("Calling index() function")
        result = index()
        current_app.logger.info("index() function called successfully")
        return result
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}", exc_info=True)
        try:
            current_app.logger.debug("Attempting to render error.html")
            return render_template('error.html', error="An error occurred. Please try again later."), 500
        except Exception as template_error:
            current_app.logger.error(f"Error rendering error template: {str(template_error)}", exc_info=True)
            return "An error occurred, and we couldn't render the error page. Please try again later.", 500

@app.route('/search', methods=['GET'])
def search_page():
    form = FlaskForm()
    return render_template('search.html', form=form)

@app.cli.command("parse-feeds")
def parse_feeds_command():
    """Parse all RSS feeds and store new content."""
    with app.app_context():
        asyncio.run(rss_manager.parse_feeds())
    print("Feeds parsed successfully.")

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    logger.info(f"Search request received. Method: {request.method}")
    
    form = FlaskForm()
    
    if request.method == 'GET':
        logger.info("Rendering search.html template")
        return render_template('search.html', form=form)
    
    if form.validate_on_submit():
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of results per page

        query = request.form.get('query', '')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    source_types = request.form.getlist('source_types')
    keywords = request.form.get('keywords', '').split(',') if request.form.get('keywords') else []

    logger.debug(f"Search parameters: query={query}, start_date={start_date}, end_date={end_date}, "
                 f"source_types={source_types}, keywords={keywords}")

    search_params = SearchParams(
        query=query,
        start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
        end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
        source_types=source_types,
        keywords=keywords
    )

    query = db.session.query(ParsedContent)
    
    query = query.filter(
        db.or_(
            ParsedContent.title.ilike(f'%{bleach.clean(search_params.query)}%'),
            ParsedContent.content.ilike(f'%{bleach.clean(search_params.query)}%')
        )
    )

    if search_params.start_date:
        query = query.filter(ParsedContent.date >= search_params.start_date)

    if search_params.end_date:
        query = query.filter(ParsedContent.date <= search_params.end_date)

    if search_params.source_types:
        query = query.filter(ParsedContent.source_type.in_([bleach.clean(st) for st in search_params.source_types]))

    if search_params.keywords:
        for keyword in search_params.keywords:
            query = query.filter(
                db.or_(
                    ParsedContent.title.ilike(f'%{bleach.clean(keyword)}%'),
                    ParsedContent.content.ilike(f'%{bleach.clean(keyword)}%')
                )
            )

    logger.debug(f"Final SQL query: {query}")

    try:
        paginated_results = query.paginate(page=page, per_page=per_page)
        logger.info(f"Search completed. Total results: {paginated_results.total}")
    except Exception as e:
        logger.error(f"Error occurred during search: {str(e)}")
        return render_template('search_results.html', error="An error occurred during the search. Please try again.")

    return render_template('search_results.html', results=paginated_results, search_params=search_params)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
