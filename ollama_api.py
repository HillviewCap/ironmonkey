import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'gemma2')
        self.max_retries = 3
        self.timeout = 30.0  # 30 seconds timeout

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

    async def check_model(self) -> bool:
        """
        Check if the specified model is available and loaded.

        Returns:
            bool: True if the model is available and loaded, False otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/ps")
                response.raise_for_status()
                data = response.json()
                return any(model['model'] == self.model for model in data.get('models', []))
        except (httpx.RequestError, httpx.HTTPStatusError):
            return False

    async def generate(self, prompt: str) -> dict:
        """
        Generate a response using the Ollama API.

        Args:
            prompt (str): The input prompt for the model.

        Returns:
            dict: The API response containing the generated text.
        """
        if not await self.check_connection():
            raise Exception("Unable to connect to Ollama API")

        if not await self.check_model():
            raise Exception(f"Model '{self.model}' is not available or loaded")

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
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
                raise Exception(f"HTTP error occurred: {exc}")
