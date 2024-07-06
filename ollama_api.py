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

    async def generate(self, prompt: str) -> dict:
        """
        Generate a response using the Ollama API.

        Args:
            prompt (str): The input prompt for the model.

        Returns:
            dict: The API response containing the generated text.
        """
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
