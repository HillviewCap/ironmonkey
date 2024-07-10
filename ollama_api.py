import os
import yaml
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from logging_config import logger
import asyncio
from functools import partial

load_dotenv()


class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL")
        self.model = os.getenv("OLLAMA_MODEL")
        if not self.base_url:
            raise ValueError("OLLAMA_BASE_URL must be set in the .env file")
        if not self.model:
            raise ValueError("OLLAMA_MODEL must be set in the .env file")
        self.llm = Ollama(base_url=self.base_url, model=self.model, num_ctx=32000, num_gpu=1)
        self.prompts = self.load_prompts()
        logger.info(
            f"Initialized OllamaAPI with base_url: {self.base_url} and model: {self.model}"
        )

    @staticmethod
    def load_prompts():
        with open("prompts.yaml", "r") as file:
            return yaml.safe_load(file)

    async def generate(self, prompt_type: str, article: str) -> str:
        try:
            prompt_data = self.prompts.get(prompt_type, {})
            system_prompt = prompt_data.get("system_prompt", "")
            full_prompt = f"System: You are a world renowned cybersecurity researcher tasked with summarizing cybersecurity blog posts and news articles:\n\nHuman: {system_prompt}\n\n Article: {article}"

            output = await asyncio.get_event_loop().run_in_executor(
                None, partial(self.llm.invoke, full_prompt)
            )

            logger.debug(f"Generated response: {output}")
            return output
        except Exception as exc:
            logger.error(f"Error occurred: {exc}")
            raise Exception(f"Error occurred: {exc}")

    async def check_connection(self) -> bool:
        try:
            # A simple prompt to test the connection
            test_prompt = "Hello, are you working?"
            response = await asyncio.get_event_loop().run_in_executor(
                None, partial(self.llm.invoke, test_prompt)
            )
            logger.info(
                f"Successfully connected to Ollama API at {self.base_url} and verified model {self.model}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to connect to Ollama API at {self.base_url}: {str(e)}"
            )
            return False
