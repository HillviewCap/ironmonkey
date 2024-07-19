"""
SummaryEnhancer: A class to enhance summaries of parsed content using OllamaAPI.

Workflow:
1. Initialize SummaryEnhancer with OllamaAPI
2. Call summarize_feed() method for a specific feed
3. For each ParsedContent without a summary:
   a. Generate summary using OllamaAPI
   b. Update ParsedContent with new summary
   c. Commit changes to database
4. Handle errors and retries
5. Log process status and completion
"""

from __future__ import annotations
from app.utils.logging_config import setup_logger
from sqlalchemy.orm import Session
from app.models import ParsedContent, db, RSSFeed
import os
import uuid
import asyncio
from typing import Optional, Union
from app.utils.ollama_client import OllamaAPI
from app.utils.groq_api import GroqAPI

logger = setup_logger('summary_enhancer', 'summary_enhancer.log')

class SummaryEnhancer:
    """A class to enhance summaries of parsed content using OllamaAPI or GroqAPI."""
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

        async with db.session() as session:
            parsed_content = await session.get(ParsedContent, content_id)
            if not parsed_content:
                logger.error(f"No ParsedContent found with id {content_id}")
                return None
            return await api.generate("threat_intel_summary", parsed_content.content)

    async def enhance_summary(self, content_id: str) -> bool:
        logger.info(f"Processing record {content_id}")

        async with db.session() as session:
            for attempt in range(self.max_retries):
                try:
                    summary = await self.generate_summary(content_id)
                    if not summary:
                        logger.warning(f"Empty summary generated for record {content_id}. Attempt {attempt + 1}/{self.max_retries}")
                        continue

                    parsed_content = await session.get(ParsedContent, content_id)
                    if not parsed_content:
                        logger.warning(f"ParsedContent not found for id {content_id}")
                        return False

                    parsed_content.summary = summary.strip()
                    await session.commit()
                    logger.info(f"Updated summary for record {content_id}")
                    return True

                except Exception as e:
                    logger.error(f"Error generating summary for record {content_id}: {str(e)}. Attempt {attempt + 1}/{self.max_retries}", exc_info=True)
                    await session.rollback()

        logger.error(f"Failed to generate summary for record {content_id} after {self.max_retries} attempts.")
        return False

    async def summarize_feed(self, feed_id: str) -> None:
        logger.info(f"Starting summary enhancement for feed {feed_id}")

        async with db.session() as session:
            feed = await session.get(RSSFeed, feed_id)
            if not feed:
                logger.error(f"Feed with id {feed_id} not found")
                return

            parsed_contents = await session.execute(
                ParsedContent.select().where(ParsedContent.feed_id == feed_id, ParsedContent.summary == None)
            )
            parsed_contents = parsed_contents.scalars().all()

            for content in parsed_contents:
                success = await self.enhance_summary(str(content.id))
                if not success:
                    logger.warning(f"Failed to generate summary for content {content.id}")

        logger.info(f"Summary enhancement for feed {feed_id} completed")
