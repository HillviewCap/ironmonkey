import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask import url_for
from app.models.relational.rss_feed import RSSFeed
from app import db

def test_add_single_feed(client, app):
    # Prepare test data
    feed_data = {
        'url': 'https://feeds.feedburner.com/TheHackersNews',
        'category': 'News'
    }

    # Send POST request to create_rss_feed endpoint
    response = client.post('/feed', json=feed_data)

    # Check response
    assert response.status_code == 201
    data = response.get_json()
    assert 'feed' in data
    assert 'feeds' in data

    # Verify the new feed is in the database
    with app.app_context():
        new_feed = RSSFeed.query.filter_by(url=feed_data['url']).first()
        assert new_feed is not None
        assert new_feed.category == feed_data['category']

    # Check that the new feed is in the returned list of feeds
    assert any(feed['url'] == feed_data['url'] for feed in data['feeds'])

    # Clean up: remove the test feed from the database
    with app.app_context():
        db.session.delete(new_feed)
        db.session.commit()
