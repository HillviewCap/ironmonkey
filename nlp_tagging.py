import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ParsedContent, Entity, Uris, Type, EntityType, Mention, Location, Category
from config import Config

def tag_content():
    # Create database session
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Fetch all parsed content
    parsed_contents = session.query(ParsedContent).all()

    url = "https://nl.diffbot.com/v1/?fields=entities,categories&token=5dc42cec418d6760f7b5b1743f61fa73"

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    for content in parsed_contents:
        payload = [
            {
                "lang": "auto",
                "format": "plain text",
                "customSummary": {"maxNumberOfSentences": 3},
                "content": content.content,
                "documentType": "news article"
            }
        ]

        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            # Process entities
            for entity_data in result[0].get('entities', []):
                entity = Entity(
                    name=entity_data['name'],
                    diffbot_uri=entity_data.get('diffbotUri'),
                    confidence=entity_data.get('confidence'),
                    salience=entity_data.get('salience'),
                    is_custom=entity_data.get('isCustom', False),
                    parsed_content=content
                )
                session.add(entity)

                # Add URIs
                for uri_data in entity_data.get('uris', []):
                    uri = Uris(uri=uri_data['uri'], type=uri_data['type'], entity=entity)
                    session.add(uri)

                # Add types
                for type_data in entity_data.get('types', []):
                    type_obj = Type(
                        name=type_data['name'],
                        diffbot_uri=type_data.get('diffbotUri'),
                        dbpedia_uri=type_data.get('dbpediaUri')
                    )
                    session.add(type_obj)
                    entity_type = EntityType(entity=entity, type=type_obj)
                    session.add(entity_type)

                # Add mentions
                for mention_data in entity_data.get('mentions', []):
                    mention = Mention(
                        text=mention_data['text'],
                        begin_offset=mention_data['beginOffset'],
                        end_offset=mention_data['endOffset'],
                        confidence=mention_data.get('confidence'),
                        entity=entity
                    )
                    session.add(mention)

                # Add locations
                for location_data in entity_data.get('locations', []):
                    location = Location(
                        latitude=location_data['latitude'],
                        longitude=location_data['longitude'],
                        precision=location_data.get('precision'),
                        entity=entity
                    )
                    session.add(location)

            # Process categories
            for category_data in result[0].get('categories', []):
                category = Category(
                    type=category_data['type'],
                    id_category=category_data['id'],
                    name=category_data['name'],
                    path=category_data.get('path'),
                    parsed_content=content
                )
                session.add(category)

            # Commit the changes
            session.commit()
        else:
            print(f"Error processing content ID {content.id}: {response.status_code}")

    session.close()

if __name__ == "__main__":
    tag_content()
