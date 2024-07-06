from __future__ import annotations

import os
import logging
import asyncio
import uuid
from datetime import datetime
from typing import List

import bleach
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, current_app
from flask_migrate import Migrate
import shutil
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask import redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

import logging_config
from logging.handlers import TimedRotatingFileHandler
from models import SearchParams, db, ParsedContent, User
from flask_login import LoginManager, UserMixin
from auth import init_auth, login, logout, register
from config import Config
from rss_manager import rss_manager
from nlp_tagging import DiffbotClient, DatabaseHandler
from ollama_api import OllamaAPI
import asyncio
from ollama_api import OllamaAPI
import asyncio
import httpx

# Load environment variables
load_dotenv()

from summary_enhancer import SummaryEnhancer

async def enhance_summaries():
    """
    Check the parsed_content table for missing summaries,
    generate summaries using Ollama, and update the database.
    """
    app = current_app._get_current_object()
    ollama_api = OllamaAPI()
    enhancer = SummaryEnhancer(ollama_api)
    await enhancer.enhance_summaries()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.ollama_api = OllamaAPI()
    asyncio.run(app.ollama_api.check_connection())  # Ensure connection on startup
    app.config.from_object(Config)
    Config.init_app(app)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        logger.warning(f"Could not create instance folder at {app.instance_path}")

    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{os.path.join(app.instance_path, 'threats.db')}"
    )
    logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Set up logging
    log_file = os.path.join(app.instance_path, 'enhance_summaries.log')
    file_handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Enhance summaries startup')

    try:
        db.init_app(app)
        CSRFProtect(app)
        init_auth(app)
        Migrate(app, db)

        # Initialize LoginManager
        login_manager = LoginManager()
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            try:
                return db.session.get(User, uuid.UUID(user_id))
            except ValueError:
                return None

        # Register blueprints
        app.register_blueprint(rss_manager)

        # Route registrations
        @app.route("/")
        def index():
            current_app.logger.info("Entering index route")
            try:
                if current_user.is_authenticated:
                    # Fetch the 6 most recent ParsedContent items with non-null title and content
                    recent_items = (
                        ParsedContent.query
                        .filter(ParsedContent.title.isnot(None), ParsedContent.content.isnot(None))
                        .order_by(ParsedContent.created_at.desc())
                        .limit(6)
                        .all()
                    )
                    return render_template("index.html", recent_items=recent_items)
                else:
                    return redirect(url_for("login"))
            except Exception as e:
                current_app.logger.error(
                    f"Error in index route: {str(e)}", exc_info=True
                )
                return render_error_page()

        # Route registrations
        app.add_url_rule("/", "index", index)
        app.add_url_rule("/login", "login", login, methods=["GET", "POST"])
        app.add_url_rule("/logout", "logout", logout)
        app.add_url_rule("/register", "register", register, methods=["GET", "POST"])

        @app.cli.command("reinit-db")
        def reinit_db():
            """Reinitialize the database by removing existing migrations and creating new ones."""
            migrations_dir = os.path.join(app.root_path, 'migrations')
            if os.path.exists(migrations_dir):
                shutil.rmtree(migrations_dir)
                print("Removed existing migrations directory.")
            
            # Initialize migrations
            Migrate(app, db)
            with app.app_context():
                db.create_all()
            
            # Create a new migration
            os.system('flask db init')
            os.system('flask db migrate -m "Initial migration"')
            os.system('flask db upgrade')
            
            print("Database reinitialized successfully.")

    except Exception as e:
        logger.error(f"Error during app initialization: {str(e)}")
        raise

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

        content = ParsedContent.get_by_id(content_id)
        if not content:
            return jsonify({"error": "Content not found"}), 404

        try:
            # Detach the content object from its current session
            db.session.expunge(content)
        
            async with httpx.AsyncClient() as client:
                result = await diffbot_client.tag_content(content.content, client)
        
            # Use the existing db.session for processing the result
            db_handler.process_nlp_result(content, result, db.session)
            # Update the summary field
            content.summary = result.get("summary", {}).get("text")
            db.session.merge(content)
            db.session.commit()

            return jsonify({"message": "Content tagged successfully"}), 200
        except Exception as e:
            current_app.logger.error(f"Error tagging content: {str(e)}")
            return jsonify({"error": "Error tagging content"}), 500

    @app.route("/batch_tag_content", methods=["POST"])
    @login_required
    async def batch_tag_content():
        diffbot_api_key = os.getenv("DIFFBOT_API_KEY")
        if not diffbot_api_key:
            return jsonify({"error": "DIFFBOT_API_KEY not set"}), 500

        diffbot_client = DiffbotClient(diffbot_api_key)
        db_handler = DatabaseHandler(app.config["SQLALCHEMY_DATABASE_URI"])

        untagged_content = (
            ParsedContent.query.filter(
                (ParsedContent.entities == None) & (ParsedContent.categories == None)
            )
            .limit(10)
            .all()
        )

        tagged_count = 0
        async with httpx.AsyncClient() as client:
            for content in untagged_content:
                try:
                    result = await diffbot_client.tag_content(content.content, client)
                    db_handler.process_nlp_result(content, result)
                    content.summary = result.get("summary", {}).get("text")
                    tagged_count += 1
                except Exception as e:
                    current_app.logger.error(
                        f"Error tagging content ID {content.id}: {str(e)}"
                    )

        db.session.commit()
        return (
            jsonify(
                {
                    "message": f"Tagged {tagged_count} out of {len(untagged_content)} contents"
                }
            ),
            200,
        )
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

            # Update the summary field
            content.summary = result.get("summary", {}).get("text")
            db.session.commit()

            return jsonify({"message": "Content tagged successfully"}), 200
        except Exception as e:
            current_app.logger.error(f"Error tagging content: {str(e)}")
            return jsonify({"error": "Error tagging content"}), 500

    @app.route("/search", methods=["GET", "POST"])
    def search():
        form = FlaskForm()
        if request.method == "GET":
            return render_template("search.html", form=form)

        if form.validate_on_submit():
            return perform_search(form)

        return render_template("search.html", form=form)

    @app.route("/view/<uuid:item_id>")
    def view_item(item_id):
        item = ParsedContent.query.get_or_404(item_id)
        return render_template("view_item.html", item=item)

    @app.cli.command("parse-feeds")
    def parse_feeds_command():
        """Parse all RSS feeds and store new content."""
        with app.app_context():
            asyncio.run(rss_manager.parse_feeds())
        print("Feeds parsed successfully.")

    @app.cli.command("enhance-summaries")
    def enhance_summaries_command():
        """Enhance summaries for parsed content using Ollama."""
        with app.app_context():
            asyncio.run(enhance_summaries())
        print("Summaries enhanced successfully.")

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
