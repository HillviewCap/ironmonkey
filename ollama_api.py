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
        try:
            models = self.client.list()
            available_models = [model["name"] for model in models["models"]]
            if self.model not in available_models:
                logger.error(
                    f"Model {self.model} is not available. Available models: {available_models}"
                )
                return False
            logger.info(
                f"Successfully connected to Ollama API at {self.base_url} and verified model {self.model}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to connect to Ollama API at {self.base_url}: {str(e)}"
            )
            return False

    async def generate(
        self, system_prompt: str, content_to_summarize: str, temperature: float = 0.7
    ) -> str:
        if not self.check_connection():
            raise Exception(
                f"Unable to connect to Ollama API at {self.base_url} or model {self.model} is not available"
            )

        system_prompt_utf8 = system_prompt.encode("utf-8", errors="ignore").decode(
            "utf-8"
        )
        content_to_summarize_utf8 = content_to_summarize.encode(
            "utf-8", errors="ignore"
        ).decode("utf-8")

        logger.debug(f"System Prompt: {system_prompt_utf8}")
        logger.debug(f"Content to Summarize: {content_to_summarize_utf8}")

        try:
            response = await self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt_utf8},
                    {
                        "role": "user",
                        "content": f"Please summarize the following content:\n\n{content_to_summarize_utf8}",
                    },
                ],
                stream=False,
                options={
                    "temperature": temperature,
                    "num_predict": 4000,  # Adjust this based on your model's capabilities
                },
            )
            generated_text = response["message"]["content"]
            logger.debug(f"Generated response: {generated_text}")
            return generated_text
        except Exception as exc:
            logger.error(f"Error occurred: {exc}")
            raise Exception(f"Error occurred: {exc}")
