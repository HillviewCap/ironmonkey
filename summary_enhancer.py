# Workflow:
# 1. Initialize SummaryEnhancer with OllamaAPI
# 2. Load prompts from prompts.yaml
# 3. Call enhance_summaries() method
#    a. Query database for ParsedContent with null summary
#    b. For each record:
#       i. Generate summary using OllamaAPI
#       ii. Update ParsedContent with new summary
#       iii. Commit changes to database
#    c. Repeat until no more records to update
# 4. Handle errors and retries
# 5. Log process status and completion

from __future__ import annotations

from logging_config import logger
from sqlalchemy.orm import Session
from models import ParsedContent, db, RSSFeed
from ollama_api import OllamaAPI
import yaml
import httpx
from typing import Dict, Any, Optional


class SummaryEnhancer:
    def __init__(self, ollama_api: OllamaAPI):
        self.ollama_api = ollama_api
        self.prompts = self.load_prompts()
        self.max_retries = 3

    @staticmethod
    def load_prompts() -> Dict[str, Any]:
        try:
            with open('prompts.yaml', 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading prompts: {str(e)}", exc_info=True)
            raise

    async def generate_summary(self, content_id: str) -> str:
        system_prompt = self.prompts['summarize']['system_prompt']
        parsed_content = ParsedContent.get_by_id(content_id)
        if not parsed_content:
            raise ValueError(f"No ParsedContent found with id {content_id}")
        return await self.ollama_api.ask(system_prompt=system_prompt, content_to_summarize=parsed_content.content)

    async def enhance_summary(self, content_id: str) -> bool:
        logger.debug(f"Processing record {content_id}")

        for attempt in range(self.max_retries):
            try:
                summary = await self.generate_summary(content_id)
                if summary:
                    with db.session.begin():
                        parsed_content = ParsedContent.get_by_id(content_id)
                        if parsed_content:
                            parsed_content.summary = summary.strip()
                            db.session.commit()
                            logger.info(f"Updated summary for record {content_id}")
                            logger.debug(f"Summary: {summary}")
                            return True
                        else:
                            logger.warning(f"ParsedContent not found for id {content_id}")
                            return False
                else:
                    logger.warning(f"Empty summary generated for record {content_id}. Attempt {attempt + 1}/{self.max_retries}")
            except httpx.ReadTimeout:
                logger.error(f"Timeout error generating summary for record {content_id}. Attempt {attempt + 1}/{self.max_retries}", exc_info=True)
            except Exception as e:
                logger.error(f"Error generating summary for record {content_id}: {str(e)}. Attempt {attempt + 1}/{self.max_retries}", exc_info=True)

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
            success = await self.process_single_record(content, db.session)
            if not success:
                logger.warning(f"Failed to generate summary for content {content.id}")

        logger.info(f"Summary enhancement for feed {feed_id} completed")

    async def process_single_record(self, document: ParsedContent, session: Session) -> bool:
        logger.debug(f"Processing single record {document.id}")
        try:
            summary = await self.generate_summary(str(document.id))
            if summary:
                document.summary = summary.strip()
                session.commit()
                logger.info(f"Updated summary for record {document.id}")
                return True
            else:
                logger.warning(f"Empty summary generated for record {document.id}")
                return False
        except Exception as e:
            logger.error(f"Error processing record {document.id}: {str(e)}", exc_info=True)
            return False
