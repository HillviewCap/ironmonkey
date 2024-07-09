from __future__ import annotations
import os
import asyncio
import uuid
from datetime import datetime
import bleach
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, current_app, abort, send_from_directory, redirect, url_for
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
from apscheduler.schedulers.background import BackgroundScheduler
import httpx

from logging_config import setup_logger
from models import db, User, SearchParams, RSSFeed, ParsedContent
from models.diffbot_model import Entity, EntityMention, EntityType, EntityUri, Category
from auth import init_auth, login, logout, register
from config import config
from rss_manager import rss_manager, fetch_and_parse_feed
from nlp_tagging import DiffbotClient, DatabaseHandler, Document
from ollama_api import OllamaAPI
from init_db import init_db

# Load environment variables
load_dotenv()

# Configure logging
logger = setup_logger('app', 'app.log')

# Initialize Flask application
app = None


def check_and_process_rss_feeds():
    with app.app_context():
        try:
            feeds = RSSFeed.query.all()
            for feed in feeds:
                asyncio.run(fetch_and_parse_feed(feed))
            logger.info(f"Checked and processed {len(feeds)} RSS feeds")
        except Exception as e:
            logger.error(f"Error in check_and_process_rss_feeds: {str(e)}")

async def start_check_empty_summaries():
    with app.app_context():
        try:
            empty_summaries = ParsedContent.query.filter(ParsedContent.summary.is_(None)).limit(10).all()
            for content in empty_summaries:
                summary = await app.ollama_api.generate("threat_intel_summary", content.content)
                content.summary = summary
            db.session.commit()
            logger.info(f"Processed {len(empty_summaries)} empty summaries")
        except Exception as e:
            logger.error(f"Error in start_check_empty_summaries: {str(e)}")

def render_error_page():
    try:
        return render_template("error.html", error="An error occurred. Please try again later."), 500
    except Exception as template_error:
        logger.error(f"Error rendering error template: {str(template_error)}", exc_info=True)
        return "An error occurred, and we couldn't render the error page. Please try again later.", 500

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

def create_app(config_name='default'):
    global app
    app = Flask(__name__, instance_relative_config=True, static_url_path='/static')
    app.ollama_api = OllamaAPI()
    if not app.ollama_api.check_connection():
        logger.error("Failed to connect to Ollama API. Exiting.")
        return None

    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(app.instance_path, 'threats.db')}"
    logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    try:
        db.init_app(app)
        CSRFProtect(app)
        init_auth(app)
        Migrate(app, db)

        login_manager = LoginManager()
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            try:
                return db.session.get(User, uuid.UUID(user_id))
            except ValueError:
                return None

        app.register_blueprint(rss_manager)

        with app.app_context():
            init_db(app)

        register_routes(app)
        setup_scheduler(app)

    except Exception as e:
        logger.error(f"Error during app initialization: {str(e)}")
        raise

    return app

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

        document = ParsedContent.get_document_by_id(content_id)
        if not document:
            return jsonify({"error": "Document not found"}), 404

        try:
            async with httpx.AsyncClient() as client:
                result = await diffbot_client.tag_content(document.content, client)
        
            # Use the existing db.session for processing the result
            db_handler.process_nlp_result(document, result, db.session)
            # Update the summary field
            document.summary = result.get("summary", {}).get("text")
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

        untagged_documents = (
            Document.query.filter(
                (Document.entities == None) & (Document.categories == None)
            )
            .limit(10)
            .all()
        )

        tagged_count = 0
        async with httpx.AsyncClient() as client:
            for document in untagged_documents:
                try:
                    result = await diffbot_client.tag_content(document.content, client)
                    db_handler.process_nlp_result(document, result)
                    document.summary = result.get("summary", {}).get("text")
                    tagged_count += 1
                except Exception as e:
                    current_app.logger.error(
                        f"Error tagging document ID {document.id}: {str(e)}"
                    )

        db.session.commit()
        return (
            jsonify(
                {
                    "message": f"Tagged {tagged_count} out of {len(untagged_documents)} documents"
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

        document = Document.query.get(content_id)
        if not document:
            return jsonify({"error": "Document not found"}), 404

        try:
            result = await diffbot_client.tag_content(document.content)
            db_handler.process_nlp_result(document, result)

            # Update the summary field
            document.summary = result.get("summary", {}).get("text")
            db.session.commit()

            return jsonify({"message": "Document tagged successfully"}), 200
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
        item = db.session.get(ParsedContent, item_id)
        if item is None:
            abort(404)
        return render_template("view_item.html", item=item)

    @app.cli.command("parse-feeds")
    def parse_feeds_command():
        """Parse all RSS feeds and store new content."""
        with app.app_context():
            asyncio.run(rss_manager.parse_feeds())
        print("Feeds parsed successfully.")


    @app.route("/summarize_content", methods=["POST"])
    @login_required
    async def summarize_content():
        content_id = request.json.get("content_id")
        if not content_id:
            current_app.logger.error("content_id is missing in the request")
            return jsonify({"error": "content_id is required"}), 400

        try:
            content_id = uuid.UUID(content_id)
            document = db.session.get(ParsedContent, content_id)
            if not document:
                current_app.logger.error(f"Document not found for id: {content_id}")
                return jsonify({"error": "Document not found"}), 404

            summary = await app.ollama_api.generate("threat_intel_summary", document.content)
            document.summary = summary
            db.session.commit()

            current_app.logger.info(f"Summary generated successfully for document id: {content_id}")
            return jsonify({"summary": summary}), 200
        except ValueError:
            current_app.logger.error(f"Invalid UUID format for content_id: {content_id}")
            return jsonify({"error": "Invalid content_id format"}), 400
        except Exception as e:
            current_app.logger.exception(f"Error summarizing content: {str(e)}")
            return jsonify({"error": f"Error summarizing content: {str(e)}"}), 500

    @app.route("/clear_all_summaries", methods=["POST"])
    @login_required
    def clear_all_summaries():
        try:
            ParsedContent.query.update({ParsedContent.summary: None})
            db.session.commit()
            return jsonify({"message": "All summaries have been cleared"}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error clearing summaries: {str(e)}")
            return jsonify({"error": "An error occurred while clearing summaries"}), 500

    # Initialize the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_and_process_rss_feeds, trigger="interval", minutes=30)
    scheduler.add_job(func=lambda: asyncio.run(start_check_empty_summaries()), trigger="interval", minutes=31)
    scheduler.start()
    logger.info("Scheduler started successfully")

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    return app

# Start the scheduler when the app starts
app = create_app('production')
if app is not None:
    with app.app_context():
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=check_and_process_rss_feeds, trigger="interval", minutes=30)
        scheduler.add_job(func=lambda: asyncio.run(start_check_empty_summaries()), trigger="interval", minutes=1)
        scheduler.start()
        logger.info("Scheduler started successfully")



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
    app = create_app('production')
    if app is not None:
        app.run(host='0.0.0.0', port=5000)
    else:
        print("Failed to create the application. Please check the logs for more information.")
def register_routes(app):
    @app.route("/")
    def index():
        current_app.logger.info("Entering index route")
        try:
            if current_user.is_authenticated:
                recent_items = (
                    db.session.query(ParsedContent)
                    .filter(ParsedContent.title.isnot(None), ParsedContent.description.isnot(None))
                    .order_by(ParsedContent.created_at.desc())
                    .limit(6)
                    .all()
                )
                return render_template("index.html", recent_items=recent_items)
            else:
                return redirect(url_for("login"))
        except Exception as e:
            current_app.logger.error(f"Error in index route: {str(e)}", exc_info=True)
            return render_error_page()

    app.add_url_rule("/", "index", index)
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

        document = ParsedContent.get_document_by_id(content_id)
        if not document:
            return jsonify({"error": "Document not found"}), 404

        try:
            async with httpx.AsyncClient() as client:
                result = await diffbot_client.tag_content(document.content, client)
        
            db_handler.process_nlp_result(document, result, db.session)
            document.summary = result.get("summary", {}).get("text")
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

        untagged_documents = (
            Document.query.filter(
                (Document.entities == None) & (Document.categories == None)
            )
            .limit(10)
            .all()
        )

        tagged_count = 0
        async with httpx.AsyncClient() as client:
            for document in untagged_documents:
                try:
                    result = await diffbot_client.tag_content(document.content, client)
                    db_handler.process_nlp_result(document, result)
                    document.summary = result.get("summary", {}).get("text")
                    tagged_count += 1
                except Exception as e:
                    current_app.logger.error(f"Error tagging document ID {document.id}: {str(e)}")

        db.session.commit()
        return jsonify({"message": f"Tagged {tagged_count} out of {len(untagged_documents)} documents"}), 200

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
        item = db.session.get(ParsedContent, item_id)
        if item is None:
            abort(404)
        return render_template("view_item.html", item=item)

    @app.cli.command("parse-feeds")
    def parse_feeds_command():
        """Parse all RSS feeds and store new content."""
        with app.app_context():
            asyncio.run(rss_manager.parse_feeds())
        print("Feeds parsed successfully.")

    @app.route("/summarize_content", methods=["POST"])
    @login_required
    async def summarize_content():
        content_id = request.json.get("content_id")
        if not content_id:
            current_app.logger.error("content_id is missing in the request")
            return jsonify({"error": "content_id is required"}), 400

        try:
            content_id = uuid.UUID(content_id)
            document = db.session.get(ParsedContent, content_id)
            if not document:
                current_app.logger.error(f"Document not found for id: {content_id}")
                return jsonify({"error": "Document not found"}), 404

            summary = await app.ollama_api.generate("threat_intel_summary", document.content)
            document.summary = summary
            db.session.commit()

            current_app.logger.info(f"Summary generated successfully for document id: {content_id}")
            return jsonify({"summary": summary}), 200
        except ValueError:
            current_app.logger.error(f"Invalid UUID format for content_id: {content_id}")
            return jsonify({"error": "Invalid content_id format"}), 400
        except Exception as e:
            current_app.logger.exception(f"Error summarizing content: {str(e)}")
            return jsonify({"error": f"Error summarizing content: {str(e)}"}), 500

    @app.route("/clear_all_summaries", methods=["POST"])
    @login_required
    def clear_all_summaries():
        try:
            ParsedContent.query.update({ParsedContent.summary: None})
            db.session.commit()
            return jsonify({"message": "All summaries have been cleared"}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error clearing summaries: {str(e)}")
            return jsonify({"error": "An error occurred while clearing summaries"}), 500

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')
def setup_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_and_process_rss_feeds, trigger="interval", minutes=30)
    scheduler.add_job(func=lambda: asyncio.run(start_check_empty_summaries()), trigger="interval", minutes=31)
    scheduler.start()
    logger.info("Scheduler started successfully")
