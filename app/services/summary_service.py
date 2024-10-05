"""
SummaryService: A service to enhance summaries of parsed content using OllamaAPI or GroqAPI.

"""

from __future__ import annotations
from app.utils.logging_config import setup_logger
from sqlalchemy.orm import Session
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.rss_feed import RSSFeed
from app.utils.db_connection_manager import DBConnectionManager
import os
import asyncio
import tempfile
import time
from typing import Optional, Union
from uuid import UUID, uuid4
from app.utils.ollama_client import OllamaAPI, OllamaAPI
from app.utils.groq_api import GroqAPI

logger = setup_logger('summary_service', 'summary_service.log')

from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
import random

class SummaryService:
    """A service to enhance summaries of parsed content using OllamaAPI or GroqAPI."""
    def __init__(self, max_retries: int = 3, lock_timeout: int = 60):
        self.max_retries = max_retries
        self.lock_timeout = lock_timeout
        self.api: Optional[Union[OllamaAPI, GroqAPI]] = None

    def _initialize_api(self) -> Union[OllamaAPI, GroqAPI]:
        if self.api is None:
            api_choice = os.getenv("SUMMARY_API_CHOICE", "ollama").lower()
            if api_choice == "ollama":
                self.api = OllamaAPI()
            elif api_choice == "groq":
                self.api = GroqAPI()
            else:
                raise ValueError(f"Unsupported API choice: {api_choice}. Please set SUMMARY_API_CHOICE to 'ollama' or 'groq' in the .env file.")
        return self.api

    async def generate_summary(self, content_id: str, text_to_summarize: str) -> Optional[str]:
        api = self._initialize_api()
        return await api.generate("threat_intel_summary", text_to_summarize)

    def enhance_summary_sync(self, content_id: str) -> bool:
        return asyncio.run(self.enhance_summary(content_id))

    async def enhance_summary(self, content_id: str) -> bool:
        logger.info(f"Processing record {content_id}")

        # Validate UUID
        try:
            uuid_obj = UUID(content_id, version=4)
        except ValueError:
            logger.warning(f"Invalid UUID format for content_id: {content_id}")
            return False

        # Normalize both UUIDs to compare their hex values without hyphens
        if uuid_obj.hex != content_id.lower().replace('-', ''):
            logger.warning(f"Invalid UUID format for content_id: {content_id}")
            return False

        for attempt in range(self.max_retries):
            try:
                with DBConnectionManager.get_session() as session:
                    parsed_content = self._lock_content(session, content_id)
                    if not parsed_content:
                        logger.warning(f"ParsedContent not found or locked for id {content_id}")
                        return False

                    if parsed_content.summary:
                        logger.info(f"Record {content_id} already has a summary. Skipping.")
                        return True

                    # Check if content exists and is not empty, if empty check description
                    text_to_summarize = None
                    if parsed_content.content and parsed_content.content.strip():
                        text_to_summarize = parsed_content.content
                    elif parsed_content.description and parsed_content.description.strip():
                        text_to_summarize = parsed_content.description
                    
                    if not text_to_summarize:
                        logger.warning(f"Record {content_id} has no content or description. Skipping summary generation.")
                        return False

                    summary = await self.generate_summary(content_id, text_to_summarize)
                    if not summary:
                        logger.warning(f"Empty summary generated for record {content_id}. Attempt {attempt + 1}/{self.max_retries}")
                        continue

                    parsed_content.summary = summary.strip()
                    session.commit()
                    logger.info(f"Updated summary for record {content_id}")
                    return True

            except OperationalError as e:
                if "database is locked" in str(e) and attempt < self.max_retries - 1:
                    wait_time = random.uniform(0.1, 0.5) * (2 ** attempt)
                    logger.warning(f"Database locked, retrying in {wait_time:.2f} seconds... (attempt {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"Operational error for record {content_id}: {str(e)}. Attempt {attempt + 1}/{self.max_retries}", exc_info=True)
            except Exception as e:
                logger.error(f"Error generating summary for record {content_id}: {str(e)}. Attempt {attempt + 1}/{self.max_retries}", exc_info=True)

        logger.error(f"Failed to generate summary for record {content_id} after {self.max_retries} attempts.")
        return False

    def _lock_content(self, session: Session, content_id: str) -> Optional[ParsedContent]:
        try:
            parsed_content = session.query(ParsedContent).filter(
                ParsedContent.id == UUID(content_id),
                ParsedContent.summary == None
            ).first()  # Removed with_for_update(nowait=True)
            return parsed_content
        except OperationalError:
            return None

    async def summarize_feed(self, feed_id: str) -> None:
        logger.info(f"Starting summary enhancement for feed {feed_id}")

        with DBConnectionManager.get_session() as session:
            feed = session.get(RSSFeed, feed_id)
            if not feed:
                logger.error(f"Feed with id {feed_id} not found")
                return

            parsed_contents = session.query(ParsedContent).filter(
                ParsedContent.feed_id == feed_id,
                ParsedContent.summary == None
            ).all()

            async def process_content(content):
                success = await self.enhance_summary(content.id.hex)
                if not success:
                    logger.warning(f"Failed to generate summary for content {content.id}")

            await asyncio.gather(*(process_content(content) for content in parsed_contents))

        logger.info(f"Summary enhancement for feed {feed_id} completed")
