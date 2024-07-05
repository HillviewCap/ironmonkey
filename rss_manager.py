from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for, flash, request
import logging_config
from flask_login import login_required
from models import db, RSSFeed, ParsedContent
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired, URL
from typing import List, Union
import csv
from io import TextIOWrapper
import httpx
import uuid
from werkzeug.wrappers import Response
from sqlalchemy.exc import IntegrityError
import feedparser
from jina_api import parse_content
import asyncio

rss_manager = Blueprint('rss_manager', __name__)
csrf = CSRFProtect()

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
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add RSS Feed')

class CSVUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Import Feeds')

class EditRSSFeedForm(FlaskForm):
    url = StringField('RSS Feed URL', validators=[DataRequired(), URL()])
    title = StringField('Title', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    description = StringField('Description')
    last_build_date = StringField('Last Build Date')
    submit = SubmitField('Update Feed')

@rss_manager.route('/rss_manager', methods=['GET', 'POST'])
@login_required
def manage_rss() -> str:
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
            logging_config.logger.info(f'RSS Feed added: {url}')
        except Exception as e:
            logging_config.logger.error(f'Error adding RSS Feed: {str(e)}')
            logging_config.logger.error(f'Error adding RSS Feed: {str(e)}')
            flash(f'Error adding RSS Feed: {str(e)}', 'error')
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

@rss_manager.route('/delete_feed/<uuid:feed_id>', methods=['POST'])
@login_required
@csrf.exempt
def delete_feed(feed_id: uuid.UUID) -> Response:
    """
    Delete an RSS feed from the database.

    Args:
        feed_id (uuid.UUID): The UUID of the feed to be deleted.

    Returns:
        werkzeug.wrappers.Response: A redirect response to the RSS manager page.
    """
    feed = RSSFeed.query.get_or_404(feed_id)
    db.session.delete(feed)
    db.session.commit()
    logging_config.logger.info(f'RSS Feed deleted: {feed.url}')
    flash('RSS Feed deleted successfully!', 'success')
    return redirect(url_for('rss_manager.manage_rss'))

@rss_manager.route('/edit_feed/<uuid:feed_id>', methods=['GET', 'POST'])
@login_required
def edit_feed(feed_id: uuid.UUID) -> Union[str, Response]:
    """
    Edit an existing RSS feed.

    Args:
        feed_id (uuid.UUID): The UUID of the feed to be edited.

    Returns:
        Union[str, Response]: Rendered HTML template or redirect response.
    """
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
            flash('RSS Feed updated successfully!', 'success')
            logging_config.logger.info(f'RSS Feed updated: {feed.url}')
        except Exception as e:
            db.session.rollback()
            logging_config.logger.error(f'Error updating RSS Feed: {str(e)}')
            flash(f'Error updating RSS Feed: {str(e)}', 'error')
        return redirect(url_for('rss_manager.manage_rss'))
    return render_template('edit_rss_feed.html', form=form, feed=feed)
