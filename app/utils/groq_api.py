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
from logging_config import setup_logger
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

    async def generate(self, prompt_type: str, article: str) -> str:
        try:
            if prompt_type == "threat_intel_summary":
                prompt = f"Please provide a concise summary of the following threat intelligence article, highlighting key points and potential impacts:\n\n{article}"
            elif prompt_type not in ["threat_intel_summary"]:
                raise ValueError(f"Unsupported prompt type: {prompt_type}")
                raise ValueError(f"Unsupported prompt type: {prompt_type}")

            messages = [HumanMessage(content=prompt)]
            response = await self.chat_model.ainvoke(messages)
            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generating summary with Groq: {str(e)}", exc_info=True)
            raise
