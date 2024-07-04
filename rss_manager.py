from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, RSSFeed
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from typing import List

rss_manager = Blueprint('rss_manager', __name__)

class RSSFeedForm(FlaskForm):
    url = StringField('RSS Feed URL', validators=[DataRequired(), URL()])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add RSS Feed')

@rss_manager.route('/rss_manager', methods=['GET', 'POST'])
@login_required
def manage_rss():
    form: RSSFeedForm = RSSFeedForm()
    if form.validate_on_submit():
        url: str = form.url.data
        category: str = form.category.data
        try:
            title, description, last_build_date = RSSFeed.fetch_feed_info(url)
            new_feed: RSSFeed = RSSFeed(url=url, title=title, category=category, description=description, last_build_date=last_build_date)
            db.session.add(new_feed)
            db.session.commit()
            flash('RSS Feed added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding RSS Feed: {str(e)}', 'error')
        return redirect(url_for('rss_manager.manage_rss'))
    
    feeds: List[RSSFeed] = RSSFeed.query.all()
    return render_template('rss_manager.html', form=form, feeds=feeds)

@rss_manager.route('/delete_feed/<uuid:feed_id>', methods=['POST'])
@login_required
def delete_feed(feed_id):
    feed = RSSFeed.query.get_or_404(feed_id)
    db.session.delete(feed)
    db.session.commit()
    flash('RSS Feed deleted successfully!', 'success')
    return redirect(url_for('rss_manager.manage_rss'))
