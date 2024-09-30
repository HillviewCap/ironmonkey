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
from typing import Optional, Union
from uuid import UUID
from app.utils.ollama_client import OllamaAPI, OllamaAPI
from app.utils.groq_api import GroqAPI

logger = setup_logger('summary_service', 'summary_service.log')

class SummaryService:
    """A service to enhance summaries of parsed content using OllamaAPI or GroqAPI."""
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
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

    async def generate_summary(self, content_id: str) -> Optional[str]:
        api = self._initialize_api()

        with DBConnectionManager.get_session() as session:
            parsed_content = session.get(ParsedContent, UUID(content_id))
            if not parsed_content:
                logger.error(f"No ParsedContent found with id {content_id}")
                return None
            return await api.generate("threat_intel_summary", parsed_content.content)

    async def enhance_summary(self, content_id: str) -> bool:
        logger.info(f"Processing record {content_id}")

        for attempt in range(self.max_retries):
            try:
                with DBConnectionManager.get_session() as session:
                    summary = await self.generate_summary(content_id)
                    if not summary:
                        logger.warning(f"Empty summary generated for record {content_id}. Attempt {attempt + 1}/{self.max_retries}")
                        continue

                    parsed_content = session.get(ParsedContent, UUID(content_id))
                    if not parsed_content:
                        logger.warning(f"ParsedContent not found for id {content_id}")
                        return False

                    if parsed_content.summary:
                        logger.info(f"Record {content_id} already has a summary. Skipping.")
                        return True

                    parsed_content.summary = summary.strip()
                    session.commit()
                    logger.info(f"Updated summary for record {content_id}")
                    return True

            except Exception as e:
                logger.error(f"Error generating summary for record {content_id}: {str(e)}. Attempt {attempt + 1}/{self.max_retries}", exc_info=True)

        logger.error(f"Failed to generate summary for record {content_id} after {self.max_retries} attempts.")
        return False

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
