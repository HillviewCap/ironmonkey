"""
This module contains the forms used for user authentication.

It includes forms for user login and registration.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models.relational.user import User

class LoginForm(FlaskForm):
    """Form for user login."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    """Form for user registration."""

    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        """
        Validate that the email is not already in use.

        Args:
            email: The email field to validate.

        Raises:
            ValidationError: If the email is already associated with an existing user.
        """
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
