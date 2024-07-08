import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from summary_enhancer import SummaryEnhancer
from models import ParsedContent
import yaml
import asyncio

@pytest.fixture
def mock_ollama_api():
    return AsyncMock()

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def enhancer(mock_ollama_api):
    with patch('summary_enhancer.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump({
            'summarize': {
                'system_prompt': 'Summarize the following content:'
            }
        })
        return SummaryEnhancer(mock_ollama_api)

@pytest.mark.asyncio
async def test_generate_summary(enhancer, mock_ollama_api):
    content = "This is a test content."
    expected_summary = "Test summary"
    mock_ollama_api.ask.return_value = expected_summary

    summary = await asyncio.wait_for(enhancer.generate_summary(content), timeout=5.0)

    assert summary == expected_summary
    mock_ollama_api.ask.assert_called_once_with(
        system_prompt='Summarize the following content:',
        user_prompt=content
    )

@pytest.mark.asyncio
async def test_process_single_record_success(enhancer, mock_db_session):
    record = ParsedContent(id=1, content="Test content")
    enhancer.generate_summary = AsyncMock(return_value="Test summary")

    result = await asyncio.wait_for(enhancer.process_single_record(record, mock_db_session), timeout=5.0)

    assert result is True
    assert record.summary == "Test summary"
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_process_single_record_failure(enhancer, mock_db_session):
    record = ParsedContent(id=1, content="Test content")
    enhancer.generate_summary = AsyncMock(side_effect=Exception("Test error"))

    result = await asyncio.wait_for(enhancer.process_single_record(record, mock_db_session), timeout=5.0)

    assert result is False
    assert record.summary is None
    mock_db_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_enhance_summaries(enhancer, mock_db_session):
    mock_records = [
        ParsedContent(id=1, content="Content 1"),
        ParsedContent(id=2, content="Content 2"),
        None
    ]
    mock_db_session.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = mock_records

    enhancer.process_single_record = AsyncMock(side_effect=[True, False])

    with patch('summary_enhancer.db.session', mock_db_session):
        await asyncio.wait_for(enhancer.enhance_summaries(), timeout=10.0)

    assert enhancer.process_single_record.call_count == 2

@pytest.mark.asyncio
async def test_enhance_summaries_exception(enhancer, mock_db_session):
    mock_db_session.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = Exception("Test error")

    with patch('summary_enhancer.db.session', mock_db_session):
        await asyncio.wait_for(enhancer.enhance_summaries(), timeout=10.0)

    # The method should complete without raising an exception
    assert True
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from summary_enhancer import SummaryEnhancer
from ollama_api import OllamaAPI
from models import ParsedContent, db

@pytest.fixture
def mock_ollama_api():
    return AsyncMock(spec=OllamaAPI)

@pytest.fixture
def summary_enhancer(mock_ollama_api):
    return SummaryEnhancer(mock_ollama_api)

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.mark.asyncio
async def test_generate_summary(summary_enhancer, mock_ollama_api):
    mock_ollama_api.generate.return_value = "Test summary"
    
    with patch('summary_enhancer.ParsedContent.get_by_id') as mock_get_by_id:
        mock_get_by_id.return_value = MagicMock(content="Test content")
        result = await summary_enhancer.generate_summary("test_id")
    
    assert result == "Test summary"
    mock_ollama_api.generate.assert_called_once()
    mock_get_by_id.assert_called_once_with("test_id")

@pytest.mark.asyncio
async def test_enhance_summary_success(summary_enhancer, mock_ollama_api, mock_db_session):
    mock_ollama_api.generate.return_value = "Test summary"
    
    with patch('summary_enhancer.ParsedContent.get_by_id') as mock_get_by_id, \
         patch('summary_enhancer.db.session', mock_db_session):
        mock_get_by_id.return_value = MagicMock(id="test_id")
        result = await summary_enhancer.enhance_summary("test_id")
    
    assert result is True
    mock_ollama_api.generate.assert_called_once()
    mock_get_by_id.assert_called_once_with("test_id")
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_enhance_summary_failure(summary_enhancer, mock_ollama_api):
    mock_ollama_api.generate.side_effect = Exception("Test error")
    
    result = await summary_enhancer.enhance_summary("test_id")
    
    assert result is False
    mock_ollama_api.generate.assert_called_once()

@pytest.mark.asyncio
async def test_summarize_feed(summary_enhancer, mock_ollama_api, mock_db_session):
    mock_feed = MagicMock()
    mock_content = MagicMock(id="test_id")
    
    with patch('summary_enhancer.RSSFeed.query') as mock_feed_query, \
         patch('summary_enhancer.ParsedContent.query') as mock_content_query, \
         patch.object(summary_enhancer, 'process_single_record') as mock_process:
        mock_feed_query.get.return_value = mock_feed
        mock_content_query.filter_by.return_value.all.return_value = [mock_content]
        mock_process.return_value = True
        
        await summary_enhancer.summarize_feed("test_feed_id")
    
    mock_feed_query.get.assert_called_once_with("test_feed_id")
    mock_content_query.filter_by.assert_called_once_with(feed_id="test_feed_id", summary=None)
    mock_process.assert_called_once_with(mock_content, mock_db_session)

@pytest.mark.asyncio
async def test_process_single_record(summary_enhancer, mock_ollama_api, mock_db_session):
    mock_document = MagicMock(id="test_id")
    mock_ollama_api.generate.return_value = "Test summary"
    
    result = await summary_enhancer.process_single_record(mock_document, mock_db_session)
    
    assert result is True
    mock_ollama_api.generate.assert_called_once()
    assert mock_document.summary == "Test summary"
    mock_db_session.commit.assert_called_once()

def test_load_prompts(summary_enhancer):
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = """
        summarize:
          system_prompt: "Summarize the following content:"
        """
        prompts = summary_enhancer.load_prompts()
    
    assert 'summarize' in prompts
    assert 'system_prompt' in prompts['summarize']
    assert prompts['summarize']['system_prompt'] == "Summarize the following content:"
