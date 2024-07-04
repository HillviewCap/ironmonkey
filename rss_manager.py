from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, RSSFeed
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL

rss_manager = Blueprint('rss_manager', __name__)

class RSSFeedForm(FlaskForm):
    url = StringField('RSS Feed URL', validators=[DataRequired(), URL()])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add RSS Feed')

@rss_manager.route('/rss_manager', methods=['GET', 'POST'])
@login_required
def manage_rss():
    form = RSSFeedForm()
    if form.validate_on_submit():
        url = form.url.data
        category = form.category.data
        try:
            title, description = RSSFeed.fetch_feed_info(url)
            new_feed = RSSFeed(url=url, title=title, category=category, description=description)
            db.session.add(new_feed)
            db.session.commit()
            flash('RSS Feed added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding RSS Feed: {str(e)}', 'error')
        return redirect(url_for('rss_manager.manage_rss'))
    
    feeds = RSSFeed.query.all()
    return render_template('rss_manager.html', form=form, feeds=feeds)
