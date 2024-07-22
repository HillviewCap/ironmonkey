import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask import url_for
from app.models.relational.rss_feed import RSSFeed
from app.models.relational.user import User
from app import db

@pytest.fixture
def authenticated_client(client, app):
    with app.app_context():
        # Create a test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()

    # Log in the user
    with client.session_transaction() as session:
        session['user_id'] = user.id
        session['_fresh'] = True

    return client

def test_add_single_feed(authenticated_client, app, csrf_token):
    # Prepare test data
    feed_data = {
        'url': 'https://feeds.feedburner.com/TheHackersNews',
        'category': 'News'
    }

    # Send POST request to create_rss_feed endpoint
    response = authenticated_client.post('/rss/feed', json=feed_data, headers={'X-CSRFToken': csrf_token})

    # Check response
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.data.decode()}")
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response: {response.data.decode()}"
    data = response.get_json()
    assert 'feed' in data, f"'feed' not in response data. Got: {data}"
    assert 'feeds' in data, f"'feeds' not in response data. Got: {data}"

    # Verify the new feed is in the database
    with app.app_context():
        new_feed = RSSFeed.query.filter_by(url=feed_data['url']).first()
        assert new_feed is not None
        assert new_feed.category == feed_data['category']

    # Check that the new feed is in the returned list of feeds
    assert any(feed['url'] == feed_data['url'] for feed in data['feeds'])

    # Clean up: remove the test feed and user from the database
    with app.app_context():
        db.session.delete(new_feed)
        User.query.filter_by(username='testuser').delete()
        db.session.commit()
