import httpx
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11435')
        self.default_model = os.getenv('OLLAMA_MODEL', 'gpt-3.5-turbo')

    async def generate(self, prompt: str, model: str = None, **kwargs) -> Dict[str, Any]:
        """
        Generate a response using the specified Ollama model.

        Args:
            model (str): The name of the Ollama model to use.
            prompt (str): The input prompt for the model.
            **kwargs: Additional parameters to pass to the Ollama API.

        Returns:
            Dict[str, Any]: The response from the Ollama API.
        """
        url = f"{self.base_url}/api/generate"
        payload = {"model": model, "prompt": prompt, **kwargs}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def list_models(self) -> Dict[str, Any]:
        """
        List all available Ollama models.

        Returns:
            Dict[str, Any]: The response from the Ollama API containing the list of models.
        """
        url = f"{self.base_url}/api/tags"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
