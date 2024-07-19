from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, URL, Optional

class AddRSSFeedForm(FlaskForm):
    url = StringField('RSS Feed URL', validators=[DataRequired(), URL()])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add Feed')

class ImportCSVForm(FlaskForm):
    file = FileField('CSV File', validators=[DataRequired()])
    submit = SubmitField('Import')

class EditRSSFeedForm(FlaskForm):
    url = StringField('RSS Feed URL', validators=[DataRequired(), URL()])
    title = StringField('Title', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    last_build_date = StringField('Last Build Date', validators=[Optional()])
    submit = SubmitField('Update Feed')
