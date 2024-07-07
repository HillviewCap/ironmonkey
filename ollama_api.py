import os
from dotenv import load_dotenv
from ollama import Client
from logging_config import logger

load_dotenv()

class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL")
        self.model = os.getenv("OLLAMA_MODEL")
        if not self.base_url or not self.model:
            raise ValueError(
                "OLLAMA_BASE_URL and OLLAMA_MODEL must be set in the .env file"
            )
        self.client = Client(host=self.base_url)

    def check_connection(self) -> bool:
        """
        Check if the Ollama API is accessible.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            self.client.list()
            logger.info(f"Successfully connected to Ollama API at {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API at {self.base_url}: {str(e)}")
            return False

    def generate(self, system_prompt: str, content_to_summarize: str) -> str:
        """
        Generate a response using the Ollama API.

        Args:
            system_prompt (str): The system prompt for the model.
            content_to_summarize (str): The content to be summarized.

        Returns:
            str: The generated text response from the model.
        """
        if not self.check_connection():
            raise Exception(f"Unable to connect to Ollama API at {self.base_url}")

        # Ensure UTF-8 encoding for both prompts
        system_prompt_utf8 = system_prompt.encode('utf-8', errors='ignore').decode('utf-8')
        content_to_summarize_utf8 = content_to_summarize.encode('utf-8', errors='ignore').decode('utf-8')

        # Log the prompts
        logger.debug(f"System Prompt: {system_prompt_utf8}")
        logger.debug(f"Content to Summarize: {content_to_summarize_utf8}")

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt_utf8
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize the following content:\n\n{content_to_summarize_utf8}"
                    }
                ],
                stream=False
            )
            return response['message']['content']
        except Exception as exc:
            logger.error(f"Error occurred: {exc}")
            raise Exception(f"Error occurred: {exc}")
