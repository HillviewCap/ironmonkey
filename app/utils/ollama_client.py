import os
import os
import yaml
import asyncio
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from app.utils.logging_config import setup_logger
from functools import partial

# Create a separate logger for Ollama API
logger = setup_logger('ollama_api', 'ollama_api.log')
from flask import current_app

load_dotenv()


class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL")
        if not self.base_url.startswith("http://") and not self.base_url.startswith("https://"):
            self.base_url = "http://" + self.base_url
        self.model = os.getenv("OLLAMA_MODEL")
        if not self.base_url:
            logger.error("OLLAMA_BASE_URL must be set in the .env file")
            raise ValueError("OLLAMA_BASE_URL must be set in the .env file")
        if not self.model:
            logger.error("OLLAMA_MODEL must be set in the .env file")
            raise ValueError("OLLAMA_MODEL must be set in the .env file")
        self.llm = Ollama(base_url=self.base_url, model=self.model, num_ctx=8200)
        self.prompts = None
        logger.info(f"Initialized OllamaAPI with base_url: {self.base_url} and model: {self.model}")

    @classmethod
    def initialize_if_ollama(cls):
        if os.getenv("SUMMARY_API_CHOICE", "ollama").lower() == "ollama":
            return cls()
        return None

    def load_prompts(self):
        if self.prompts is None:
            prompts_path = os.path.join(current_app.root_path, 'static', 'yaml', 'prompts.yaml')
            with open(prompts_path, "r") as file:
                self.prompts = yaml.safe_load(file)
        return self.prompts

    async def generate(self, prompt_type: str, article: str) -> str:
        """Generate a response based on the prompt type and article."""
        try:
            prompts = self.load_prompts()
            prompt_data = prompts.get(prompt_type, {})
            system_prompt = prompt_data.get("system_prompt", "")
            full_prompt = f"Human: {system_prompt}\n\n Article: {article}"

            output = await asyncio.get_event_loop().run_in_executor(
                None, partial(self.llm.invoke, full_prompt)
            )

            if current_app.debug:
                logger.debug(f"Generated response: {output}")
            return output
        except Exception as exc:
            logger.error(f"Error occurred while generating response: {exc}")
            raise RuntimeError(f"Error occurred while generating response: {exc}")

    async def check_connection(self) -> bool:
        try:
            # A simple prompt to test the connection
            test_prompt = "Hello, are you working?"
            response = await asyncio.get_event_loop().run_in_executor(
                None, partial(self.llm.invoke, test_prompt)
            )
            if current_app.debug:
                logger.info(f"Successfully connected to Ollama API at {self.base_url} with model: {self.model}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to connect to Ollama API at {self.base_url}: {str(e)}"
            )
            return False

    def check_connection_sync(self) -> bool:
        return asyncio.run(self.check_connection())
