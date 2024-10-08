import os
from datetime import datetime
from typing import List, Dict
from app.models.relational.parsed_content import ParsedContent
from app.utils.ollama_client import OllamaAPI
from app.utils.groq_api import GroqAPI
from app.utils.logging_config import setup_logger
from app.extensions import db

logger = setup_logger('news_rollup_service', 'news_rollup_service.log')

class NewsRollupService:
    def __init__(self):
        api_choice = os.getenv("SUMMARY_API_CHOICE", "ollama").lower()
        if api_choice == "ollama":
            self.api = OllamaAPI()
        elif api_choice == "groq":
            self.api = GroqAPI()
        else:
            raise ValueError(f"Invalid SUMMARY_API_CHOICE: {api_choice}")

    async def generate_rollup(self, rollup_type: str) -> str:
        content = self._get_content_for_rollup(rollup_type)
        formatted_content = self._format_content(content)
        prompt_type = f"{rollup_type}_rollup"
        return await self.api.generate(prompt_type, formatted_content)

    def _get_content_for_rollup(self, rollup_type: str) -> List[ParsedContent]:
        now = datetime.utcnow()
        today = now.date().isoformat()
        if rollup_type == "morning":
            start_time = f"{today}T00:00:00"
            end_time = f"{today}T12:00:00"
        elif rollup_type == "midday":
            start_time = f"{today}T12:00:00"
            end_time = f"{today}T18:00:00"
        elif rollup_type == "end_of_day":
            start_time = f"{today}T18:00:00"
            end_time = f"{today}T23:59:59"
        else:
            raise ValueError(f"Invalid rollup_type: {rollup_type}")

        return ParsedContent.query.filter(
            ParsedContent.pub_date.between(start_time, end_time)
        ).order_by(ParsedContent.pub_date.desc()).all()

    def _format_content(self, content: List[ParsedContent]) -> str:
        formatted_content = ""
        for item in content:
            formatted_content += f"Title: {item.title}\n"
            formatted_content += f"Description: {item.description}\n"
            formatted_content += f"Summary: {item.summary}\n"
            formatted_content += f"Source URL: {item.url}\n\n"
        return formatted_content

    async def generate_all_rollups(self) -> Dict[str, str]:
        return {
            "morning": await self.generate_rollup("morning"),
            "midday": await self.generate_rollup("midday"),
            "end_of_day": await self.generate_rollup("end_of_day")
        }
