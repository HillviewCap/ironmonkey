import os
from datetime import datetime, timedelta
from typing import List, Dict
from app.models.relational.parsed_content import ParsedContent
from app.utils.experimental_ollama_client import ExperimentalOllamaAPI
from app.utils.groq_api import GroqAPI
from app.utils.logging_config import setup_logger
from app.extensions import db
from sqlalchemy import func

logger = setup_logger('news_rollup_service', 'news_rollup_service.log')

class NewsRollupService:
    def __init__(self):
        api_choice = os.getenv("SUMMARY_API_CHOICE", "ollama").lower()
        if api_choice == "ollama":
            self.api = ExperimentalOllamaAPI()
        elif api_choice == "groq":
            self.api = GroqAPI()
        else:
            raise ValueError(f"Invalid SUMMARY_API_CHOICE: {api_choice}")

    async def generate_rollup(self, rollup_type: str) -> Dict:
        content = self._get_content_for_rollup(rollup_type)
        formatted_content = self._format_content(content)
        prompt_type = f"{rollup_type}_rollup_json"
        return await self.api.generate_json(prompt_type, formatted_content)

    def _get_content_for_rollup(self, rollup_type: str) -> List[ParsedContent]:
        now = datetime.utcnow()
        today = now.date()
        
        if rollup_type == "morning":
            start_time = datetime.combine(today, datetime.min.time())
            end_time = datetime.combine(today, datetime.strptime("12:00:00", "%H:%M:%S").time())
        elif rollup_type == "midday":
            start_time = datetime.combine(today, datetime.strptime("12:00:00", "%H:%M:%S").time())
            end_time = datetime.combine(today, datetime.strptime("18:00:00", "%H:%M:%S").time())
        elif rollup_type == "end_of_day":
            start_time = datetime.combine(today, datetime.strptime("18:00:00", "%H:%M:%S").time())
            end_time = datetime.combine(today + timedelta(days=1), datetime.min.time())
        else:
            raise ValueError(f"Invalid rollup_type: {rollup_type}")

        content = ParsedContent.query.filter(
            ParsedContent.pub_date.between(start_time, end_time)
        ).order_by(ParsedContent.pub_date.desc()).limit(10).all()

        if not content:
            # If no content found for the specified time range, get the latest 10 entries
            content = ParsedContent.query.order_by(ParsedContent.pub_date.desc()).limit(10).all()

        return content

    def _format_content(self, content: List[ParsedContent]) -> str:
        if not content:
            return "No recent news articles found."
        
        formatted_content = ""
        for item in content:
            formatted_content += f"Title: {item.title}\n"
            formatted_content += f"Published: {item.pub_date.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            formatted_content += f"Description: {item.description or 'No description available'}\n"
            formatted_content += f"Summary: {item.summary or 'No summary available'}\n"
            formatted_content += f"Source URL: {item.url}\n\n"
        return formatted_content

    async def generate_all_rollups(self) -> Dict[str, Dict]:
        return {
            "morning": await self.generate_rollup("morning"),
            "midday": await self.generate_rollup("midday"),
            "end_of_day": await self.generate_rollup("end_of_day")
        }
