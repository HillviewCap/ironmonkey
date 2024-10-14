import os
from datetime import datetime, timedelta
from typing import List, Dict, Union
import json
from app.models.relational.parsed_content import ParsedContent
from app.models import Rollup
from app.utils.experimental_ollama_client import ExperimentalOllamaAPI
from app.utils.groq_api import GroqAPI
from app.utils.elevenlabs_tts import ElevenLabsTTS
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
        
        self.tts = ElevenLabsTTS()

    async def generate_rollup(self, rollup_type: str) -> Dict:
        try:
            content = self._get_content_for_rollup(rollup_type)
            formatted_content = self._format_content(content)
            prompt_type = f"{rollup_type}_rollup_json"
            result = await self.api.generate_json(prompt_type, formatted_content)
            if isinstance(result, dict):
                return result
            elif isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse result as JSON: {result}")
                    return {"error": "Failed to generate valid JSON"}
            else:
                logger.error(f"Unexpected result type: {type(result)}")
                return {"error": "Failed to generate valid JSON"}
        except Exception as e:
            logger.error(f"Error generating {rollup_type} rollup: {str(e)}")
            return {"error": f"Failed to generate {rollup_type} rollup"}

    def generate_audio_rollup(self, rollup_content: Dict, rollup_type: str) -> str:
        try:
            text_to_speak = self._format_rollup_for_speech(rollup_content)
            output_path = os.path.join(os.getcwd(), 'app', 'static', 'audio', f'{rollup_type}_rollup.mp3')
            audio_file = self.tts.generate_audio(text_to_speak, output_path)
            return audio_file
        except Exception as e:
            logger.error(f"Error generating audio rollup: {str(e)}")
            return ""

    def _format_rollup_for_speech(self, rollup_content: Dict) -> str:
        speech_text = f"Here's your {rollup_content.get('timestamp', 'latest')} intelligence briefing.\n\n"
        speech_text += f"Summary: {rollup_content.get('summary', 'No summary available.')}\n\n"
        
        if 'top_stories' in rollup_content:
            speech_text += "Top Stories:\n"
            for story in rollup_content['top_stories']:
                speech_text += f"- {story.get('title', 'Untitled')}: {story.get('summary', 'No summary available.')}\n"
        
        return speech_text

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

    def _format_content(self, content: Union[List[ParsedContent], Dict]) -> str:
        if not content:
            return "No recent news articles found."
        
        if isinstance(content, dict):
            # If content is already a dictionary, return it as a JSON string
            return json.dumps(content, indent=2)
        
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

    async def create_and_store_rollup(self, rollup_type: str):
        rollup_content = await self.generate_rollup(rollup_type)
        audio_file = self.generate_audio_rollup(rollup_content, rollup_type)
        
        # Store the rollup in the database
        rollup = Rollup(
            type=rollup_type,
            content=rollup_content,
            audio_file=audio_file
        )
        db.session.add(rollup)
        db.session.commit()
        
        logger.info(f"Created and stored {rollup_type} rollup")

    @staticmethod
    def get_latest_rollup(rollup_type: str) -> Dict:
        today = datetime.utcnow().date()
        rollup = Rollup.query.filter(
            Rollup.type == rollup_type,
            func.date(Rollup.created_at) == today
        ).order_by(Rollup.created_at.desc()).first()
        if rollup:
            return {
                "content": rollup.content,
                "audio_file": rollup.audio_file,
                "created_at": rollup.created_at
            }
        return None

    @staticmethod
    def get_rollup_types_for_today():
        today = datetime.utcnow().date()
        rollups = Rollup.query.filter(func.date(Rollup.created_at) == today).all()
        return [rollup.type for rollup in rollups]
