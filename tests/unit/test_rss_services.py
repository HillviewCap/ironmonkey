import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import UUID
from datetime import datetime
from app.services.rss_feed_service import RSSFeedService
from app.services.parsed_content_service import ParsedContentService
from app import create_app
from app.extensions import db

@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config['TESTING'] = True
    instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'instance')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "threatstest.db")}'
    with app.app_context():
        db.create_all()
    yield app

@pytest.fixture(scope='function')
def app_context(app):
    with app.app_context():
        yield

@pytest.fixture(scope='module')
def db(app):
    with app.app_context():
        yield db
        db.session.remove()

@pytest.fixture(scope='function')
def session(db):
    connection = db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    db.session = session
    yield session
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    return app.test_cli_runner()

from app.models.relational import RSSFeed, ParsedContent

@pytest.fixture
def rss_feed_service():
    return RSSFeedService()

@pytest.fixture
def parsed_content_service():
    return ParsedContentService()

class TestRSSFeedService:
    def test_get_all_feeds(self, app_context, db, rss_feed_service):
        feeds = [
            RSSFeed(id=UUID('12345678-1234-5678-1234-567812345678'), url='https://grahamcluley.com/feed/'),
            RSSFeed(id=UUID('87654321-4321-8765-4321-876543210987'), url='https://cyberscoop.com/feed/')
        ]
        db.session.add_all(feeds)
        db.session.commit()

        result = rss_feed_service.get_all_feeds()
        assert len(result) == 2
        assert result[0].url == 'https://grahamcluley.com/feed/'
        assert result[1].url == 'https://cyberscoop.com/feed/'

    def test_get_feed_by_id(self, app_context, db, rss_feed_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        feed = RSSFeed(id=feed_id, url='https://grahamcluley.com/feed/')
        db.session.add(feed)
        db.session.commit()

        result = rss_feed_service.get_feed_by_id(feed_id)
        assert result.id == feed_id
        assert result.url == 'https://grahamcluley.com/feed/'

    def test_get_feed_by_url(self, app_context, db, rss_feed_service):
        url = 'https://grahamcluley.com/feed/'
        feed = RSSFeed(id=UUID('12345678-1234-5678-1234-567812345678'), url=url)
        db.session.add(feed)
        db.session.commit()

        result = rss_feed_service.get_feed_by_url(url)
        assert result.url == url

    @pytest.mark.asyncio
    async def test_create_feed(self, app_context, db, rss_feed_service):
        feed_data = {
            'url': 'https://www.bellingcat.com/feed/',
            'title': 'New Feed',
            'category': 'News'
        }
        with patch('app.services.rss_feed_service.fetch_feed_info', return_value={'title': 'New Feed', 'description': 'Description', 'last_build_date': datetime.now()}):
            new_feed = await rss_feed_service.create_feed(feed_data)
            assert new_feed.url == feed_data['url']
            assert new_feed.title == feed_data['title']
            assert new_feed.category == feed_data['category']

    @pytest.mark.asyncio
    async def test_update_feed(self, app_context, db, rss_feed_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        feed = RSSFeed(id=feed_id, url='https://cyberscoop.com/feed/')
        db.session.add(feed)
        db.session.commit()

        feed_data = {
            'url': 'https://www.bellingcat.com/feed/',
            'title': 'Updated Feed',
            'category': 'Blog'
        }
        with patch('app.services.rss_feed_service.fetch_feed_info', return_value={'title': 'Updated Feed', 'description': 'Updated Description', 'last_build_date': datetime.now()}):
            updated_feed = await rss_feed_service.update_feed(feed_id, feed_data)
            assert updated_feed.url == feed_data['url']
            assert updated_feed.title == feed_data['title']
            assert updated_feed.category == feed_data['category']

    def test_delete_feed(self, app_context, db, rss_feed_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        feed = RSSFeed(id=feed_id, url='https://cyberscoop.com/feed/')
        db.session.add(feed)
        db.session.commit()

        rss_feed_service.delete_feed(feed_id)
        assert db.session.query(RSSFeed).get(feed_id) is None

    @pytest.mark.asyncio
    async def test_parse_feed(self, app_context, db, rss_feed_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        feed = RSSFeed(id=feed_id, url='https://cyberscoop.com/feed/')
        db.session.add(feed)
        db.session.commit()

        with patch('app.services.rss_feed_service.feedparser.parse') as mock_parse, \
             patch('app.services.parsed_content_service.ParsedContentService.create_parsed_content', new_callable=AsyncMock) as mock_create_content:
            mock_parse.return_value = {
                'feed': {'title': 'Test Feed', 'description': 'Test Description'},
                'entries': [
                    {'title': 'Entry 1', 'link': 'https://grahamcluley.com/feed/', 'summary': 'Summary 1'},
                    {'title': 'Entry 2', 'link': 'https://cyberscoop.com/feed/', 'summary': 'Summary 2'}
                ]
            }
            await rss_feed_service.parse_feed(feed_id)
            assert mock_create_content.call_count == 2

class TestParsedContentService:
    def test_get_parsed_content(self, app_context, db, parsed_content_service):
        content_items = [
            ParsedContent(id=UUID('12345678-1234-5678-1234-567812345678'), title='Test Content 1'),
            ParsedContent(id=UUID('87654321-4321-8765-4321-876543210987'), title='Test Content 2')
        ]
        db.session.add_all(content_items)
        db.session.commit()

        filters = {'search': 'test'}
        page = 1
        per_page = 10
        content, total = parsed_content_service.get_parsed_content(filters, page, per_page)
        assert len(content) == 2
        assert content[0].title == 'Test Content 1'
        assert content[1].title == 'Test Content 2'
        assert total == 2

    def test_get_content_by_id(self, app_context, db, parsed_content_service):
        content_id = UUID('12345678-1234-5678-1234-567812345678')
        content = ParsedContent(id=content_id, title='Test Content')
        db.session.add(content)
        db.session.commit()

        result = parsed_content_service.get_content_by_id(content_id)
        assert result.id == content_id
        assert result.title == 'Test Content'

    def test_create_parsed_content(self, app_context, db, parsed_content_service):
        content_data = {
            'title': 'New Content',
            'url': 'https://grahamcluley.com/?p=16345023',
            'description': 'This is new content',
            'pub_date': datetime.now(),
            'feed_id': UUID('12345678-1234-5678-1234-567812345678')
        }
        new_content = parsed_content_service.create_parsed_content(content_data)
        assert new_content.title == content_data['title']
        assert new_content.url == content_data['url']
        assert new_content.description == content_data['description']
        assert new_content.pub_date == content_data['pub_date']
        assert new_content.feed_id == content_data['feed_id']

    def test_update_parsed_content(self, app_context, db, parsed_content_service):
        content_id = UUID('12345678-1234-5678-1234-567812345678')
        content = ParsedContent(id=content_id, title='Old Content')
        db.session.add(content)
        db.session.commit()

        content_data = {
            'title': 'Updated Content',
            'description': 'This is updated content'
        }
        updated_content = parsed_content_service.update_parsed_content(content_id, content_data)
        assert updated_content.title == content_data['title']
        assert updated_content.description == content_data['description']

    def test_delete_parsed_content(self, app_context, db, parsed_content_service):
        content_id = UUID('12345678-1234-5678-1234-567812345678')
        content = ParsedContent(id=content_id, title='Test Content')
        db.session.add(content)
        db.session.commit()

        parsed_content_service.delete_parsed_content(content_id)
        assert db.session.query(ParsedContent).get(content_id) is None

    def test_delete_parsed_content_by_feed_id(self, app_context, db, parsed_content_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        content_items = [
            ParsedContent(id=UUID('12345678-1234-5678-1234-567812345678'), title='Content 1', feed_id=feed_id),
            ParsedContent(id=UUID('87654321-4321-8765-4321-876543210987'), title='Content 2', feed_id=feed_id)
        ]
        db.session.add_all(content_items)
        db.session.commit()

        parsed_content_service.delete_parsed_content_by_feed_id(feed_id)
        assert db.session.query(ParsedContent).filter_by(feed_id=feed_id).count() == 0
