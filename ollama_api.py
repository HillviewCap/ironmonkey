import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL')
        self.model = os.getenv('OLLAMA_MODEL')
        if not self.base_url or not self.model:
            raise ValueError("OLLAMA_BASE_URL and OLLAMA_MODEL must be set in the .env file")
        self.max_retries = 5
        self.timeout = 60.0  # 60 seconds timeout

    async def check_connection(self) -> bool:
        """
        Check if the Ollama API is accessible.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/ps")
                response.raise_for_status()
                return True
        except (httpx.RequestError, httpx.HTTPStatusError):
            return False

    async def generate(self, prompt: str, content: str = "") -> dict:
        """
        Generate a response using the Ollama API.

        Args:
            prompt (str): The input prompt for the model.
            content (str): The content to be appended to the prompt.

        Returns:
            dict: The API response containing the generated text.
        """
        if not await self.check_connection():
            raise Exception("Unable to connect to Ollama API")

        url = f"{self.base_url}/api/generate"
        full_prompt = f"{prompt}\n{content}" if content else prompt
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json()
            except httpx.ReadTimeout:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except httpx.HTTPStatusError as exc:
                if attempt == self.max_retries - 1:
                    raise Exception(f"HTTP error occurred: {exc}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
