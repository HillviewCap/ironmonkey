import os
import yaml
import asyncio
import dirtyjson as json
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
        self.llm = Ollama(base_url=self.base_url, model=self.model, num_ctx=128000)
        self.prompts = None
        logger.info(f"Initialized ExperimentalOllamaAPI with base_url: {self.base_url} and model: {self.model}")

    def load_prompts(self):
        if self.prompts is None:
            prompts_path = os.path.join(current_app.root_path, 'static', 'yaml', 'experimental_prompts.yaml')
            with open(prompts_path, "r") as file:
                self.prompts = yaml.safe_load(file)
        return self.prompts

    async def _generate_json_with_retry(self, prompt_type: str, article: str, max_retries: int = 3) -> dict:
        prompts = self.load_prompts()
        prompt_data = prompts.get(prompt_type, {})
        system_prompt = prompt_data.get("system_prompt", "")
        full_prompt = f"Human: {system_prompt}\n\nArticle: {article}\n\nRespond with a valid JSON object."

        for attempt in range(max_retries):
            try:
                output = await asyncio.get_event_loop().run_in_executor(
                    None, partial(self.llm.invoke, full_prompt)
                )

                if current_app.debug:
                    logger.debug(f"Generated response (attempt {attempt + 1}): {output}")

                # Use dirtyjson to parse the entire output
                try:
                    json_output = json.loads(output)
                    return json_output
                except json.Error as e:
                    logger.warning(f"Failed to parse JSON (attempt {attempt + 1}): {e}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Wait for 1 second before retrying
            except Exception as exc:
                logger.error(f"Error occurred while generating response (attempt {attempt + 1}): {exc}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Wait for 1 second before retrying

        return {"error": "Failed to generate valid JSON after multiple attempts"}

    async def generate_json(self, prompt_type: str, article: str) -> dict:
        """Generate a JSON response based on the prompt type and article."""
        try:
            return await self._generate_json_with_retry(prompt_type, article)
        except Exception as exc:
            logger.error(f"Error occurred while generating response: {exc}")
            raise RuntimeError(f"Error occurred while generating response: {exc}")

    async def generate_json_stream(self, prompt_type: str, article: str):
        chunk_size = 4000  # Adjust based on your model's context window size and needs
        chunks = [article[i:i+chunk_size] for i in range(0, len(article), chunk_size)]

        results = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1} of {len(chunks)}")
            result = await self.generate_json(prompt_type, chunk)
            results.append(result)

        # Combine results from all chunks
        merged_result = self.merge_results(results)
        return merged_result

    def merge_results(self, results):
        merged_result = {}

        for result in results:
            for key, value in result.items():
                if key not in merged_result:
                    merged_result[key] = value
                else:
                    if isinstance(value, list):
                        # Ensure merged_result[key] is a list
                        if not isinstance(merged_result[key], list):
                            merged_result[key] = [merged_result[key]] if merged_result[key] else []
                        merged_result[key].extend(value)
                    elif isinstance(value, dict):
                        # Merge dictionaries (shallow merge)
                        merged_result[key] = {**merged_result[key], **value}
                    elif isinstance(value, str):
                        # Concatenate strings with a space separator
                        merged_result[key] = f"{merged_result[key]} {value}"
                    else:
                        # Handle other data types as needed
                        merged_result[key] = value  # Overwrite or define custom logic

        return merged_result
        try:
            test_prompt = "Respond with a JSON object containing the key 'status' and value 'ok'."
            response = await asyncio.get_event_loop().run_in_executor(
                None, partial(self.llm.invoke, test_prompt)
            )
            try:
                json_response = json.loads(response)
                if json_response.get('status') == 'ok':
                    if current_app.debug:
                        logger.info(f"Successfully connected to Ollama API at {self.base_url} with model: {self.model}")
                    return True
                return False
            except json.Error as e:
                logger.error(f"Failed to parse JSON response during connection check: {e}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama API at {self.base_url}: {str(e)}")
            return False

    def check_connection_sync(self) -> bool:
        return asyncio.run(self.check_connection())
