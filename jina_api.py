import httpx
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from ratelimit import limits, sleep_and_retry
import logging
from logging_config import setup_logger

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")

# Set up logger
logger = setup_logger("jina_api", "jina_api.log")


# Rate limit: 200 requests per minute
@sleep_and_retry
@limits(calls=200, period=60)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def parse_content(url: str) -> str:
    """
    Parse content using the Jina API.

    Args:
        url (str): The URL to parse.

    Returns:
        str: Parsed text content.
    """
    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "X-Return-Format": "text",
        "Accept": "application/json",
    }

    logger.info(f"Parsing content from URL: {url}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"https://r.jina.ai/{url}", headers=headers)
            response.raise_for_status()
            data = response.json()

            if data["code"] != 200 or data["status"] != 20000:
                logger.error(
                    f"API returned unexpected status. Code: {data['code']}, Status: {data['status']}"
                )
                return None

            return data["data"]["text"]
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None


async def update_content_in_database(post_id: str, content: str):
    """
    Update the content field in the database for the given post.

    Args:
        post_id (str): The ID of the post to update.
        content (str): The new content to set.
    """
    # This is a placeholder function. You need to implement the actual database update logic.
    logger.info(f"Updating content for post ID: {post_id}")
    # Your database update code here
    pass


async def process_url(url: str, post_id: str):
    """
    Process a URL: parse its content and update the database.

    Args:
        url (str): The URL to process.
        post_id (str): The ID of the associated post in the database.
    """
    content = await parse_content(url)
    if content:
        await update_content_in_database(post_id, content)
        logger.info(f"Successfully processed URL: {url}")
    else:
        logger.warning(f"Failed to process URL: {url}")
