import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from app import create_app, db
from app.models.relational.user import User
from config import TestingConfig
from flask_wtf.csrf import generate_csrf

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF protection for testing
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def csrf_token(app):
    with app.test_request_context():
        return generate_csrf()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()
