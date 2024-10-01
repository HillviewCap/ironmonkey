import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask import url_for
from app.models.relational.rss_feed import RSSFeed
from app.models.relational.user import User
from app import db
from app.models.relational.awesome_threat_intel_blog import AwesomeThreatIntelBlog

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
            session['user_id'] = str(user.id)  # Convert UUID to string
            session['_fresh'] = True

        # Perform a login request
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpassword'
        }, follow_redirects=True)

    return client

def test_add_single_feed(authenticated_client, app, csrf_token):
    # Prepare test data
    feed_data = {
        'url': 'https://feeds.feedburner.com/TheHackersNews',
        'category': 'News',
        'csrf_token': csrf_token
    }

    # Send POST request to create_rss_feed endpoint
    response = authenticated_client.post('/rss/feed', json=feed_data)

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

def test_get_awesome_blogs(authenticated_client, app):
    # Add a test blog to the database
    with app.app_context():
        test_blog = AwesomeThreatIntelBlog(
            blog="Test Blog",
            blog_category="Test Category",
            type="Test Type",
            blog_link="https://testblog.com",
            feed_link="https://testblog.com/feed"
        )
        db.session.add(test_blog)
        db.session.commit()

    # Send GET request to get_awesome_blogs endpoint
    response = authenticated_client.get('/awesome_blogs')

    # Check response
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    blogs = data['data']
    assert len(blogs) > 0
    assert any(blog['blog'] == "Test Blog" for blog in blogs)

    # Clean up: remove the test blog from the database
    with app.app_context():
        db.session.delete(test_blog)
        db.session.commit()

def test_update_awesome_threat_intel(authenticated_client, app, csrf_token):
    # Send POST request to update_awesome_threat_intel endpoint
    response = authenticated_client.post('/update_awesome_threat_intel', data={'csrf_token': csrf_token})

    # Check response
    assert response.status_code == 302  # Expecting a redirect
    assert response.location == url_for('rss_manager.get_rss_feeds')

    # Check if the flash message is set
    with authenticated_client.session_transaction() as session:
        flash_messages = session.get('_flashes', [])
        assert any('Awesome Threat Intel Blogs have been updated.' in message for category, message in flash_messages)
