from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, flash, request
import httpx
import logging_config
from flask_login import login_required
from models import db, RSSFeed, ParsedContent
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired, URL
from typing import List
import csv
from io import TextIOWrapper
import httpx
import uuid
from werkzeug.wrappers import Response
from sqlalchemy.exc import IntegrityError
import feedparser
from jina_api import parse_content
import asyncio
from sqlalchemy import func
from flask import request
from nlp_tagging import tag_single_content

rss_manager = Blueprint('rss_manager', __name__)
csrf = CSRFProtect()

PER_PAGE_OPTIONS = [10, 25, 50, 100]

@rss_manager.route('/parse_feeds', methods=['POST'])
@login_required
async def parse_feeds():
    feeds = RSSFeed.query.all()
    for feed in feeds:
        try:
            parsed_feed = feedparser.parse(feed.url)
            for entry in parsed_feed.entries:
                existing_content = ParsedContent.query.filter_by(url=entry.link).first()
                if not existing_content:
                    parsed_data = await parse_content(entry.link)
                    new_content = ParsedContent(
                        title=parsed_data['title'],
                        url=parsed_data['url'],
                        content=parsed_data['content'],
                        links=parsed_data['links'],
                        feed_id=feed.id
                    )
                    db.session.add(new_content)
            db.session.commit()
        except Exception as e:
            logging_config.logger.error(f"Error parsing feed {feed.url}: {str(e)}")
    
    flash('Feed parsing completed', 'success')
    return redirect(url_for('rss_manager.manage_rss'))

class RSSFeedForm(FlaskForm):
    url = StringField('RSS Feed URL', validators=[DataRequired(), URL()])
    category = SelectField('Category', choices=[('News', 'News'), ('Blog', 'Blog'), ('Research', 'Research')], validators=[DataRequired()])
    submit = SubmitField('Add RSS Feed')

class CSVUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Import Feeds')

@rss_manager.route('/rss_manager', methods=['GET', 'POST'])
@login_required
async def manage_rss() -> str:
    """
    Handle RSS feed management operations.
    
    This function handles both GET and POST requests for the RSS manager page.
    It processes form submissions for adding individual RSS feeds and importing
    feeds from CSV files.

    Returns:
        str: Rendered HTML template for the RSS manager page.
    """
    form: RSSFeedForm = RSSFeedForm()
    csv_form: CSVUploadForm = CSVUploadForm()
    
    if form.validate_on_submit():
        url: str = form.url.data
        category: str = form.category.data
        try:
            title, description, last_build_date = RSSFeed.fetch_feed_info(url)
            new_feed: RSSFeed = RSSFeed(
                url=url,
                title=title if title else 'Not available',
                category=category,
                description=description if description else 'Not available',
                last_build_date=last_build_date if last_build_date else None
            )
            db.session.add(new_feed)
            db.session.commit()
            flash('RSS Feed added successfully!', 'success')
            logging_config.logger.info(f'RSS Feed added: {url}')
            
            # Start parsing the new feed immediately
            await parse_single_feed(new_feed)
            flash('New feed parsed successfully!', 'success')
        except Exception as e:
            logging_config.logger.error(f'Error adding or parsing RSS Feed: {str(e)}')
            flash(f'Error adding or parsing RSS Feed: {str(e)}', 'error')
        return redirect(url_for('rss_manager.manage_rss'))
    
    if csv_form.validate_on_submit():
        csv_file = csv_form.file.data
        if csv_file.filename.endswith('.csv'):
            try:
                csv_file = TextIOWrapper(csv_file, encoding='utf-8')
                csv_reader = csv.reader(csv_file)
                errors = []
                feeds_to_add = []
                imported_count = 0
                skipped_count = 0
                for row in csv_reader:
                    if len(row) >= 1:
                        url = row[0]
                        category = row[1] if len(row) > 1 else 'Uncategorized'
                        title, description, last_build_date = 'Unknown Title', 'No description available', None
                        try:
                            title, description, last_build_date = RSSFeed.fetch_feed_info(url)
                        except Exception as e:
                            errors.append(f'Error fetching info for RSS Feed {url}: {str(e)}')
                            logging_config.logger.error(f'Error fetching info for RSS Feed {url}: {str(e)}')
                        new_feed: RSSFeed = RSSFeed(url=url, title=title, category=category, description=description, last_build_date=last_build_date)
                        feeds_to_add.append(new_feed)
                if errors:
                    for error in errors:
                        flash(error, 'error')
                else:
                    if feeds_to_add:
                        for feed in feeds_to_add:
                            try:
                                db.session.add(feed)
                                db.session.commit()
                                imported_count += 1
                                logging_config.logger.info(f'RSS Feed added from CSV: {feed.url}')
                            except IntegrityError:
                                db.session.rollback()
                                skipped_count += 1
                                logging_config.logger.info(f'Skipped duplicate RSS Feed: {feed.url}')
                        if imported_count > 0:
                            flash(f'Successfully imported {imported_count} RSS feeds.', 'success')
                        if skipped_count > 0:
                            flash(f'Skipped {skipped_count} duplicate RSS feeds.', 'info')
                        if imported_count == 0 and skipped_count == 0:
                            flash('No valid feeds found in CSV file.', 'warning')
                    else:
                        flash('No valid feeds found in CSV file.', 'warning')
            except Exception as e:
                logging_config.logger.error(f'Error processing CSV file: {str(e)}')
                flash(f'Error processing CSV file: {str(e)}', 'error')
        else:
            logging_config.logger.warning('Invalid file format. Please upload a CSV file.')
            flash('Invalid file format. Please upload a CSV file.', 'error')
        return redirect(url_for('rss_manager.manage_rss'))
    
    feeds: List[RSSFeed] = RSSFeed.query.all()
    delete_form = FlaskForm()  # Create a new form for CSRF protection
    return render_template('rss_manager.html', form=form, csv_form=csv_form, feeds=feeds, delete_form=delete_form)

@rss_manager.route('/parsed_content')
@login_required
def parsed_content():
    """Display parsed content from the database with pagination and search."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '')

    query = ParsedContent.query.order_by(ParsedContent.created_at.desc())

    if search_query:
        query = query.filter(
            (ParsedContent.title.ilike(f'%{search_query}%')) |
            (ParsedContent.content.ilike(f'%{search_query}%')) |
            (ParsedContent.url.ilike(f'%{search_query}%'))
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items

    return render_template('parsed_content.html', 
                           posts=posts, 
                           pagination=pagination, 
                           search_query=search_query,
                           per_page=per_page,
                           per_page_options=PER_PAGE_OPTIONS)

@rss_manager.route('/tag_content/<uuid:post_id>', methods=['POST'])
@login_required
def tag_content(post_id):
    post = ParsedContent.query.get_or_404(post_id)
    try:
        tag_single_content(post)
        flash('Content tagged successfully!', 'success')
    except Exception as e:
        flash(f'Error tagging content: {str(e)}', 'error')
    return redirect(url_for('rss_manager.parsed_content'))

@rss_manager.route('/delete_feed/<uuid:feed_id>', methods=['POST'])
@login_required
def delete_feed(feed_id: uuid.UUID):
    """
    Delete an RSS feed from the database.

    Args:
        feed_id (uuid.UUID): The UUID of the feed to be deleted.

    Returns:
        flask.Response: A redirect response to the RSS manager page.
    """
    feed = RSSFeed.query.get_or_404(feed_id)
    db.session.delete(feed)
    db.session.commit()
    logging_config.logger.info(f'RSS Feed deleted: {feed.url}')
    flash('RSS Feed deleted successfully!', 'success')
    return redirect(url_for('rss_manager.manage_rss'))
async def parse_single_feed(feed: RSSFeed):
    """Parse a single RSS feed and store new content."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(feed.url)
            feed_data = feedparser.parse(response.text)
            
            for entry in feed_data.entries:
                existing_content = ParsedContent.query.filter_by(url=entry.link).first()
                if not existing_content:
                    parsed_data = await parse_content(entry.link)
                    new_content = ParsedContent(
                        title=parsed_data['title'],
                        url=parsed_data['url'],
                        content=parsed_data['content'],
                        links=parsed_data['links'],
                        feed_id=feed.id
                    )
                    db.session.add(new_content)
            db.session.commit()
    except Exception as e:
        logging_config.logger.error(f"Error parsing feed {feed.url}: {str(e)}")
        raise
