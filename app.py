from __future__ import annotations

import logging_config
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
from models import SearchParams, SearchResult, User, db, RSSFeed, Threat
from datetime import datetime
from flask_login import login_required, current_user
from auth import init_auth, login, logout, register
import os
from dotenv import load_dotenv
from werkzeug.exceptions import BadRequest
import bleach
from flask_wtf.csrf import CSRFProtect
from typing import List, Dict
import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/threats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db.init_app(app)
csrf = CSRFProtect(app)
init_auth(app)

app.route('/login', methods=['GET', 'POST'])(login)
app.route('/logout')(logout)
app.route('/register', methods=['GET', 'POST'])(register)

from rss_manager import rss_manager
app.register_blueprint(rss_manager)

def init_db():
    with app.app_context():
        logger.info("Starting database initialization")
        db.create_all()
        logger.info("Database initialization completed")

from auth import index

app.route('/')(index)

@app.cli.command("parse-feeds")
def parse_feeds_command():
    """Parse all RSS feeds and store new content."""
    with app.app_context():
        asyncio.run(rss_manager.parse_feeds())
    print("Feeds parsed successfully.")

@app.route('/search', methods=['POST'])
@login_required
def search() -> List[Dict[str, str | datetime]]:
    """
    Perform a search based on the provided search parameters.
    
    This function expects a JSON payload with search parameters, validates them,
    and then queries the database for matching Threat entries. It applies filters
    based on the search query, date range, source types, and keywords.
    
    Returns:
        List[Dict[str, str | datetime]]: A list of search results as dictionaries,
        where each dictionary represents a Threat object with its attributes.
    
    Raises:
        BadRequest: If the provided search parameters are invalid.
    """
    try:
        data = request.json
        search_params = SearchParams(**data)
    except ValueError as e:
        raise BadRequest(str(e))

    query = db.session.query(Threat)
    
    query = query.filter(
        db.or_(
            Threat.title.ilike(f'%{bleach.clean(search_params.query)}%'),
            Threat.description.ilike(f'%{bleach.clean(search_params.query)}%')
        )
    )

    if search_params.start_date:
        query = query.filter(Threat.date >= search_params.start_date)

    if search_params.end_date:
        query = query.filter(Threat.date <= search_params.end_date)

    if search_params.source_types:
        query = query.filter(Threat.source_type.in_([bleach.clean(st) for st in search_params.source_types]))

    if search_params.keywords:
        for keyword in search_params.keywords:
            query = query.filter(
                db.or_(
                    Threat.title.ilike(f'%{bleach.clean(keyword)}%'),
                    Threat.description.ilike(f'%{bleach.clean(keyword)}%')
                )
            )

    results = query.all()
    return jsonify([SearchResult(
        id=str(threat.id),
        title=threat.title,
        description=threat.description,
        source_type=threat.source_type,
        date=threat.date,
        url=threat.url
    ).dict() for threat in results])

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
