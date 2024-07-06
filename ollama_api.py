import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'gemma2')

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

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
