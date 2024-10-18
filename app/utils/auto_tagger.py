import os
from pymongo import MongoClient
import spacy
from spacy.matcher import PhraseMatcher
import logging
from flask import current_app
from app.utils.mongodb_connection import get_mongo_client

# Spacy setup
nlp = spacy.load("en_core_web_lg")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def tag_additional_entities(doc):
    additional_tags = []
    
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "PRODUCT", "GPE"]:
            label = {
                "PERSON": "NAME",
                "ORG": "COMPANY",
                "PRODUCT": "PRODUCT",
                "GPE": "COUNTRY"
            }.get(ent.label_, ent.label_)
            
            additional_tags.append({
                'text': ent.text,
                'label': label,
                'start_char': ent.start_char,
                'end_char': ent.end_char
            })
    
    return additional_tags

def tag_text_field(text):
    doc = nlp(text)
    tags = []
    
    # Matcher for GROUP_NAME and TOOL_NAME
    matches = matcher(doc)
    group_matches = []
    tool_matches = []
    
    for match_id, start, end in matches:
        span = doc[start:end]
        label = nlp.vocab.strings[match_id]
        if label == "GROUP_NAME":
            group_matches.append((start, end, label))
        elif label == "TOOL_NAME":
            tool_matches.append((start, end, label))
    
    # Prioritize GROUP_NAME matches
    for start, end, label in group_matches + tool_matches:
        span = doc[start:end]
        tags.append({
            'text': span.text,
            'label': label,
            'start_char': span.start_char,
            'end_char': span.end_char
        })
    
    # Add additional entity tags
    tags.extend(tag_additional_entities(doc))
    
    logger.debug(f"Tagged text: '{text[:50]}...', Found tags: {tags}")
    return tags

# Remove the tag_content function as it's redundant with tag_text_field

def process_and_update_documents():
    try:
        mongo_client = get_mongo_client()
        db = mongo_client[current_app.config['MONGO_DB_NAME']]
        parsed_content_collection = db['parsed_content']
        allgroups_collection = db['allgroups']
        alltools_collection = db['alltools']

        # Load group and tool names
        group_names = [item['name'] for item in allgroups_collection.find({}, {'name': 1})]
        logger.info(f"Loaded {len(group_names)} group names")
        logger.debug(f"Group names: {group_names[:10]}...")  # Log first 10 group names
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
                    updates[f"{field}_tags"] = tags  # Always update, even if empty
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

def tag_all_content(force_all=False):
    """
    Tags all content in the parsed_content collection.
    If force_all is True, it re-tags all documents, otherwise it only tags untagged documents.
    """
    try:
        mongo_client = get_mongo_client()
        db = mongo_client[current_app.config['MONGO_DB_NAME']]
        parsed_content_collection = db['parsed_content']

        # Load group and tool names
        allgroups_collection = db['allgroups']
        alltools_collection = db['alltools']
        group_names = [item['name'] for item in allgroups_collection.find({}, {'name': 1})]
        tool_names = [item['name'] for item in alltools_collection.find({}, {'name': 1})]
        
        logger.info(f"Loaded {len(group_names)} group names and {len(tool_names)} tool names")
        logger.debug(f"Sample group names: {group_names[:5]}")
        logger.debug(f"Sample tool names: {tool_names[:5]}")

        # Add patterns to matcher
        group_patterns = [nlp.make_doc(name) for name in group_names]
        tool_patterns = [nlp.make_doc(name) for name in tool_names]
        matcher.add("GROUP_NAME", group_patterns)
        matcher.add("TOOL_NAME", tool_patterns)

        fields_to_tag = ['content', 'description', 'summary', 'title']

        # Determine which documents to process
        if force_all:
            documents_to_process = parsed_content_collection.find()
            logger.info("Processing all documents for tagging")
        else:
            # Find documents without tags
            documents_to_process = parsed_content_collection.find({
                "$or": [{f"{field}_tags": {"$exists": False}} for field in fields_to_tag]
            })
            logger.info("Processing only untagged documents")

        processed_count = 0
        tagged_count = 0
        for document in documents_to_process:
            updates = {}
            for field in fields_to_tag:
                text = document.get(field)
                if text:
                    tags = tag_text_field(text)
                    updates[f"{field}_tags"] = tags
                    if any(tag['label'] == 'GROUP_NAME' for tag in tags):
                        tagged_count += 1
            if updates:
                parsed_content_collection.update_one(
                    {'_id': document['_id']},
                    {'$set': updates}
                )
            processed_count += 1
            if processed_count % 100 == 0:
                logger.info(f"Processed {processed_count} documents, tagged {tagged_count} with GROUP_NAME")
        
        logger.info(f"Completed tagging. Processed {processed_count} documents, tagged {tagged_count} with GROUP_NAME")
    except Exception as e:
        logger.error(f"An error occurred while tagging content: {e}")
    finally:
        mongo_client.close()

def tag_untagged_content():
    """
    Tags untagged content in the parsed_content collection.
    """
    try:
        mongo_client = get_mongo_client()
        db = mongo_client[current_app.config['MONGO_DB_NAME']]
        parsed_content_collection = db['parsed_content']

        # Load group and tool names
        allgroups_collection = db['allgroups']
        alltools_collection = db['alltools']
        group_names = [item['name'] for item in allgroups_collection.find({}, {'name': 1})]
        tool_names = [item['name'] for item in alltools_collection.find({}, {'name': 1})]

        # Add patterns to matcher
        group_patterns = [nlp.make_doc(name) for name in group_names]
        tool_patterns = [nlp.make_doc(name) for name in tool_names]
        matcher.add("GROUP_NAME", group_patterns)
        matcher.add("TOOL_NAME", tool_patterns)

        fields_to_tag = ['content', 'description', 'summary', 'title']

        # Find documents without tags
        untagged_docs = parsed_content_collection.find({
            "$or": [{f"{field}_tags": {"$exists": False}} for field in fields_to_tag]
        })

        for document in untagged_docs:
            updates = {}
            for field in fields_to_tag:
                if f"{field}_tags" not in document:
                    text = document.get(field)
                    tags = tag_text_field(text) if text else []
                    updates[f"{field}_tags"] = tags
            if updates:
                parsed_content_collection.update_one(
                    {'_id': document['_id']},
                    {'$set': updates}
                )
        
        logger.info("Completed tagging untagged documents in parsed_content collection")
    except Exception as e:
        logger.error(f"An error occurred while tagging untagged content: {e}")
    finally:
        mongo_client.close()

if __name__ == "__main__":
    # This block will only run if the script is executed directly
    from flask import Flask
    from config import get_config

    app = Flask(__name__)
    app.config.from_object(get_config())

    with app.app_context():
        tag_all_content()
