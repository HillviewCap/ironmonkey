from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class QuestionnaireForm(FlaskForm):
    role = StringField('Role')
    organization = StringField('Organization')
    location = StringField('Location')
    department = StringField('Department')
    job_function = StringField('Job Function')

    risk_tolerance = SelectField('Risk Tolerance', choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    alert_threshold = SelectField('Alert Threshold', choices=[
        ('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    alert_frequency = SelectField('Alert Frequency', choices=[
        ('real-time', 'Real-time'), ('daily', 'Daily'), ('weekly', 'Weekly')])

    threat_focus_areas = TextAreaField('Threat Focus Areas')
    analysis_scope = StringField('Analysis Scope')

    compliance_requirements = TextAreaField('Compliance Requirements')
    industry_specific_threats = TextAreaField('Industry-specific Threats')

    submit = SubmitField('Submit')
