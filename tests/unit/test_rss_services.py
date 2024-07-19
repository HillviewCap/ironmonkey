import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import UUID
from datetime import datetime
from app.services.rss_feed_service import RSSFeedService
from app.services.parsed_content_service import ParsedContentService
from app.models.relational import RSSFeed, ParsedContent

@pytest.fixture
def rss_feed_service():
    return RSSFeedService()

@pytest.fixture
def parsed_content_service():
    return ParsedContentService()

class TestRSSFeedService:
    def test_get_all_feeds(self, app, rss_feed_service):
        with app.app_context():
            with patch('app.models.relational.RSSFeed.query') as mock_query:
            mock_query.all.return_value = [
                RSSFeed(id=UUID('12345678-1234-5678-1234-567812345678'), url='http://example.com/feed1'),
                RSSFeed(id=UUID('87654321-4321-8765-4321-876543210987'), url='http://example.com/feed2')
            ]
            feeds = rss_feed_service.get_all_feeds()
            assert len(feeds) == 2
            assert feeds[0].url == 'http://example.com/feed1'
            assert feeds[1].url == 'http://example.com/feed2'

    def test_get_feed_by_id(self, rss_feed_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        with patch('app.models.relational.RSSFeed.query') as mock_query:
            mock_query.get.return_value = RSSFeed(id=feed_id, url='http://example.com/feed')
            feed = rss_feed_service.get_feed_by_id(feed_id)
            assert feed.id == feed_id
            assert feed.url == 'http://example.com/feed'

    def test_get_feed_by_url(self, rss_feed_service):
        url = 'http://example.com/feed'
        with patch('app.models.relational.RSSFeed.query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = RSSFeed(id=UUID('12345678-1234-5678-1234-567812345678'), url=url)
            feed = rss_feed_service.get_feed_by_url(url)
            assert feed.url == url

    @pytest.mark.asyncio
    async def test_create_feed(self, app, rss_feed_service):
        feed_data = {
            'url': 'http://example.com/newfeed',
            'title': 'New Feed',
            'category': 'News'
        }
        with app.app_context():
            with patch('app.services.rss_feed_service.db.session.add'), \
                 patch('app.services.rss_feed_service.db.session.commit'), \
                 patch('app.services.rss_feed_service.fetch_feed_info', return_value={'title': 'New Feed', 'description': 'Description', 'last_build_date': datetime.now()}):
                new_feed = await rss_feed_service.create_feed(feed_data)
                assert new_feed.url == feed_data['url']
            assert new_feed.title == feed_data['title']
            assert new_feed.category == feed_data['category']

    def test_update_feed(self, rss_feed_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        feed_data = {
            'url': 'http://example.com/updatedfeed',
            'title': 'Updated Feed',
            'category': 'Blog'
        }
        with patch('app.models.relational.RSSFeed.query') as mock_query, \
             patch('app.services.rss_feed_service.db.session.commit'):
            mock_query.get.return_value = RSSFeed(id=feed_id, url='http://example.com/oldfeed')
            updated_feed = rss_feed_service.update_feed(feed_id, feed_data)
            assert updated_feed.url == feed_data['url']
            assert updated_feed.title == feed_data['title']
            assert updated_feed.category == feed_data['category']

    def test_delete_feed(self, rss_feed_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        with patch('app.models.relational.RSSFeed.query') as mock_query, \
             patch('app.services.rss_feed_service.db.session.delete'), \
             patch('app.services.rss_feed_service.db.session.commit'):
            mock_query.get.return_value = RSSFeed(id=feed_id, url='http://example.com/feed')
            rss_feed_service.delete_feed(feed_id)
            mock_query.get.assert_called_once_with(feed_id)

    @pytest.mark.asyncio
    async def test_parse_feed(self, rss_feed_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        with patch('app.services.rss_feed_service.RSSFeed.query') as mock_query, \
             patch('app.services.rss_feed_service.feedparser.parse') as mock_parse, \
             patch('app.services.rss_feed_service.ParsedContentService.create_parsed_content', new_callable=AsyncMock) as mock_create_content:
            mock_query.get.return_value = RSSFeed(id=feed_id, url='http://example.com/feed')
            mock_parse.return_value = {
                'feed': {'title': 'Test Feed', 'description': 'Test Description'},
                'entries': [
                    {'title': 'Entry 1', 'link': 'http://example.com/entry1', 'summary': 'Summary 1'},
                    {'title': 'Entry 2', 'link': 'http://example.com/entry2', 'summary': 'Summary 2'}
                ]
            }
            await rss_feed_service.parse_feed(feed_id)
            assert mock_create_content.call_count == 2

class TestParsedContentService:
    def test_get_parsed_content(self, app, parsed_content_service):
        filters = {'search': 'test'}
        page = 1
        per_page = 10
        with app.app_context():
            with patch('app.models.relational.ParsedContent.query') as mock_query:
            mock_query.filter.return_value.paginate.return_value = Mock(
                items=[
                    ParsedContent(id=UUID('12345678-1234-5678-1234-567812345678'), title='Test Content 1'),
                    ParsedContent(id=UUID('87654321-4321-8765-4321-876543210987'), title='Test Content 2')
                ],
                total=2
            )
            content, total = parsed_content_service.get_parsed_content(filters, page, per_page)
            assert len(content) == 2
            assert content[0].title == 'Test Content 1'
            assert content[1].title == 'Test Content 2'
            assert total == 2

    def test_get_content_by_id(self, parsed_content_service):
        content_id = UUID('12345678-1234-5678-1234-567812345678')
        with patch('app.models.relational.ParsedContent.query') as mock_query:
            mock_query.get.return_value = ParsedContent(id=content_id, title='Test Content')
            content = parsed_content_service.get_content_by_id(content_id)
            assert content.id == content_id
            assert content.title == 'Test Content'

    def test_create_parsed_content(self, parsed_content_service):
        content_data = {
            'title': 'New Content',
            'url': 'http://example.com/newcontent',
            'description': 'This is new content',
            'pub_date': datetime.now(),
            'feed_id': UUID('12345678-1234-5678-1234-567812345678')
        }
        with patch('app.services.parsed_content_service.db.session.add'), \
             patch('app.services.parsed_content_service.db.session.commit'):
            new_content = parsed_content_service.create_parsed_content(content_data)
            assert new_content.title == content_data['title']
            assert new_content.url == content_data['url']
            assert new_content.description == content_data['description']
            assert new_content.pub_date == content_data['pub_date']
            assert new_content.feed_id == content_data['feed_id']

    def test_update_parsed_content(self, parsed_content_service):
        content_id = UUID('12345678-1234-5678-1234-567812345678')
        content_data = {
            'title': 'Updated Content',
            'description': 'This is updated content'
        }
        with patch('app.models.relational.ParsedContent.query') as mock_query, \
             patch('app.services.parsed_content_service.db.session.commit'):
            mock_query.get.return_value = ParsedContent(id=content_id, title='Old Content')
            updated_content = parsed_content_service.update_parsed_content(content_id, content_data)
            assert updated_content.title == content_data['title']
            assert updated_content.description == content_data['description']

    def test_delete_parsed_content(self, parsed_content_service):
        content_id = UUID('12345678-1234-5678-1234-567812345678')
        with patch('app.models.relational.ParsedContent.query') as mock_query, \
             patch('app.services.parsed_content_service.db.session.delete'), \
             patch('app.services.parsed_content_service.db.session.commit'):
            mock_query.get.return_value = ParsedContent(id=content_id, title='Test Content')
            parsed_content_service.delete_parsed_content(content_id)
            mock_query.get.assert_called_once_with(content_id)

    def test_delete_parsed_content_by_feed_id(self, parsed_content_service):
        feed_id = UUID('12345678-1234-5678-1234-567812345678')
        with patch('app.models.relational.ParsedContent.query') as mock_query, \
             patch('app.services.parsed_content_service.db.session.delete'), \
             patch('app.services.parsed_content_service.db.session.commit'):
            parsed_content_service.delete_parsed_content_by_feed_id(feed_id)
            mock_query.filter_by.assert_called_once_with(feed_id=feed_id)
