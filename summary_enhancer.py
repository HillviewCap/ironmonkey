import logging
from sqlalchemy.orm import Session
from models import ParsedContent, db
from ollama_api import OllamaAPI
import yaml
import httpx

logger = logging.getLogger(__name__)

class SummaryEnhancer:
    def __init__(self, ollama_api: OllamaAPI):
        self.ollama_api = ollama_api
        self.prompts = self.load_prompts()

    @staticmethod
    def load_prompts():
        with open('prompts.yaml', 'r') as file:
            return yaml.safe_load(file)

    async def process_single_record(self, record: ParsedContent, session: Session) -> bool:
        logger.debug(f"Processing record {record.id}")
        system_prompt = self.prompts['summarize']['system_prompt']
        user_prompt = record.content

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.ollama_api.ask(system_prompt=system_prompt, user_prompt=user_prompt)
                summary = response.strip()

                if summary:
                    record.summary = summary
                    session.commit()
                    logger.info(f"Updated summary for record {record.id}")
                    logger.info(f"Summary: {summary}")
                    return True
                else:
                    logger.warning(f"Empty summary generated for record {record.id}. Attempt {attempt + 1}/{max_retries}")
            except httpx.ReadTimeout:
                logger.error(f"Timeout error generating summary for record {record.id}. Attempt {attempt + 1}/{max_retries}", exc_info=True)
            except Exception as e:
                logger.error(f"Error generating summary for record {record.id}: {str(e)}. Attempt {attempt + 1}/{max_retries}", exc_info=True)

        logger.error(f"Failed to generate summary for record {record.id} after {max_retries} attempts.")
        return False

    async def enhance_summaries(self):
        logger.info("Starting summary enhancement process")

        while True:
            try:
                with db.session.begin():
                    record_to_update = db.session.query(ParsedContent).filter(ParsedContent.summary.is_(None)).with_for_update().first()

                    if not record_to_update:
                        logger.info("No more records to update. Process completed.")
                        break

                    success = await self.process_single_record(record_to_update, db.session)
                    if not success:
                        logger.warning(f"Moving to next record after failed attempts for record {record_to_update.id}")

            except Exception as e:
                logger.error(f"Error during summary enhancement: {str(e)}", exc_info=True)

        logger.info("Summary enhancement process completed")
