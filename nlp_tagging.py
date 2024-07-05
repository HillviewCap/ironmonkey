import httpx
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


class DiffbotClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = f"https://nl.diffbot.com/v1/?fields=entities,categories&token={self.api_key}"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }

    async def tag_content(self, content: str, client: httpx.AsyncClient) -> Dict[str, Any]:
        payload = [
            {
                "lang": "auto",
                "format": "plain text",
                "customSummary": {"maxNumberOfSentences": 3},
                "content": content,
                "documentType": "news article",
            }
        ]

        response = await client.post(self.url, json=payload, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"Error processing content: {response.status_code}")

        return response.json()[0]


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
        for uri_data in uris_data:
            uri = Uris(uri=uri_data["uri"], type=uri_data["type"], entity=entity)
            session.add(uri)

    def add_types(self, session, entity: Entity, types_data: List[Dict[str, str]]):
        for type_data in types_data:
            type_obj = Type(
                name=type_data["name"],
                diffbot_uri=type_data.get("diffbotUri"),
                dbpedia_uri=type_data.get("dbpediaUri"),
            )
            session.add(type_obj)
            entity_type = EntityType(entity=entity, type=type_obj)
            session.add(entity_type)

    def add_mentions(
        self, session, entity: Entity, mentions_data: List[Dict[str, Any]]
    ):
        for mention_data in mentions_data:
            mention = Mention(
                text=mention_data["text"],
                begin_offset=mention_data["beginOffset"],
                end_offset=mention_data["endOffset"],
                confidence=mention_data.get("confidence"),
                entity=entity,
            )
            session.add(mention)

    def add_locations(
        self, session, entity: Entity, locations_data: List[Dict[str, Any]]
    ):
        for location_data in locations_data:
            location = Location(
                latitude=location_data["latitude"],
                longitude=location_data["longitude"],
                precision=location_data.get("precision"),
                entity=entity,
            )
            session.add(location)

    def add_categories(
        self, session, categories_data: List[Dict[str, Any]], content: ParsedContent
    ):
        for category_data in categories_data:
            category = Category(
                type=category_data["type"],
                id_category=category_data["id"],
                name=category_data["name"],
                path=category_data.get("path"),
                parsed_content=content,
            )
            session.add(category)

    def process_nlp_result(self, content: ParsedContent, result: Dict[str, Any]):
        with self.Session() as session:
            for entity_data in result.get("entities", []):
                entity = self.add_entity(session, entity_data, content)
                self.add_uris(session, entity, entity_data.get("uris", []))
                self.add_types(session, entity, entity_data.get("types", []))
                self.add_mentions(session, entity, entity_data.get("mentions", []))
                self.add_locations(session, entity, entity_data.get("locations", []))

            self.add_categories(session, result.get("categories", []), content)
            session.commit()


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
