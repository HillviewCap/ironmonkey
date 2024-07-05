from __future__ import annotations

import os
import logging
import asyncio
from datetime import datetime
from typing import List
from flask_login import login_required

from flask import Flask, render_template, request, jsonify, current_app
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
import bleach
from dotenv import load_dotenv

import logging_config
from models import SearchParams, SearchResult, User, db, RSSFeed, Threat, ParsedContent
from auth import init_auth, login, logout, register
from config import Config
from rss_manager import rss_manager
from nlp_tagging import DiffbotClient, DatabaseHandler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    Config.init_app(app)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{os.path.join(app.instance_path, 'threats.db')}"
    )
    logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    db.init_app(app)
    csrf = CSRFProtect(app)
    init_auth(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(rss_manager)

    # Route registrations
    app.add_url_rule("/login", "login", login, methods=["GET", "POST"])
    app.add_url_rule("/logout", "logout", logout)
    app.add_url_rule("/register", "register", register, methods=["GET", "POST"])

    @app.route("/tag_content", methods=["POST"])
    @login_required
    async def tag_content():
        diffbot_api_key = os.getenv("DIFFBOT_API_KEY")
        if not diffbot_api_key:
            return jsonify({"error": "DIFFBOT_API_KEY not set"}), 500

        diffbot_client = DiffbotClient(diffbot_api_key)
        db_handler = DatabaseHandler(app.config["SQLALCHEMY_DATABASE_URI"])

        content_id = request.json.get("content_id")
        if not content_id:
            return jsonify({"error": "content_id is required"}), 400

        content = ParsedContent.query.get(content_id)
        if not content:
            return jsonify({"error": "Content not found"}), 404

        try:
            result = await diffbot_client.tag_content(content.content)
            db_handler.process_nlp_result(content, result)
            return jsonify({"message": "Content tagged successfully"}), 200
        except Exception as e:
            current_app.logger.error(f"Error tagging content: {str(e)}")
            return jsonify({"error": "Error tagging content"}), 500

    @app.route("/")
    def root():
        current_app.logger.info("Entering root route")
        try:
            from auth import index

            result = index()
            current_app.logger.info("index() function called successfully")
            return result
        except Exception as e:
            current_app.logger.error(f"Error in index route: {str(e)}", exc_info=True)
            return render_error_page()

    @app.route("/search", methods=["GET", "POST"])
    def search():
        form = FlaskForm()
        if request.method == "GET":
            return render_template("search.html", form=form)

        if form.validate_on_submit():
            return perform_search(form)

        return render_template("search.html", form=form)

    @app.cli.command("parse-feeds")
    def parse_feeds_command():
        """Parse all RSS feeds and store new content."""
        with app.app_context():
            asyncio.run(rss_manager.parse_feeds())
        print("Feeds parsed successfully.")

    return app


def init_db(app):
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error during database initialization: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during database initialization: {str(e)}")


def render_error_page():
    try:
        return (
            render_template(
                "error.html", error="An error occurred. Please try again later."
            ),
            500,
        )
    except Exception as template_error:
        logger.error(
            f"Error rendering error template: {str(template_error)}", exc_info=True
        )
        return (
            "An error occurred, and we couldn't render the error page. Please try again later.",
            500,
        )


def perform_search(form):
    page = request.args.get("page", 1, type=int)
    per_page = 10

    search_params = get_search_params(form)
    query = build_search_query(search_params)

    try:
        paginated_results = query.paginate(page=page, per_page=per_page)
        logger.info(f"Search completed. Total results: {paginated_results.total}")
    except Exception as e:
        logger.error(f"Error occurred during search: {str(e)}")
        return render_template(
            "search_results.html",
            error="An error occurred during the search. Please try again.",
        )

    return render_template(
        "search_results.html", results=paginated_results, search_params=search_params
    )


def get_search_params(form):
    return SearchParams(
        query=form.data.get("query", ""),
        start_date=(
            datetime.strptime(form.data.get("start_date"), "%Y-%m-%d").date()
            if form.data.get("start_date")
            else None
        ),
        end_date=(
            datetime.strptime(form.data.get("end_date"), "%Y-%m-%d").date()
            if form.data.get("end_date")
            else None
        ),
        source_types=form.data.get("source_types", []),
        keywords=(
            form.data.get("keywords", "").split(",")
            if form.data.get("keywords")
            else []
        ),
    )


def build_search_query(search_params):
    query = db.session.query(ParsedContent)

    query = query.filter(
        db.or_(
            ParsedContent.title.ilike(f"%{bleach.clean(search_params.query)}%"),
            ParsedContent.content.ilike(f"%{bleach.clean(search_params.query)}%"),
        )
    )

    if search_params.start_date:
        query = query.filter(ParsedContent.date >= search_params.start_date)

    if search_params.end_date:
        query = query.filter(ParsedContent.date <= search_params.end_date)

    if search_params.source_types:
        query = query.filter(
            ParsedContent.source_type.in_(
                [bleach.clean(st) for st in search_params.source_types]
            )
        )

    if search_params.keywords:
        for keyword in search_params.keywords:
            query = query.filter(
                db.or_(
                    ParsedContent.title.ilike(f"%{bleach.clean(keyword)}%"),
                    ParsedContent.content.ilike(f"%{bleach.clean(keyword)}%"),
                )
            )

    logger.debug(f"Final SQL query: {query}")
    return query


if __name__ == "__main__":
    app = create_app()
    init_db(app)
    app.run(debug=True)
