import os
import asyncio
from dotenv import load_dotenv
from ollama import AsyncClient

load_dotenv()


class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL")
        self.model = os.getenv("OLLAMA_MODEL")
        if not self.base_url or not self.model:
            raise ValueError(
                "OLLAMA_BASE_URL and OLLAMA_MODEL must be set in the .env file"
            )
        self.max_retries = 5
        self.timeout = 60.0  # 60 seconds timeout
        self.client = AsyncClient(host=self.base_url)

    async def check_connection(self) -> bool:
        """
        Check if the Ollama API is accessible.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        try:
            await self.client.list()
            return True
        except Exception:
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

        full_prompt = f"{prompt}\n{content}" if content else prompt

        for attempt in range(self.max_retries):
            try:
                response = await self.client.generate(
                    model=self.model, prompt=full_prompt
                )
                return response
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)  # Exponential backoff
            except Exception as exc:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Error occurred: {exc}")
                await asyncio.sleep(2**attempt)  # Exponential backoff

    async def ask(self, system_prompt: str, user_prompt: str) -> str:
        """
        Ask a question to the Ollama model.

        Args:
            system_prompt (str): The system prompt for the model.
            user_prompt (str): The user prompt for the model.

        Returns:
            str: The response from the model.
        """
        if not await self.check_connection():
            raise Exception("Unable to connect to Ollama API")

        response = await self.generate(system_prompt, user_prompt)
        return response["choices"]["text"]


# Example usage
async def main():
    api = OllamaAPI()
    system_prompt = (
        "You are an unhelpful and sarcastic AI that enjoys making fun of humans."
    )
    user_prompt = "Hello large language model. How are you doing?"
    response = await api.ask(system_prompt, user_prompt)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
