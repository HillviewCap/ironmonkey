"""
This module contains the forms used for RSS feed management.

It includes forms for adding, importing, and editing RSS feeds.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, URL, Optional

class AddRSSFeedForm(FlaskForm):
    """Form for adding a new RSS feed."""
    url = StringField('RSS Feed URL', validators=[DataRequired(), URL()])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add Feed')

class ImportCSVForm(FlaskForm):
    """Form for importing RSS feeds from a CSV file."""

    file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Import')

class EditRSSFeedForm(FlaskForm):
    """Form for editing an existing RSS feed."""
    url = StringField('RSS Feed URL', validators=[DataRequired(), URL()])
    title = StringField('Title', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    last_build_date = StringField('Last Build Date', validators=[Optional()])
    submit = SubmitField('Update Feed')
