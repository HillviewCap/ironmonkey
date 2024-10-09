import os
import yaml
import asyncio
import json
import re
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from app.utils.logging_config import setup_logger
from functools import partial
from flask import current_app

logger = setup_logger('experimental_ollama_api', 'experimental_ollama_api.log')

load_dotenv()

class ExperimentalOllamaAPI:
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
        logger.info(f"Initialized ExperimentalOllamaAPI with base_url: {self.base_url} and model: {self.model}")

    def load_prompts(self):
        if self.prompts is None:
            prompts_path = os.path.join(current_app.root_path, 'static', 'yaml', 'experimental_prompts.yaml')
            with open(prompts_path, "r") as file:
                self.prompts = yaml.safe_load(file)
        return self.prompts

    async def generate_json(self, prompt_type: str, article: str) -> dict:
        """Generate a JSON response based on the prompt type and article."""
        try:
            prompts = self.load_prompts()
            prompt_data = prompts.get(prompt_type, {})
            system_prompt = prompt_data.get("system_prompt", "")
            full_prompt = f"Human: {system_prompt}\n\nArticle: {article}\n\nRespond with a valid JSON object."

            output = await asyncio.get_event_loop().run_in_executor(
                None, partial(self.llm.invoke, full_prompt)
            )

            if current_app.debug:
                logger.debug(f"Generated response: {output}")
            
            # Use regex to extract JSON object
            json_match = re.search(r'(\{.*\})', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                # Attempt to parse the extracted JSON
                try:
                    json_output = json.loads(json_str)
                    return json_output
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse extracted JSON: {e}")
                    return {"error": "Failed to parse extracted JSON"}
            else:
                logger.error("No JSON object found in the response")
                return {"error": "No JSON object found in the response"}

        except Exception as exc:
            logger.error(f"Error occurred while generating response: {exc}")
            raise RuntimeError(f"Error occurred while generating response: {exc}")

    async def check_connection(self) -> bool:
        try:
            test_prompt = "Respond with a JSON object containing the key 'status' and value 'ok'."
            response = await asyncio.get_event_loop().run_in_executor(
                None, partial(self.llm.invoke, test_prompt)
            )
            json_response = json.loads(response)
            if json_response.get('status') == 'ok':
                if current_app.debug:
                    logger.info(f"Successfully connected to Ollama API at {self.base_url} with model: {self.model}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API at {self.base_url}: {str(e)}")
            return False

    def check_connection_sync(self) -> bool:
        return asyncio.run(self.check_connection())
