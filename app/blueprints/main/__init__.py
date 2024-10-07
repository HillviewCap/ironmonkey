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
            # (Update other fields similarly)
        else:
            # Create a new entry
            questionnaire = UserQuestionnaire(
                user_id=current_user.id,
                role=form.role.data,
                organization=form.organization.data,
                # (Set other fields similarly)
            )
            db.session.add(questionnaire)
        db.session.commit()
        flash('Your information has been submitted successfully.', 'success')
        return redirect(url_for('main.dashboard'))
    else:
        # Pre-fill form if data exists
        existing_entry = UserQuestionnaire.query.filter_by(user_id=current_user.id).first()
        if existing_entry:
            form.role.data = existing_entry.role
            form.organization.data = existing_entry.organization
            # (Pre-fill other fields similarly)
    return render_template('questionnaire.html', form=form)
