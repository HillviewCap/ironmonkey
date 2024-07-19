import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from unittest.mock import patch, Mock
from app.utils.rss_validator import validate_rss_url, extract_feed_info
from app.utils.content_sanitizer import sanitize_html_content

class TestRSSValidator:
    @pytest.mark.parametrize("url,expected", [
        ("http://example.com/valid_feed.xml", True),
        ("http://example.com/invalid_feed.xml", False),
        ("http://example.com/not_a_feed.html", False),
    ])
    def test_validate_rss_url(self, url, expected):
        with patch('app.utils.rss_validator.feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(version='' if not expected else '2.0', bozo=not expected)
            result = validate_rss_url(url)
            assert result == expected

    def test_extract_feed_info_valid(self):
        url = "http://example.com/valid_feed.xml"
        with patch('app.utils.rss_validator.feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(
                version='2.0',
                bozo=False,
                feed={
                    'title': 'Test Feed',
                    'description': 'A test RSS feed',
                    'link': 'http://example.com',
                    'updated': '2023-07-18T12:00:00Z'
                }
            )
            result = extract_feed_info(url)
            assert result == {
                'title': 'Test Feed',
                'description': 'A test RSS feed',
                'link': 'http://example.com',
                'last_build_date': '2023-07-18T12:00:00Z'
            }

    def test_extract_feed_info_invalid(self):
        url = "http://example.com/invalid_feed.xml"
        with patch('app.utils.rss_validator.feedparser.parse') as mock_parse:
            mock_parse.return_value = Mock(version='', bozo=True)
            result = extract_feed_info(url)
            assert result is None

class TestContentSanitizer:
    @pytest.mark.parametrize("input_html,expected_output", [
        ("<p>Test</p>", "<p>Test</p>"),
        ("<script>alert('XSS')</script>", ""),
        ('<a href="http://example.com" onclick="alert(\'XSS\')">Link</a>', '<a href="http://example.com">Link</a>'),
        ('<img src="image.jpg" onerror="alert(\'XSS\')" />', '<img src="image.jpg">'),
    ])
    def test_sanitize_html_content(self, input_html, expected_output):
        result = sanitize_html_content(input_html)
        assert result.strip() == expected_output.strip()

    def test_sanitize_html_content_preserves_allowed_tags(self):
        input_html = "<p><strong>Bold</strong> and <em>italic</em> text</p>"
        result = sanitize_html_content(input_html)
        assert result.strip() == input_html.strip()

    def test_sanitize_html_content_removes_disallowed_tags(self):
        input_html = "<p>Text with <iframe>iframe</iframe> and <script>script</script></p>"
        expected_output = "<p>Text with  and </p>"
        result = sanitize_html_content(input_html)
        assert result.strip() == expected_output.strip()
