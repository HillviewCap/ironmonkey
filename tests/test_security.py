import pytest
from app import app
from models import db, User
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()
        yield client
        db.drop_all()

def test_unauthorized_access(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location

def test_sql_injection(client):
    with app.app_context():
        user = User(email='test@example.com', password=generate_password_hash('password'))
        db.session.add(user)
        db.session.commit()

    client.post('/login', data=dict(
        email='test@example.com',
        password='password'
    ), follow_redirects=True)

    response = client.post('/search', json={
        'keywords': "'; DROP TABLE threats; --"
    })
    assert response.status_code == 400

def test_xss_prevention(client):
    with app.app_context():
        user = User(email='test@example.com', password=generate_password_hash('password'))
        db.session.add(user)
        db.session.commit()

    client.post('/login', data=dict(
        email='test@example.com',
        password='password'
    ), follow_redirects=True)

    response = client.post('/search', json={
        'keywords': '<script>alert("XSS")</script>'
    })
    assert response.status_code == 200
    assert '<script>' not in response.get_data(as_text=True)
