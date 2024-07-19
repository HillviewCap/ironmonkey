from __future__ import annotations

import os
import uuid
import hashlib
import csv
import html
import re
from io import TextIOWrapper
from datetime import datetime
from typing import TextIO, Tuple, List, Union, Optional

import httpx
import feedparser
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, Response
from flask_login import login_required
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired, URL
from sqlalchemy.exc import IntegrityError

from models import db, ParsedContent, RSSFeed, Category, AwesomeThreatIntelBlog
from nlp_tagging import DiffbotClient, DatabaseHandler
from jina_api import parse_content
from logging_config import setup_logger

def sanitize_html(text: str) -> str:
    """
    Remove HTML tags and unescape HTML entities.
    
    Args:
        text (str): The input text containing HTML.
    
    Returns:
        str: The sanitized text with HTML tags removed and entities unescaped.
    """
    # Unescape HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Create a separate logger for RSS manager
logger = setup_logger('rss_manager', 'rss_manager.log')
from ollama_api import OllamaAPI
from summary_enhancer import SummaryEnhancer

rss_manager = Blueprint("rss_manager", __name__)
csrf = CSRFProtect()

PER_PAGE_OPTIONS = [10, 25, 50, 100]

def init_app(app):
    with app.app_context():
        hashed_count = ParsedContent.hash_existing_articles()
        logger.info(f"Hashed {hashed_count} existing articles")

# Form classes
class RSSFeedForm(FlaskForm):
    url = StringField("RSS Feed URL", validators=[DataRequired(), URL()])
    category = SelectField(
        "Category",
        choices=[("News", "News"), ("Blog", "Blog"), ("Research", "Research")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Add RSS Feed")


class CSVUploadForm(FlaskForm):
    file = FileField("CSV File", validators=[DataRequired()])
    submit = SubmitField("Import Feeds")


class EditRSSFeedForm(FlaskForm):
    url = StringField("RSS Feed URL", validators=[DataRequired(), URL()])
    title = StringField("Title", validators=[DataRequired()])
    category = StringField("Category", validators=[DataRequired()])
    description = StringField("Description")
    last_build_date = StringField("Last Build Date")
    submit = SubmitField("Update Feed")


# Helper functions
from app.services.feed_parser_service import fetch_and_parse_feed


from typing import TextIO, Tuple, List

def process_csv_file(csv_file: TextIO) -> Tuple[int, int, List[str]]:
    """Process the uploaded CSV file and return import statistics."""
    imported_count, skipped_count = 0, 0
    errors: List[str] = []
    csv_file = TextIOWrapper(csv_file, encoding="utf-8")
    csv_reader = csv.reader(csv_file)

    # Skip the header row
    next(csv_reader, None)

    for row in csv_reader:
        if len(row) >= 1:
            url = row[0]
            category = row[1] if len(row) > 1 else "Uncategorized"
            try:
                title, description, last_build_date = RSSFeed.fetch_feed_info(url)
                new_feed = RSSFeed(
                    url=url,
                    title=title,
                    category=category,
                    description=description,
                    last_build_date=last_build_date,
                )
                db.session.add(new_feed)
                db.session.commit()
                imported_count += 1
                logger.info(f"RSS Feed added from CSV: {url}")
            except IntegrityError:
                db.session.rollback()
                skipped_count += 1
                logger.info(f"Skipped duplicate RSS Feed: {url}")
            except Exception as e:
                errors.append(f"Error processing RSS Feed {url}: {str(e)}")
                logger.error(
                    f"Error processing RSS Feed {url}: {str(e)}"
                )

    return imported_count, skipped_count, errors


# Route handlers
@rss_manager.route("/parse_feeds", methods=["POST"])
@login_required
async def parse_feeds():
    """Parse all RSS feeds in the database."""
    feeds = RSSFeed.query.all()
    success_count = 0
    error_count = 0
    for feed in feeds:
        try:
            await fetch_and_parse_feed(feed)
            success_count += 1
        except Exception as e:
            error_count += 1
            logger.error(f"Error parsing feed {feed.url}: {str(e)}", exc_info=True)
            # Don't flash for each error to avoid overwhelming the user
            continue

    if success_count > 0:
        flash(f"Successfully parsed {success_count} feed(s)", "success")
    if error_count > 0:
        flash(f"Failed to parse {error_count} feed(s). Check logs for details.", "warning")
    
    flash("Feed parsing completed", "info")
    return redirect(url_for("rss_manager.manage_rss"))


@rss_manager.route("/rss_manager", methods=["GET", "POST"])
@login_required
async def manage_rss() -> str:
    """Handle RSS feed management operations."""
    form = RSSFeedForm()
    csv_form = CSVUploadForm()
    awesome_blogs = AwesomeThreatIntelBlog.query.all()

    # Get unique categories and types for filters
    categories = sorted(set(blog.blog_category for blog in awesome_blogs if blog.blog_category))
    types = sorted(set(blog.type for blog in awesome_blogs if blog.type))

    # Get all RSS feeds
    rss_feeds = RSSFeed.query.all()
    rss_feed_urls = {feed.url for feed in rss_feeds}

    # Mark awesome blogs that are already in RSS feeds
    for blog in awesome_blogs:
        blog.is_in_rss_feeds = blog.feed_link in rss_feed_urls

    if form.validate_on_submit():
        url = form.url.data
        category = form.category.data
        try:
            existing_feed = RSSFeed.query.filter_by(url=url).first()
            if existing_feed:
                flash(f"RSS Feed with URL '{url}' already exists.", "warning")
            else:
                title, description, last_build_date = RSSFeed.fetch_feed_info(url)
                new_feed = RSSFeed(
                    url=url,
                    title=title if title else "Not available",
                    category=category,
                    description=description if description else "Not available",
                    last_build_date=last_build_date if last_build_date else None,
                )
                db.session.add(new_feed)
                db.session.commit()
                flash("RSS Feed added successfully!", "success")
                logger.info(f"RSS Feed added: {url}")

                await fetch_and_parse_feed(new_feed)
                flash("New feed parsed successfully!", "success")
        except IntegrityError:
            db.session.rollback()
            flash(f"RSS Feed with URL '{url}' already exists.", "warning")
            logger.warning(f"Attempted to add duplicate RSS Feed: {url}")
        except Exception as e:
            logger.error(f"Error adding or parsing RSS Feed: {str(e)}")
            flash(f"Error adding or parsing RSS Feed: {str(e)}", "error")
        return redirect(url_for("rss_manager.manage_rss"))

    if csv_form.validate_on_submit():
        csv_file = csv_form.file.data
        if csv_file.filename.endswith(".csv"):
            imported_count, skipped_count, errors = process_csv_file(csv_file)

            for error in errors:
                flash(error, "error")
            if imported_count > 0:
                flash(f"Successfully imported {imported_count} RSS feeds.", "success")
            if skipped_count > 0:
                flash(f"Skipped {skipped_count} duplicate RSS feeds.", "info")
            if imported_count == 0 and skipped_count == 0:
                flash("No valid feeds found in CSV file.", "warning")
        else:
            flash("Invalid file format. Please upload a CSV file.", "error")
        return redirect(url_for("rss_manager.manage_rss"))

    feeds = RSSFeed.query.all()
    delete_form = FlaskForm()
    return render_template(
        "rss_manager.html",
        form=form,
        csv_form=csv_form,
        feeds=feeds,
        delete_form=delete_form,
        awesome_blogs=awesome_blogs,
        categories=categories,
        types=types,
    )

@rss_manager.route("/add_awesome_feed/<uuid:blog_id>", methods=["POST"])
@login_required
async def add_awesome_feed(blog_id):
    """Add an RSS feed from the Awesome Threat Intel Blog list."""
    awesome_blog = AwesomeThreatIntelBlog.query.get_or_404(blog_id)
    
    if not awesome_blog.feed_link:
        return jsonify({"status": "error", "message": "This blog doesn't have an associated RSS feed."}), 400

    existing_feed = RSSFeed.query.filter_by(url=awesome_blog.feed_link).first()
    if existing_feed:
        return jsonify({"status": "exists", "message": f"RSS Feed with URL '{awesome_blog.feed_link}' already exists."}), 200

    try:
        title, description, last_build_date = RSSFeed.fetch_feed_info(awesome_blog.feed_link)
        new_feed = RSSFeed(
            url=awesome_blog.feed_link,
            title=title if title else awesome_blog.blog,
            category=awesome_blog.blog_category,
            description=description if description else "Not available",
            last_build_date=last_build_date if last_build_date else None,
            awesome_blog_id=awesome_blog.id
        )
        db.session.add(new_feed)
        db.session.commit()
        logger.info(f"Awesome Threat Intel Blog RSS Feed added: {awesome_blog.feed_link}")

        await fetch_and_parse_feed(new_feed)
        return jsonify({"status": "success", "message": "RSS Feed added and parsed successfully!"}), 200
    except Exception as e:
        logger.error(f"Error adding or parsing Awesome Threat Intel Blog RSS Feed: {str(e)}")
        return jsonify({"status": "error", "message": f"Error adding or parsing RSS Feed: {str(e)}"}), 500


@rss_manager.route("/parsed_content")
@login_required
def parsed_content():
    """Display parsed content from the database with pagination and search."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search_query = request.args.get("search", "")
    feed_id = request.args.get("feed_id")

    query = ParsedContent.query

    if feed_id:
        try:
            feed_id = uuid.UUID(feed_id)
            query = query.filter(ParsedContent.feed_id == feed_id)
        except ValueError:
            flash("Invalid feed ID", "error")
            return redirect(url_for("rss_manager.manage_rss"))

    if search_query:
        query = query.filter(
            (ParsedContent.content.ilike(f"%{search_query}%"))
            | (ParsedContent.url.ilike(f"%{search_query}%"))
            | (ParsedContent.title.ilike(f"%{search_query}%"))
            | (ParsedContent.description.ilike(f"%{search_query}%"))
        )

    total_results = query.count()
    query = query.order_by(ParsedContent.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items

    return render_template(
        "parsed_content.html",
        posts=posts,
        pagination=pagination,
        search_query=search_query,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
        total_results=total_results,
        feed_id=feed_id,
    )

@rss_manager.route("/parsed_content_data")
@login_required
def parsed_content_data():
    """Serve parsed content data as JSON for Grid.js."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search_query = request.args.get("search", "")
    feed_id = request.args.get("feed_id")

    query = ParsedContent.query

    if feed_id:
        try:
            feed_id = uuid.UUID(feed_id)
            query = query.filter(ParsedContent.feed_id == feed_id)
        except ValueError:
            return jsonify({"error": "Invalid feed ID"}), 400

    if search_query:
        query = query.filter(
            (ParsedContent.content.ilike(f"%{search_query}%"))
            | (ParsedContent.url.ilike(f"%{search_query}%"))
            | (ParsedContent.title.ilike(f"%{search_query}%"))
            | (ParsedContent.description.ilike(f"%{search_query}%"))
        )

    total = query.count()
    query = query.order_by(ParsedContent.created_at.desc())
    posts = query.paginate(page=page, per_page=per_page, error_out=False).items

    data = [
        {
            "id": str(post.id),
            "title": post.title,
            "url": post.url,
            "description": post.description,
            "pub_date": post.pub_date.isoformat() if isinstance(post.pub_date, datetime) else post.pub_date,
            "creator": post.creator,
            "summary": post.summary
        }
        for post in posts
    ]

    return jsonify({"data": data, "total": total})


@rss_manager.route("/tag_content/<uuid:post_id>", methods=["POST"])
@login_required
async def tag_content(post_id):
    """Tag a single piece of parsed content."""
    try:
        post = db.session.get(ParsedContent, post_id)
        if post is None:
            flash("Content not found", "error")
            return redirect(url_for("rss_manager.parsed_content"))

        diffbot_api_key = os.getenv("DIFFBOT_API_KEY")
        if not diffbot_api_key:
            raise ValueError("DIFFBOT_API_KEY not set")

        diffbot_client = DiffbotClient(diffbot_api_key)
        db_handler = DatabaseHandler(current_app.config["SQLALCHEMY_DATABASE_URI"])

        result = await diffbot_client.tag_content(post.content)
        db_handler.process_nlp_result(post, result)
        
        db.session.commit()
        flash("Content tagged successfully!", "success")
    except ValueError as e:
        flash(f"Error: {str(e)}", "error")
    except Exception as e:
        db.session.rollback()
        flash(f"Error tagging content: {str(e)}", "error")
    return redirect(url_for("rss_manager.parsed_content"))

@rss_manager.route("/add_parsed_content", methods=["POST"])
@login_required
def add_parsed_content():
    form = request.form
    new_content = ParsedContent(
        title=form['title'],
        url=form['url'],
        description=form['description'],
        date=datetime.strptime(form['date'], '%Y-%m-%d'),
        source_type=form['source_type']
    )
    db.session.add(new_content)
    db.session.commit()
    flash('New content added successfully', 'success')
    return redirect(url_for('admin'))


@rss_manager.route("/summarize_content/<uuid:post_id>", methods=["POST"])
@login_required
async def summarize_content(post_id):
    """Summarize a single piece of parsed content."""
    try:
        post = db.session.get(ParsedContent, post_id)
        if post is None:
            return jsonify({"status": "error", "message": "Content not found"}), 404

        summary_enhancer = SummaryEnhancer()
        success = await summary_enhancer.process_single_record(post)
        
        if success:
            return jsonify({"status": "success", "message": "Content summarized successfully!"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to summarize content"}), 500
    except Exception as e:
        logger.error(f"Error summarizing content: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": f"Error summarizing content: {str(e)}"}), 500


@rss_manager.route("/delete_feed/<uuid:feed_id>", methods=["POST"])
@login_required
def delete_feed(feed_id: uuid.UUID):
    """Delete an RSS feed from the database."""
    feed = RSSFeed.query.get_or_404(feed_id)
    try:
        # Delete associated parsed content
        ParsedContent.query.filter_by(feed_id=feed_id).delete()
        # Delete the feed
        db.session.delete(feed)
        db.session.commit()
        flash("RSS Feed and associated content deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting RSS Feed: {str(e)}")
        flash(f"Error deleting RSS Feed: {str(e)}", "error")
    return redirect(url_for("rss_manager.manage_rss"))


@rss_manager.route("/edit_feed/<uuid:feed_id>", methods=["GET", "POST"])
@login_required
def edit_feed(feed_id: uuid.UUID) -> Union[str, Response]:
    """Edit an existing RSS feed."""
    feed = RSSFeed.query.get_or_404(feed_id)
    form = EditRSSFeedForm(obj=feed)
    if form.validate_on_submit():
        feed.url = form.url.data
        feed.title = form.title.data
        feed.category = form.category.data
        feed.description = form.description.data
        feed.last_build_date = form.last_build_date.data
        try:
            db.session.commit()
            flash("RSS Feed updated successfully!", "success")
            logger.info(f"RSS Feed updated: {feed.url}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating RSS Feed: {str(e)}")
            flash(f"Error updating RSS Feed: {str(e)}", "error")
        return redirect(url_for("rss_manager.manage_rss"))
    return render_template("edit_rss_feed.html", form=form, feed=feed)
