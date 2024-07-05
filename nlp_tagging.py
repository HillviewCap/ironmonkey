import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ParsedContent
import json
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
            
            # Extract entities and categories
            entities = result[0].get('entities', [])
            categories = result[0].get('categories', [])
            
            # Update the ParsedContent object
            content.entities = json.dumps(entities)
            content.categories = json.dumps(categories)
            
            # Commit the changes
            session.commit()
        else:
            print(f"Error processing content ID {content.id}: {response.status_code}")

    session.close()

if __name__ == "__main__":
    tag_content()
