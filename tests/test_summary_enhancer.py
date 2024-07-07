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
