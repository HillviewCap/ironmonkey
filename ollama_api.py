import os
import asyncio
from dotenv import load_dotenv
from ollama import AsyncClient
from logging_config import logger

load_dotenv()


class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL")
        self.model = os.getenv("OLLAMA_MODEL")
        self.app_secret = os.getenv("APP_SECRET")
        if not self.base_url or not self.model or not self.app_secret:
            raise ValueError(
                "OLLAMA_BASE_URL, OLLAMA_MODEL, and APP_SECRET must be set in the .env file"
            )
        self.max_retries = 5
        self.timeout = 60.0  # 60 seconds timeout
        self.client = AsyncClient(host=self.base_url)

    async def check_connection(self, app_secret: str) -> bool:
        """
        Check if the Ollama API is accessible and the app_secret is correct.

        Args:
            app_secret (str): The secret key for app authentication.

        Returns:
            bool: True if the connection is successful and authenticated, False otherwise.
        """
        if app_secret != self.app_secret:
            logger.error("Invalid app_secret provided")
            return False

        try:
            await self.client.list()
            logger.info(f"Successfully connected to Ollama API at {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API at {self.base_url}: {str(e)}")
            return False

    async def generate(self, system_prompt: str, user_prompt: str, app_secret: str) -> dict:
        """
        Generate a response using the Ollama API.

        Args:
            system_prompt (str): The system prompt for the model.
            user_prompt (str): The user prompt for the model.
            app_secret (str): The secret key for app authentication.

        Returns:
            dict: The API response containing the generated text.
        """
        if not await self.check_connection(app_secret):
            raise Exception(f"Unable to connect to Ollama API at {self.base_url} or invalid app_secret")

        # Ensure UTF-8 encoding for both prompts
        system_prompt_utf8 = system_prompt.encode('utf-8', errors='ignore').decode('utf-8')
        user_prompt_utf8 = user_prompt.encode('utf-8', errors='ignore').decode('utf-8')

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt_utf8},
                        {"role": "user", "content": user_prompt_utf8}
                    ]
                )
                return response
            except asyncio.TimeoutError:
                logger.error(f"Timeout error occurred (attempt {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Timeout error occurred after {self.max_retries} attempts")
                await asyncio.sleep(2**attempt)  # Exponential backoff
            except Exception as exc:
                logger.error(f"Error occurred (attempt {attempt + 1}/{self.max_retries}): {exc}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Error occurred after {self.max_retries} attempts: {exc}")
                await asyncio.sleep(2**attempt)  # Exponential backoff

    async def ask(self, system_prompt: str, user_prompt: str, app_secret: str) -> str:
        """
        Ask a question to the Ollama model.

        Args:
            system_prompt (str): The system prompt for the model.
            user_prompt (str): The user prompt for the model.
            app_secret (str): The secret key for app authentication.

        Returns:
            str: The response from the model.
        """
        response = await self.generate(system_prompt, user_prompt, app_secret)
        return response["message"]["content"]
