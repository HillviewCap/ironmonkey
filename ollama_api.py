import os
import yaml
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from logging_config import logger

load_dotenv()

class OllamaAPI:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL")
        self.model = os.getenv("OLLAMA_MODEL")
        if not self.base_url:
            raise ValueError("OLLAMA_BASE_URL must be set in the .env file")
        self.llm = Ollama(base_url=self.base_url, model=self.model)
        self.prompts = self.load_prompts()

    @staticmethod
    def load_prompts():
        with open('prompts.yaml', 'r') as file:
            return yaml.safe_load(file)

    async def generate(self, prompt_type: str, article: str) -> str:
        try:
            prompt_data = self.prompts.get(prompt_type, {})
            system_prompt = prompt_data.get('system_prompt', '')
            full_prompt = f"System: {system_prompt}\n\nHuman: Analyze the following article:\n\nArticle: {article}"
            output = self.llm(full_prompt)
            logger.debug(f"Generated response: {output}")
            return output
        except Exception as exc:
            logger.error(f"Error occurred: {exc}")
            raise Exception(f"Error occurred: {exc}")

    def check_connection(self) -> bool:
        try:
            # A simple prompt to test the connection
            test_prompt = "Hello, are you working?"
            response = self.llm(test_prompt)
            logger.info(f"Successfully connected to Ollama API at {self.base_url} and verified model {self.model}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API at {self.base_url}: {str(e)}")
            return False
