import httpx
import os
import logging
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    db,
    ParsedContent,
    Entity,
    Uris,
    Type,
    EntityType,
    Mention,
    Location,
    Category,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from config import Config
from typing import List, Dict, Any
import asyncio
import time
from ratelimit import limits, sleep_and_retry

# Set up logging for nlp_tagging
logger = logging.getLogger("nlp_tagging")
logger.setLevel(logging.INFO)

# Ensure logs directory exists
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Create a file handler
file_handler = logging.FileHandler(os.path.join(logs_dir, "nlp_tagging.log"))
file_handler.setLevel(logging.INFO)

# Create a formatting for the logs
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)


class DiffbotClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = f"https://nl.diffbot.com/v1/?fields=entities,sentiment,categories,summary&token={self.api_key}"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }

    @sleep_and_retry
    @limits(calls=5, period=60)
    async def tag_content(
        self, content: str, client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        payload = {
            "lang": "auto",
            "format": "plain text",
            "content": content,
            "documentType": "news article",
        }

        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = await client.post(
                    self.url, json=payload, headers=self.headers
                )

                if response.status_code != 200:
                    error_message = f"Error processing content: {response.status_code}"
                    logger.error(error_message)
                    raise Exception(error_message)

                response_json = response.json()

                # Log the full JSON response
                logger.info(f"Diffbot response: {json.dumps(response_json, indent=2)}")

                logger.info("Diffbot response received and logged")

                # Check if the response is a dictionary and has the expected keys
                if isinstance(response_json, dict) and "entities" in response_json:
                    return response_json
                else:
                    error_message = "Unexpected response format from Diffbot API"
                    logger.error(error_message)
                    raise Exception(error_message)

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"All {max_retries} attempts failed. Last error: {str(e)}"
                    )
                    raise


class DatabaseHandler:
    def __init__(self, db_uri: str):
        engine = create_engine(db_uri)
        self.Session = sessionmaker(bind=engine)

    def get_all_parsed_content(self) -> List[ParsedContent]:
        with self.Session() as session:
            return session.query(ParsedContent).filter(ParsedContent.id != None).all()

    def add_entity(
        self, session, entity_data: Dict[str, Any], content: ParsedContent
    ) -> Entity:
        entity = Entity(
            name=entity_data["name"],
            diffbot_uri=entity_data.get("diffbotUri"),
            confidence=entity_data.get("confidence"),
            salience=entity_data.get("salience"),
            is_custom=entity_data.get("isCustom", False),
            parsed_content=content,
        )
        session.add(entity)
        return entity

    def add_uris(self, session, entity: Entity, uris_data: List[Dict[str, str]]):
        if isinstance(uris_data, list):
            for uri_data in uris_data:
                if isinstance(uri_data, dict):
                    uri = Uris(
                        uri=uri_data.get("uri"),
                        type=uri_data.get("type"),
                        entity=entity,
                    )
                    session.add(uri)
                else:
                    logger.warning(f"Unexpected URI data type: {type(uri_data)}")
        else:
            logger.warning(f"Unexpected URIs data type: {type(uris_data)}")

    def add_types(self, session, entity: Entity, types_data: List[Dict[str, str]]):
        if isinstance(types_data, list):
            for type_data in types_data:
                if isinstance(type_data, dict):
                    type_obj = Type(
                        name=type_data.get("name"),
                        diffbot_uri=type_data.get("diffbotUri"),
                        dbpedia_uri=type_data.get("dbpediaUri"),
                    )
                    session.add(type_obj)
                    entity_type = EntityType(entity=entity, type=type_obj)
                    session.add(entity_type)
                else:
                    logger.warning(f"Unexpected type data type: {type(type_data)}")
        else:
            logger.warning(f"Unexpected types data type: {type(types_data)}")

    def add_mentions(
        self, session, entity: Entity, mentions_data: List[Dict[str, Any]]
    ):
        if isinstance(mentions_data, list):
            for mention_data in mentions_data:
                if isinstance(mention_data, dict):
                    mention = Mention(
                        text=mention_data.get("text"),
                        begin_offset=mention_data.get("beginOffset"),
                        end_offset=mention_data.get("endOffset"),
                        confidence=mention_data.get("confidence"),
                        entity=entity,
                    )
                    session.add(mention)
                else:
                    logger.warning(
                        f"Unexpected mention data type: {type(mention_data)}"
                    )
        else:
            logger.warning(f"Unexpected mentions data type: {type(mentions_data)}")

    def add_locations(
        self, session, entity: Entity, locations_data: List[Dict[str, Any]]
    ):
        if isinstance(locations_data, list):
            for location_data in locations_data:
                if isinstance(location_data, dict):
                    location = Location(
                        latitude=location_data.get("latitude"),
                        longitude=location_data.get("longitude"),
                        precision=location_data.get("precision"),
                        entity=entity,
                    )
                    session.add(location)
                else:
                    logger.warning(
                        f"Unexpected location data type: {type(location_data)}"
                    )
        else:
            logger.warning(f"Unexpected locations data type: {type(locations_data)}")

    def add_categories(
        self, session, categories_data: List[Dict[str, Any]], content: ParsedContent
    ):
        if isinstance(categories_data, list):
            for category_data in categories_data:
                if isinstance(category_data, dict):
                    category = Category(
                        type=category_data.get("type"),
                        id_category=category_data.get("id"),
                        name=category_data.get("name"),
                        path=category_data.get("path"),
                        parsed_content=content,
                    )
                    session.add(category)
                else:
                    logger.warning(
                        f"Unexpected category data type: {type(category_data)}"
                    )
        else:
            logger.warning(f"Unexpected categories data type: {type(categories_data)}")

    def process_nlp_result(
        self, content: ParsedContent, result: Dict[str, Any], session
    ):
        entities = result.get("entities", [])
        if isinstance(entities, list):
            for entity_data in entities:
                if isinstance(entity_data, dict):
                    entity = self.add_entity(session, entity_data, content)
                    self.add_uris(session, entity, entity_data.get("uris", []))
                    self.add_types(session, entity, entity_data.get("types", []))
                    self.add_mentions(session, entity, entity_data.get("mentions", []))
                    self.add_locations(
                        session, entity, entity_data.get("locations", [])
                    )
                else:
                    logging.warning(f"Unexpected entity data type: {type(entity_data)}")

        categories = result.get("categories", [])
        if isinstance(categories, list):
            self.add_categories(session, categories, content)
        else:
            logging.warning(f"Unexpected categories data type: {type(categories)}")


async def process_single_content(
    diffbot_client: DiffbotClient, db_handler: DatabaseHandler, content: ParsedContent
):
    try:
        result = await diffbot_client.tag_content(content.content)
        db_handler.process_nlp_result(content, result)
    except Exception as e:
        print(f"Error processing content ID {content.id}: {str(e)}")


async def main():
    diffbot_api_key = os.getenv("DIFFBOT_API_KEY")
    if not diffbot_api_key:
        raise ValueError("DIFFBOT_API_KEY environment variable is not set")

    diffbot_client = DiffbotClient(diffbot_api_key)
    db_handler = DatabaseHandler(Config.SQLALCHEMY_DATABASE_URI)

    parsed_contents = db_handler.get_all_parsed_content()

    tasks = [
        process_single_content(diffbot_client, db_handler, content)
        for content in parsed_contents
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
