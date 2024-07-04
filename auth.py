from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db
from flask import current_app, request, redirect, url_for, flash

login_manager = LoginManager()
principal = Principal()

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_auth(app):
    login_manager.init_app(app)
    principal.init_app(app)

    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(current_user.id))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                identity_changed.send(current_app._get_current_object(),
                                      identity=Identity(user.id))
                flash('Logged in successfully.')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password.')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        identity_changed.send(current_app._get_current_object(),
                              identity=AnonymousIdentity())
        flash('Logged out successfully.')
        return redirect(url_for('index'))

def create_user(email, password):
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
