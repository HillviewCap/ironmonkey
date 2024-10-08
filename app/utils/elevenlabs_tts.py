import os
from langchain.tools import ElevenLabsText2SpeechTool
from app.utils.logging_config import setup_logger

logger = setup_logger('elevenlabs_tts', 'elevenlabs_tts.log')

class ElevenLabsTTS:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            logger.error("ELEVENLABS_API_KEY must be set in the .env file")
            raise ValueError("ELEVENLABS_API_KEY must be set in the .env file")
        
        self.tts_tool = ElevenLabsText2SpeechTool(elevenlabs_api_key=self.api_key)

    def generate_audio(self, text: str, output_path: str) -> str:
        try:
            audio_file = self.tts_tool.run({
                "text": text,
                "output_path": output_path
            })
            logger.info(f"Generated audio file: {audio_file}")
            return audio_file
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise
