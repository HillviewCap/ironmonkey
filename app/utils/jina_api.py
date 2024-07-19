import httpx
from httpx import ReadTimeout
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
from ratelimit import limits, sleep_and_retry
import logging
from logging_config import setup_logger
from cachetools import TTLCache
from functools import lru_cache

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")

# Set up logger
logger = setup_logger("jina_api", "jina_api.log")

# Create a TTL cache with a maximum of 1000 items and a 1-hour expiration
content_cache = TTLCache(maxsize=1000, ttl=3600)


async def follow_redirects(url: str) -> str:
    """Follow redirects and return the final URL."""
    """
    Follow redirects and return the final URL.

    Args:
        url (str): The initial URL.

    Returns:
        str: The final URL after following all redirects.
    """
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url)
        return str(response.url)


# Rate limit: 200 requests per minute
@sleep_and_retry
@limits(calls=200, period=60)
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError, ReadTimeout, ValueError, KeyError)),
    before_sleep=before_sleep_log(logger, logging.ERROR)
)
async def parse_content(url: str) -> str:
    """Parse content using the Jina API and return the parsed text."""
    """
    Parse content using the Jina API.

    Args:
        url (str): The URL to parse.

    Returns:
        str: Parsed text content or None if an error occurs.
    """
    # Check if the content is already in the cache
    if url in content_cache:
        logger.info(f"Retrieved cached content for URL: {url}")
        return content_cache[url]

    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "X-Return-Format": "text",
        "Accept": "application/json",
    }

    logger.info(f"Parsing content from URL: {url}")

    try:
        # Follow redirects to get the final URL
        final_url = await follow_redirects(url)
        logger.info(f"Final URL after redirects: {final_url}")

        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://r.jina.ai/{final_url}", headers=headers, timeout=60.0)
            response.raise_for_status()
            data = response.json()

            if data["code"] != 200 or data["status"] != 20000:
                logger.error(
                    f"API returned unexpected status for URL {final_url}. Code: {data['code']}, Status: {data['status']}"
                )
                return None

            content = data["data"]["text"]
            logger.info(f"Successfully parsed content from URL: {final_url}")
            
            # Cache the parsed content
            content_cache[url] = content
            return content
    except ReadTimeout as e:
        logger.error(f"Read timeout occurred while parsing URL {url}: {str(e)}", exc_info=True)
        return None
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


async def update_content_in_database(post_id: str, content: str) -> None:
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


async def process_url(url: str, post_id: str) -> None:
    """
    Process a URL: parse its content and update the database.

    Args:
        url (str): The URL to process.
        post_id (str): The ID of the associated post in the database.
    """
    if url in content_cache:
        content = content_cache[url]
        logger.info(f"Using cached content for URL: {url}")
    else:
        content = await parse_content(url)
    
    if content:
        await update_content_in_database(post_id, content)
        logger.info(f"Successfully processed URL: {url} and updated post ID: {post_id}")
    else:
        logger.warning(f"Failed to process URL: {url} for post ID: {post_id}")
