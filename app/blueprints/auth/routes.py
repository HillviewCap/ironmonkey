"""
This module contains the authentication routes for the application.

It defines routes for user login, logout, and registration.
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from flask import Blueprint

bp = Blueprint('auth', __name__)
from app.models.relational import User
from app.forms.auth_forms import LoginForm, RegisterForm
from app import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.

    If the user is already authenticated, redirect to the main index.
    Otherwise, process the login form and authenticate the user.

    Returns:
        A redirect to the next page or main index if login is successful,
        or the login page with an error message if login fails.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
@login_required
def logout():
    """
    Handle user logout.

    Logs out the current user and redirects to the main index.

    Returns:
        A redirect to the main index with a logout confirmation message.
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.

    If the user is already authenticated, redirect to the main index.
    Otherwise, process the registration form and create a new user.

    Returns:
        A redirect to the login page if registration is successful,
        or the registration page if the form is invalid or not submitted.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

# Add other auth routes here
