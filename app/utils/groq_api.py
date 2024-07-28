"""
GroqAPI: A class to interact with the Groq API for generating summaries.

This class uses the langchain-groq library to make API calls to Groq.
It requires a GROQ_API_KEY to be set in the .env file.

Methods:
    generate(prompt_type: str, article: str) -> str: Generates a summary based on the provided prompt type and article.

This class uses the langchain-groq library to make API calls to Groq.
It requires a GROQ_API_KEY to be set in the .env file.
"""

import os
import yaml
from flask import current_app
from app.utils.logging_config import setup_logger
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage

logger = setup_logger('groq_api', 'groq_api.log')

class GroqAPI:
    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.error("GROQ_API_KEY must be set in the .env file")
            raise ValueError("GROQ_API_KEY must be set in the .env file")
        
        self.model = "mixtral-8x7b-32768"  # You can change this to the desired Groq model
        self.chat_model = ChatGroq(groq_api_key=self.api_key, model_name=self.model)
        self.prompts = self.load_prompts()

    @staticmethod
    def load_prompts():
        prompts_path = os.path.join(current_app.root_path, 'static', 'yaml', 'prompts.yaml')
        with open(prompts_path, "r") as file:
            return yaml.safe_load(file)

    async def generate(self, prompt_type: str, article: str) -> str:
        try:
            prompt_data = self.prompts.get(prompt_type, {})
            system_prompt = prompt_data.get("system_prompt", "")
            full_prompt = f"Human: {system_prompt}\n\n Article: {article}"

            messages = [HumanMessage(content=full_prompt)]
            response = await self.chat_model.ainvoke(messages)
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generating summary with Groq: {str(e)}", exc_info=True)
            raise
