import httpx
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
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
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError, ValueError, KeyError)),
    before_sleep=before_sleep_log(logger, logging.ERROR)
)
async def parse_content(url: str) -> str:
    """
    Parse content using the Jina API.

    Args:
        url (str): The URL to parse.

    Returns:
        str: Parsed text content or None if an error occurs.
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
                    f"API returned unexpected status for URL {url}. Code: {data['code']}, Status: {data['status']}"
                )
                return None

            logger.info(f"Successfully parsed content from URL: {url}")
            return data["data"]["text"]
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred while parsing URL {url}: {str(e)}", exc_info=True)
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error occurred while parsing URL {url}: {str(e)}", exc_info=True)
            return None
        except ValueError as e:
            logger.error(f"JSON decoding error occurred while parsing URL {url}: {str(e)}", exc_info=True)
            return None
        except KeyError as e:
            logger.error(f"Unexpected API response structure for URL {url}: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while parsing URL {url}: {str(e)}", exc_info=True)
            return None


async def update_content_in_database(post_id: str, content: str):
    """
    Update the content field in the database for the given post.

    Args:
        post_id (str): The ID of the post to update.
        content (str): The new content to set.
    """
    # This is a placeholder function. You need to implement the actual database update logic.
    try:
        logger.info(f"Updating content for post ID: {post_id}")
        # Your database update code here
        logger.info(f"Successfully updated content for post ID: {post_id}")
    except Exception as e:
        logger.error(f"Failed to update content for post ID {post_id}: {e}")


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
        logger.info(f"Successfully processed URL: {url} for post ID: {post_id}")
    else:
        logger.warning(f"Failed to process URL: {url} for post ID: {post_id}")
