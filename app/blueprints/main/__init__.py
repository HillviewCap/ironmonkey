from flask import Blueprint
from flask_login import login_required

bp = Blueprint('main', __name__)

from . import routes

# Apply login_required to all routes in this blueprint
@bp.before_request
@login_required
def before_request():
    pass

__all__ = ['bp']
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms.questionnaire_form import QuestionnaireForm
from app.models.relational.user_questionnaire import UserQuestionnaire
from app import db

@bp.route('/questionnaire', methods=['GET', 'POST'])
@login_required
def questionnaire():
    form = QuestionnaireForm()
    if form.validate_on_submit():
        # Check if the user has already submitted the questionnaire
        existing_entry = UserQuestionnaire.query.filter_by(user_id=current_user.id).first()
        if existing_entry:
            # Update existing entry
            existing_entry.role = form.role.data
            existing_entry.organization = form.organization.data
            existing_entry.location = form.location.data
            existing_entry.department = form.department.data
            existing_entry.job_function = form.job_function.data
            existing_entry.risk_tolerance = form.risk_tolerance.data
            existing_entry.alert_threshold = form.alert_threshold.data
            existing_entry.alert_frequency = form.alert_frequency.data
            existing_entry.threat_focus_areas = form.threat_focus_areas.data
            existing_entry.analysis_scope = form.analysis_scope.data
            existing_entry.compliance_requirements = form.compliance_requirements.data
            existing_entry.industry_specific_threats = form.industry_specific_threats.data
        else:
            # Create a new entry
            questionnaire = UserQuestionnaire(
                user_id=current_user.id,
                role=form.role.data,
                organization=form.organization.data,
                location=form.location.data,
                department=form.department.data,
                job_function=form.job_function.data,
                risk_tolerance=form.risk_tolerance.data,
                alert_threshold=form.alert_threshold.data,
                alert_frequency=form.alert_frequency.data,
                threat_focus_areas=form.threat_focus_areas.data,
                analysis_scope=form.analysis_scope.data,
                compliance_requirements=form.compliance_requirements.data,
                industry_specific_threats=form.industry_specific_threats.data
            )
            db.session.add(questionnaire)
        db.session.commit()
        flash('Your information has been submitted successfully.', 'success')
        return redirect(url_for('main.index'))
    else:
        # Pre-fill form if data exists
        existing_entry = UserQuestionnaire.query.filter_by(user_id=current_user.id).first()
        if existing_entry:
            form.role.data = existing_entry.role
            form.organization.data = existing_entry.organization
            form.location.data = existing_entry.location
            form.department.data = existing_entry.department
            form.job_function.data = existing_entry.job_function
            form.risk_tolerance.data = existing_entry.risk_tolerance
            form.alert_threshold.data = existing_entry.alert_threshold
            form.alert_frequency.data = existing_entry.alert_frequency
            form.threat_focus_areas.data = existing_entry.threat_focus_areas
            form.analysis_scope.data = existing_entry.analysis_scope
            form.compliance_requirements.data = existing_entry.compliance_requirements
            form.industry_specific_threats.data = existing_entry.industry_specific_threats
    return render_template('questionnaire.html', form=form)
