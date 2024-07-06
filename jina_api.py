import httpx
import os
import asyncio
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry

load_dotenv()

JINA_API_KEY = os.getenv('JINA_API_KEY')

# Rate limit: 200 requests per minute
@sleep_and_retry
@limits(calls=200, period=60)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def parse_content(url: str) -> dict:
    """
    Parse content using the Jina API.

    Args:
        url (str): The URL to parse.

    Returns:
        dict: Parsed content including title, url, content, and links.
    """
    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "X-With-Generated-Alt": "true",
        "X-With-Links-Summary": "true",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f'https://r.jina.ai/{url}', headers=headers)
        response.raise_for_status()
        data = response.json()['data']
        
        return {
            'title': data['title'],
            'url': data['url'],
            'content': data['content'],
            'links': data['links']
        }
