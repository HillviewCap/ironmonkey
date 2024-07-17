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
from logging_config import setup_logger
from sqlalchemy.orm import Session
from models import ParsedContent, db, RSSFeed
import os
from ollama_api import OllamaAPI
from groq_api import GroqAPI
from typing import Optional

logger = setup_logger('summary_enhancer', 'summary_enhancer.log')

class SummaryEnhancer:
    def __init__(self, max_retries: int = 3):
        self.api = self._initialize_api()
        self.max_retries = max_retries

    def _initialize_api(self):
        api_choice = os.getenv("SUMMARY_API_CHOICE", "ollama").lower()
        if api_choice == "ollama":
            return OllamaAPI()
        elif api_choice == "groq":
            return GroqAPI()
        else:
            raise ValueError(f"Unsupported API choice: {api_choice}. Please set SUMMARY_API_CHOICE to 'ollama' or 'groq' in the .env file.")

    async def generate_summary(self, content_id: str) -> str:
        parsed_content = ParsedContent.get_by_id(content_id)
        if not parsed_content:
            raise ValueError(f"No ParsedContent found with id {content_id}")
        return await self.api.generate("threat_intel_summary", parsed_content.content)

    async def enhance_summary(self, content_id: str) -> bool:
        logger.info(f"Processing record {content_id}")

        for attempt in range(self.max_retries):
            try:
                summary = await self.generate_summary(content_id)
                if not summary:
                    logger.warning(f"Empty summary generated for record {content_id}. Attempt {attempt + 1}/{self.max_retries}")
                    continue

                parsed_content = ParsedContent.get_by_id(content_id)
                if not parsed_content:
                    logger.warning(f"ParsedContent not found for id {content_id}")
                    return False

                parsed_content.summary = summary.strip()
                db.session.add(parsed_content)
                db.session.commit()
                logger.info(f"Updated summary for record {content_id}")
                return True

            except Exception as e:
                logger.error(f"Error generating summary for record {content_id}: {str(e)}. Attempt {attempt + 1}/{self.max_retries}", exc_info=True)
                db.session.rollback()

        logger.error(f"Failed to generate summary for record {content_id} after {self.max_retries} attempts.")
        return False

    async def summarize_feed(self, feed_id: str) -> None:
        logger.info(f"Starting summary enhancement for feed {feed_id}")

        feed = RSSFeed.query.get(feed_id)
        if not feed:
            logger.error(f"Feed with id {feed_id} not found")
            return

        parsed_contents = ParsedContent.query.filter_by(feed_id=feed_id, summary=None).all()
        for content in parsed_contents:
            success = await self.process_single_record(content)
            if not success:
                logger.warning(f"Failed to generate summary for content {content.id}")

        logger.info(f"Summary enhancement for feed {feed_id} completed")

    async def process_single_record(self, document: ParsedContent) -> bool:
        logger.info(f"Processing single record {document.id}")
        try:
            summary = await self.generate_summary(str(document.id))
            if not summary:
                logger.warning(f"Empty summary generated for record {document.id}")
                return False

            document.summary = summary.strip()
            db.session.add(document)
            db.session.commit()
            logger.info(f"Updated summary for record {document.id}")
            return True

        except Exception as e:
            logger.error(f"Error processing record {document.id}: {str(e)}", exc_info=True)
            db.session.rollback()
            return False
