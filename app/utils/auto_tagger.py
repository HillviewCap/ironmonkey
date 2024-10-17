import os
from pymongo import MongoClient
import spacy
from spacy.matcher import PhraseMatcher
import logging
from flask import current_app

# Spacy setup
nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_mongo_client():
    mongodb_uri = current_app.config['MONGODB_URI']
    return MongoClient(mongodb_uri)

def tag_text_field(text):
    doc = nlp(text)
    tags = []
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        label = nlp.vocab.strings[match_id]
        tags.append({
            'text': span.text,
            'label': label,
            'start_char': span.start_char,
            'end_char': span.end_char
        })
    return tags

def tag_content(text):
    """
    Tags the given text using the current matcher.
    
    :param text: The text to be tagged
    :return: A list of tags found in the text
    """
    doc = nlp(text)
    tags = []
    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        label = nlp.vocab.strings[match_id]
        tags.append({
            'text': span.text,
            'label': label,
            'start_char': span.start_char,
            'end_char': span.end_char
        })
    return tags

def process_and_update_documents():
    try:
        mongo_client = get_mongo_client()
        db = mongo_client[current_app.config['MONGO_DB_NAME']]
        parsed_content_collection = db['parsed_content']
        allgroups_collection = db['allgroups']
        alltools_collection = db['alltools']

        # Load group and tool names
        group_names = [item['name'] for item in allgroups_collection.find({}, {'name': 1})]
        tool_names = [item['name'] for item in alltools_collection.find({}, {'name': 1})]

        # Add patterns to matcher
        group_patterns = [nlp.make_doc(name) for name in group_names]
        tool_patterns = [nlp.make_doc(name) for name in tool_names]
        matcher.add("GROUP_NAME", group_patterns)
        matcher.add("TOOL_NAME", tool_patterns)

        fields_to_tag = ['content', 'description', 'summary', 'title']

        for document in parsed_content_collection.find():
            updates = {}
            for field in fields_to_tag:
                text = document.get(field)
                if text:
                    tags = tag_text_field(text)
                    updates[f"{field}_tags"] = tags
            if updates:
                parsed_content_collection.update_one(
                    {'_id': document['_id']},
                    {'$set': updates}
                )
        logger.info("Completed tagging documents in parsed_content collection")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        mongo_client.close()

def tag_all_content():
    """
    Wrapper function for process_and_update_documents to maintain backwards compatibility.
    """
    process_and_update_documents()

if __name__ == "__main__":
    # This block will only run if the script is executed directly
    from flask import Flask
    from config import get_config

    app = Flask(__name__)
    app.config.from_object(get_config())

    with app.app_context():
        tag_all_content()
