from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Union, Optional

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired, URL
from sqlalchemy.exc import IntegrityError
import uuid
from datetime import datetime

from app.models.relational import AwesomeThreatIntelBlog
from app.services.rss_feed_service import RSSFeedService
from app.services.parsed_content_service import ParsedContentService
from app.services.csv_import_service import process_csv_file
from logging_config import setup_logger
from summary_enhancer import SummaryEnhancer

# Create a separate logger for RSS manager
logger = setup_logger('rss_manager', 'rss_manager.log')

rss_manager = Blueprint("rss_manager", __name__)
csrf = CSRFProtect()
rss_feed_service = RSSFeedService()
parsed_content_service = ParsedContentService()

PER_PAGE_OPTIONS = [10, 25, 50, 100]

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

@rss_manager.route("/rss/feeds", methods=["GET"])
@login_required
def list_rss_feeds():
    """List all RSS feeds."""
    feeds = rss_feed_service.get_all_feeds()
    return jsonify([{
        "id": str(feed.id),
        "url": feed.url,
        "title": feed.title,
        "category": feed.category,
        "last_build_date": feed.last_build_date.isoformat() if feed.last_build_date else None
    } for feed in feeds]), 200

@rss_manager.route("/rss/feed/<uuid:feed_id>", methods=["GET"])
@login_required
def get_rss_feed(feed_id):
    """Get details of a specific RSS feed."""
    try:
        feed = rss_feed_service.get_feed_by_id(feed_id)
        if not feed:
            return jsonify({"error": "Feed not found"}), 404
        return jsonify({
            "id": str(feed.id),
            "url": feed.url,
            "title": feed.title,
            "category": feed.category,
            "description": feed.description,
            "last_build_date": feed.last_build_date.isoformat() if feed.last_build_date else None
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving RSS feed: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@rss_manager.route("/rss/feed/<uuid:feed_id>", methods=["DELETE"])
@login_required
def delete_rss_feed(feed_id):
    """Delete an RSS feed."""
    try:
        rss_feed_service.delete_feed(feed_id)
        return jsonify({"message": "RSS feed deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error deleting RSS feed: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@rss_manager.route("/rss_manager", methods=["GET", "POST"])
@login_required
async def manage_rss() -> str:
    """Handle RSS feed management operations."""
    form = RSSFeedForm()
    csv_form = CSVUploadForm()
    awesome_blogs = AwesomeThreatIntelBlog.query.all()

    categories = sorted(set(blog.blog_category for blog in awesome_blogs if blog.blog_category))
    types = sorted(set(blog.type for blog in awesome_blogs if blog.type))

    rss_feeds = rss_feed_service.get_all_feeds()
    rss_feed_urls = {feed.url for feed in rss_feeds}

    for blog in awesome_blogs:
        blog.is_in_rss_feeds = blog.feed_link in rss_feed_urls

    if form.validate_on_submit():
        url = form.url.data
        category = form.category.data
        try:
            new_feed = rss_feed_service.create_feed({"url": url, "category": category})
            flash("RSS Feed added successfully!", "success")
            logger.info(f"RSS Feed added: {url}")

            await rss_feed_service.parse_feed(new_feed.id)
            flash("New feed parsed successfully!", "success")
        except IntegrityError:
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

    feeds = rss_feed_service.get_all_feeds()
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

    existing_feed = rss_feed_service.get_feed_by_url(awesome_blog.feed_link)
    if existing_feed:
        return jsonify({"status": "exists", "message": f"RSS Feed with URL '{awesome_blog.feed_link}' already exists."}), 200

    try:
        new_feed = rss_feed_service.create_feed({
            "url": awesome_blog.feed_link,
            "title": awesome_blog.blog,
            "category": awesome_blog.blog_category,
            "awesome_blog_id": awesome_blog.id
        })
        logger.info(f"Awesome Threat Intel Blog RSS Feed added: {awesome_blog.feed_link}")

        await rss_feed_service.parse_feed(new_feed.id)
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

    filters = {}
    if feed_id:
        try:
            filters["feed_id"] = uuid.UUID(feed_id)
        except ValueError:
            flash("Invalid feed ID", "error")
            return redirect(url_for("rss_manager.manage_rss"))

    if search_query:
        filters["search"] = search_query

    content, total = parsed_content_service.get_parsed_content(filters, page, per_page)

    return render_template(
        "parsed_content.html",
        posts=content,
        pagination={"page": page, "per_page": per_page, "total": total},
        search_query=search_query,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
        total_results=total,
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

    filters = {}
    if feed_id:
        try:
            filters["feed_id"] = uuid.UUID(feed_id)
        except ValueError:
            return jsonify({"error": "Invalid feed ID"}), 400

    if search_query:
        filters["search"] = search_query

    content, total = parsed_content_service.get_parsed_content(filters, page, per_page)

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
        for post in content
    ]

    return jsonify({"data": data, "total": total})

@rss_manager.route("/tag_content/<uuid:post_id>", methods=["POST"])
@login_required
async def tag_content(post_id):
    """Tag a single piece of parsed content."""
    try:
        post = parsed_content_service.get_content_by_id(post_id)
        if post is None:
            flash("Content not found", "error")
            return redirect(url_for("rss_manager.parsed_content"))

        # Implement tagging logic here
        # This might involve calling an NLP service or using a local model
        # For now, we'll just add a placeholder tag
        post.tags = ["placeholder_tag"]
        parsed_content_service.update_parsed_content(post_id, {"tags": post.tags})
        
        flash("Content tagged successfully!", "success")
    except Exception as e:
        logger.error(f"Error tagging content: {str(e)}")
        flash(f"Error tagging content: {str(e)}", "error")
    return redirect(url_for("rss_manager.parsed_content"))

@rss_manager.route("/add_parsed_content", methods=["POST"])
@login_required
def add_parsed_content():
    form = request.form
    new_content = parsed_content_service.create_parsed_content({
        "title": form['title'],
        "url": form['url'],
        "description": form['description'],
        "pub_date": datetime.strptime(form['date'], '%Y-%m-%d'),
        "source_type": form['source_type']
    })
    flash('New content added successfully', 'success')
    return redirect(url_for('admin'))

@rss_manager.route("/summarize_content/<uuid:post_id>", methods=["POST"])
@login_required
async def summarize_content(post_id):
    """Summarize a single piece of parsed content."""
    try:
        post = parsed_content_service.get_content_by_id(post_id)
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

@rss_manager.route("/edit_feed/<uuid:feed_id>", methods=["GET", "POST"])
@login_required
def edit_feed(feed_id: uuid.UUID) -> Union[str, Response]:
    """Edit an existing RSS feed."""
    feed = rss_feed_service.get_feed_by_id(feed_id)
    if not feed:
        flash("RSS feed not found", "error")
        return redirect(url_for("rss_manager.manage_rss"))

    form = EditRSSFeedForm(obj=feed)
    if form.validate_on_submit():
        try:
            updated_feed = rss_feed_service.update_feed(feed_id, {
                "url": form.url.data,
                "title": form.title.data,
                "category": form.category.data,
                "description": form.description.data,
                "last_build_date": form.last_build_date.data
            })
            flash("RSS Feed updated successfully!", "success")
            logger.info(f"RSS Feed updated: {updated_feed.url}")
        except Exception as e:
            logger.error(f"Error updating RSS Feed: {str(e)}")
            flash(f"Error updating RSS Feed: {str(e)}", "error")
        return redirect(url_for("rss_manager.manage_rss"))
    return render_template("edit_rss_feed.html", form=form, feed=feed)
