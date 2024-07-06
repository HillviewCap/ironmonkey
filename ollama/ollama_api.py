import httpx
from typing import Dict, Any


class OllamaAPI:
    def __init__(self, base_url: str = "http://localhost:11435"):
        self.base_url = base_url

    async def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
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
