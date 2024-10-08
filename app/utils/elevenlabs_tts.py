import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from app.utils.logging_config import setup_logger

logger = setup_logger('elevenlabs_tts', 'elevenlabs_tts.log')

class ElevenLabsTTS:
    def __init__(self):
        self.api_key = os.getenv("ELEVEN_API_KEY")
        if not self.api_key:
            logger.error("ELEVEN_API_KEY must be set in the .env file")
            raise ValueError("ELEVEN_API_KEY must be set in the .env file")
        
        self.client = ElevenLabs(api_key=self.api_key)

    def generate_audio(self, text: str, output_path: str) -> str:
        try:
            response = self.client.text_to_speech.convert(
                voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
                output_format="mp3_22050_32",
                text=text,
                model_id="eleven_turbo_v2_5",  # use the turbo model for low latency
                voice_settings=VoiceSettings(
                    stability=0.0,
                    similarity_boost=1.0,
                    style=0.0,
                    use_speaker_boost=True,
                ),
            )

            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Writing the audio to the specified file
            with open(output_path, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)

            logger.info(f"Generated audio file: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise
