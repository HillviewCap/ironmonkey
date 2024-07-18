from __future__ import annotations

from flask import Flask, redirect, url_for, render_template, flash
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo
from sqlalchemy.exc import IntegrityError
import uuid
from datetime import timedelta
from typing import Optional

login_manager = LoginManager()

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

def init_auth(app: Flask) -> None:
    """Initialize authentication for the Flask app."""
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id: str) -> Optional[User]:
        """Load user by ID."""
        try:
            return User.query.get(uuid.UUID(user_id))
        except (ValueError, AttributeError):
            return None

@login_required
def index():
    """Render the index page."""
    return render_template('index.html')

def login():
    """Handle user login."""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data, duration=timedelta(days=30))
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password')
    return render_template('login.html', form=form)

@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('index'))

def register():
    """Handle user registration."""
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        try:
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Email address already exists. Please use a different email.', 'danger')
    return render_template('register.html', form=form)
