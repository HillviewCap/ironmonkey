from flask import Blueprint, render_template, redirect, url_for, flash, request
import logging_config
from flask_login import login_required
from models import db, RSSFeed
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired, URL
from typing import List
import csv
from io import TextIOWrapper

rss_manager = Blueprint('rss_manager', __name__)

class RSSFeedForm(FlaskForm):
    url = StringField('RSS Feed URL', validators=[DataRequired(), URL()])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add RSS Feed')

class CSVUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Import Feeds')

@rss_manager.route('/rss_manager', methods=['GET', 'POST'])
@login_required
def manage_rss():
    form: RSSFeedForm = RSSFeedForm()
    csv_form: CSVUploadForm = CSVUploadForm()
    
    if form.validate_on_submit():
        url: str = form.url.data
        category: str = form.category.data
        try:
            title, description, last_build_date = RSSFeed.fetch_feed_info(url)
            new_feed: RSSFeed = RSSFeed(url=url, title=title, category=category, description=description, last_build_date=last_build_date)
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
                for row in csv_reader:
                    if len(row) >= 2:
                        url, category = row[0], row[1]
                        try:
                            title, description, last_build_date = RSSFeed.fetch_feed_info(url)
                            new_feed: RSSFeed = RSSFeed(url=url, title=title, category=category, description=description, last_build_date=last_build_date)
                            feeds_to_add.append(new_feed)
                        except Exception as e:
                            errors.append(f'Error fetching info for RSS Feed {url}: {str(e)}')
                if errors:
                    url = None  # Ensure url is defined before logging
                    for error in errors:
                        flash(error, 'error')
                    for error in errors:
                        logging_config.logger.error(error)
                else:
                    logging_config.logger.info(f'RSS Feed added from CSV: {url}')
                    db.session.bulk_save_objects(feeds_to_add)
                    db.session.commit()
                    flash('CSV file processed successfully!', 'success')
            except Exception as e:
                logging_config.logger.error(f'Error processing CSV file: {str(e)}')
                flash(f'Error processing CSV file: {str(e)}', 'error')
        else:
            logging_config.logger.warning('Invalid file format. Please upload a CSV file.')
            flash('Invalid file format. Please upload a CSV file.', 'error')
        return redirect(url_for('rss_manager.manage_rss'))
    
    feeds: List[RSSFeed] = RSSFeed.query.all()
    return render_template('rss_manager.html', form=form, csv_form=csv_form, feeds=feeds)

@rss_manager.route('/delete_feed/<uuid:feed_id>', methods=['POST'])
@login_required
def delete_feed(feed_id):
    feed = RSSFeed.query.get_or_404(feed_id)
    db.session.delete(feed)
    db.session.commit()
    logging_config.logger.info(f'RSS Feed deleted: {feed.url}')
    flash('RSS Feed deleted successfully!', 'success')
    return redirect(url_for('rss_manager.manage_rss'))
