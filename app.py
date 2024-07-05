from __future__ import annotations

import logging_config
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import Pagination
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
from typing import List, Dict
import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
# Ensure the instance folder exists
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "threats.db")}'
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

@app.route('/search', methods=['GET'])
def search_page():
    return render_template('search.html')

@app.cli.command("parse-feeds")
def parse_feeds_command():
    """Parse all RSS feeds and store new content."""
    with app.app_context():
        asyncio.run(rss_manager.parse_feeds())
    print("Feeds parsed successfully.")

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of results per page

    if request.method == 'GET':
        query = request.args.get('query', '')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        source_types = request.args.getlist('source_types')
        keywords = request.args.get('keywords', '').split(',') if request.args.get('keywords') else []

        search_params = SearchParams(
            query=query,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
            source_types=source_types,
            keywords=keywords
        )
    else:  # POST
        try:
            data = request.json
            search_params = SearchParams(**data)
        except ValueError as e:
            raise BadRequest(str(e))

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

    paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)
    
    if request.method == 'GET':
        return render_template('search.html', results=paginated_results, search_params=search_params)
    else:  # POST
        return jsonify({
            'results': [SearchResult(
                id=str(content.id),
                title=content.title,
                description=content.content[:200] + '...' if len(content.content) > 200 else content.content,
                source_type=content.source_type,
                date=content.date,
                url=content.url
            ).dict() for content in paginated_results.items],
            'total': paginated_results.total,
            'pages': paginated_results.pages,
            'current_page': page
        })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
