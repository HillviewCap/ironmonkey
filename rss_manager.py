from __future__ import annotations

import os
import uuid
import os
import hashlib
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from datetime import datetime
from models import db, ParsedContent
from nlp_tagging import DiffbotClient, DatabaseHandler
from nlp_tagging import DiffbotClient, DatabaseHandler
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired, URL
from typing import List, Union, Tuple
import csv
from io import TextIOWrapper
import uuid
from werkzeug.wrappers import Response
from sqlalchemy.exc import IntegrityError
import feedparser
import httpx
import asyncio
import html
import re

from models import db, RSSFeed, ParsedContent, Category, AwesomeThreatIntelBlog
from jina_api import parse_content
from logging_config import setup_logger

def sanitize_html(text):
    """Remove HTML tags and unescape HTML entities."""
    # Unescape HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Create a separate logger for RSS manager
logger = setup_logger('rss_manager', 'rss_manager.log')
from flask import current_app
from nlp_tagging import DiffbotClient, DatabaseHandler
from ollama_api import OllamaAPI

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
async def fetch_and_parse_feed(feed: RSSFeed) -> int:
    """Fetch and parse a single RSS feed."""
    new_entries_count = 0
    try:
        if current_app.debug:
            logger.debug(f"Starting to fetch and parse feed: {feed.url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(feed.url, timeout=30.0, headers=headers)
            response.raise_for_status()

            # Check if the URL has been redirected
            if response.url != feed.url:
                logger.info(f"Feed URL redirected from {feed.url} to {response.url}")
                feed.url = str(response.url)
                db.session.commit()

            feed_data = feedparser.parse(response.text)
            if current_app.debug:
                logger.debug(f"Parsed feed data for {feed.url}")
            for entry in feed_data.entries:
                try:
                    url = entry.link
                    title = entry.get('title', '')
                    if current_app.debug:
                        logger.debug(f"Processing entry: {url} - {title}")
                    art_hash = hashlib.sha256(f"{url}{title}".encode()).hexdigest()

                    existing_content = ParsedContent.query.filter_by(art_hash=art_hash).first()
                    if not existing_content:
                        if current_app.debug:
                            logger.debug(f"New content found: {url}")
                        parsed_content = await parse_content(url)
                        if parsed_content is not None:
                            new_content = ParsedContent(
                                content=parsed_content,
                                feed_id=feed.id,
                                url=url,
                                title=sanitize_html(title),
                                description=sanitize_html(entry.get('description', '')),
                                pub_date=entry.get('published', ''),
                                creator=sanitize_html(entry.get('author', '')),
                                art_hash=art_hash
                            )
                            db.session.add(new_content)
                            db.session.flush()  # This will assign the UUID to new_content

                            for category in entry.get('tags', []):
                                db_category = Category.create_from_feedparser(category, new_content.id)
                                db.session.add(db_category)
                            new_entries_count += 1
                            if current_app.debug:
                                logger.debug(f"Added new entry: {url}")
                        else:
                            logger.warning(f"Failed to parse content for URL: {url}")
                    else:
                        if current_app.debug:
                            logger.debug(f"Content already exists: {url}")
                except Exception as entry_error:
                    logger.error(f"Error processing entry {entry.get('link', 'Unknown')} from feed {feed.url}: {str(entry_error)}")
                    continue  # Continue with the next entry

            db.session.commit()
            logger.info(f"Feed: {feed.url} - Added {new_entries_count} new entries to database")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching feed {feed.url}: {e}")
        raise ValueError(f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}")
    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting {feed.url}: {e}")
        raise ValueError(f"Request error: {str(e)}")
    except httpx.TimeoutException as e:
        logger.error(f"Timeout occurred while fetching feed {feed.url}: {e}")
        raise ValueError(f"Timeout error: The request to {feed.url} timed out")
    except feedparser.FeedParserError as e:
        logger.error(f"FeedParser error occurred while parsing feed {feed.url}: {e}")
        raise ValueError(f"FeedParser error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred while parsing feed {feed.url}: {e}", exc_info=True)
        logger.error(f"new_entries_count: {new_entries_count}")
        logger.error(f"feed_data entries: {len(feed_data.entries)}")
        logger.error(f"Last processed entry: {url if 'url' in locals() else 'Unknown'}")
        logger.error(f"Last processed title: {title if 'title' in locals() else 'Unknown'}")
        raise ValueError(f"Unexpected error: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching feed {feed.url}: {e}")
        raise ValueError(f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}")
    except httpx.RequestError as e:
        logger.error(f"An error occurred while requesting {feed.url}: {e}")
        raise ValueError(f"Request error: {str(e)}")
    except httpx.TimeoutException as e:
        logger.error(f"Timeout occurred while fetching feed {feed.url}: {e}")
        raise ValueError(f"Timeout error: The request to {feed.url} timed out")
    except feedparser.FeedParserError as e:
        logger.error(f"FeedParser error occurred while parsing feed {feed.url}: {e}")
        raise ValueError(f"FeedParser error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error occurred while parsing feed {feed.url}: {e}", exc_info=True)
        raise ValueError(f"Unexpected error: {str(e)}")
    finally:
        return new_entries_count


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

    # Get unique categories and types for filters
    categories = sorted(set(blog.blog_category for blog in awesome_blogs if blog.blog_category))
    types = sorted(set(blog.type for blog in awesome_blogs if blog.type))

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
        flash("This blog doesn't have an associated RSS feed.", "warning")
        return redirect(url_for("rss_manager.manage_rss"))

    existing_feed = RSSFeed.query.filter_by(url=awesome_blog.feed_link).first()
    if existing_feed:
        flash(f"RSS Feed with URL '{awesome_blog.feed_link}' already exists.", "warning")
    else:
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
            flash("Awesome Threat Intel Blog RSS Feed added successfully!", "success")
            logger.info(f"Awesome Threat Intel Blog RSS Feed added: {awesome_blog.feed_link}")

            await fetch_and_parse_feed(new_feed)
            flash("New feed parsed successfully!", "success")
        except Exception as e:
            logger.error(f"Error adding or parsing Awesome Threat Intel Blog RSS Feed: {str(e)}")
            flash(f"Error adding or parsing RSS Feed: {str(e)}", "error")

    return redirect(url_for("rss_manager.manage_rss"))


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
            flash("Content not found", "error")
            return redirect(url_for("rss_manager.parsed_content"))

        ollama_api = current_app.ollama_api
        
        summary = await ollama_api.generate("threat_intel_summary", post.content)
        
        if summary:
            post.summary = summary
            db.session.commit()
            flash("Content summarized successfully!", "success")
        else:
            flash("Failed to summarize content", "error")
    except Exception as e:
        logger.error(f"Error summarizing content: {str(e)}", exc_info=True)
        flash(f"Error summarizing content: {str(e)}", "error")
    
    return redirect(url_for("rss_manager.parsed_content"))


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
