import os
from dotenv import load_dotenv
from ollama import Client
from logging_config import logger

load_dotenv()

class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL")
        self.model = os.getenv("OLLAMA_MODEL", "llama3:latest")
        if not self.base_url:
            raise ValueError("OLLAMA_BASE_URL must be set in the .env file")
        self.client = Client(host=self.base_url)
        self.keep_alive = 60  # Added keep_alive parameter

    async def generate(self, system_prompt: str, content_to_summarize: str) -> str:
        try:
            response = self.client.generate(
                model=self.model,
                prompt=content_to_summarize,
                system=system_prompt,
                keep_alive=self.keep_alive
            )
            generated_text = response["response"]
            logger.debug(f"Generated response: {generated_text}")
            return generated_text
        except Exception as exc:
            logger.error(f"Error occurred: {exc}")
            raise Exception(f"Error occurred: {exc}")

    # You may want to keep a simplified version of the check_connection method
    def check_connection(self) -> bool:
        try:
            models = self.client.list()
            available_models = [model["name"] for model in models["models"]]
            if self.model not in available_models:
                logger.error(f"Model {self.model} is not available. Available models: {available_models}")
                return False
            logger.info(f"Successfully connected to Ollama API at {self.base_url} and verified model {self.model}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API at {self.base_url}: {str(e)}")
            return False
