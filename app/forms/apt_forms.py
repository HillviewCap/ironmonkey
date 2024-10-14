from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectMultipleField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional

class APTGroupForm(FlaskForm):
    actor = StringField('Actor', validators=[DataRequired()])
    country = StringField('Country', validators=[Optional()])
    motivation = StringField('Motivation', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    first_seen = DateField('First Seen', format='%Y-%m-%d', validators=[Optional()])
    observed_sectors = SelectMultipleField('Observed Sectors', choices=[], validators=[Optional()])
    observed_countries = SelectMultipleField('Observed Countries', choices=[], validators=[Optional()])
    tools = SelectMultipleField('Tools Used', choices=[], validators=[Optional()])
    submit = SubmitField('Save')
