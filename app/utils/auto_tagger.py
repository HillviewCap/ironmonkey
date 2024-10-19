import os
from pymongo import MongoClient
import spacy
from spacy.matcher import PhraseMatcher
import logging
from flask import current_app
from app.utils.mongodb_connection import get_mongo_client
from app.utils.logging_config import setup_logger

# Spacy setup
nlp = spacy.load("en_core_web_lg")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

# Set up a dedicated logger for auto_tagger
logger = setup_logger('auto_tagger', 'auto_tagger.log', level=logging.DEBUG)

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
    try:
        doc = nlp(text)
        tags = []
        
        # Matcher for GROUP_NAME and TOOL_NAME
        matches = matcher(doc)
        custom_matches = []
        
        for match_id, start, end in matches:
            span = doc[start:end]
            label = nlp.vocab.strings[match_id]
            custom_matches.append((start, end, label))
        
        # Sort custom matches by start position
        custom_matches.sort(key=lambda x: x[0])
        
        # Add custom matches (GROUP_NAME and TOOL_NAME)
        for start, end, label in custom_matches:
            span = doc[start:end]
            tags.append({
                'text': span.text,
                'label': label,
                'start_char': span.start_char,
                'end_char': span.end_char
            })
        
        # Add additional entity tags, but don't overwrite custom matches
        existing_spans = set((tag['start_char'], tag['end_char']) for tag in tags)
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "PRODUCT", "GPE"] and (ent.start_char, ent.end_char) not in existing_spans:
                label = {
                    "PERSON": "NAME",
                    "ORG": "COMPANY",
                    "PRODUCT": "PRODUCT",
                    "GPE": "COUNTRY"
                }.get(ent.label_, ent.label_)
                
                tags.append({
                    'text': ent.text,
                    'label': label,
                    'start_char': ent.start_char,
                    'end_char': ent.end_char
                })
        
        logger.debug(f"Tagged text: '{text[:50]}...', Found tags: {tags}")
        return tags
    except Exception as e:
        logger.error(f"Error in tag_text_field: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []  # Return an empty list if there's an error

# Remove the tag_content function as it's redundant with tag_text_field

def process_and_update_documents():
    try:
        logger.info("Starting process_and_update_documents")
        mongo_client = get_mongo_client()
        db = mongo_client[current_app.config['MONGO_DB_NAME']]
        parsed_content_collection = db['parsed_content']
        allgroups_collection = db['allgroups']
        alltools_collection = db['alltools']

        # Load group and tool names
        group_names = [item['name'] for item in allgroups_collection.find({}, {'name': 1})]
        logger.info(f"Loaded {len(group_names)} group names")
        logger.debug(f"Sample group names: {group_names[:10]}")
        tool_names = [item['name'] for item in alltools_collection.find({}, {'name': 1})]
        logger.info(f"Loaded {len(tool_names)} tool names")
        logger.debug(f"Sample tool names: {tool_names[:10]}")

        # Add patterns to matcher
        group_patterns = [nlp.make_doc(name) for name in group_names]
        tool_patterns = [nlp.make_doc(name) for name in tool_names]
        matcher.add("GROUP_NAME", group_patterns)
        matcher.add("TOOL_NAME", tool_patterns)

        fields_to_tag = ['content', 'description', 'summary', 'title']

        processed_count = 0
        tagged_count = 0
        for document in parsed_content_collection.find():
            updates = {}
            for field in fields_to_tag:
                text = document.get(field)
                if text:
                    tags = tag_text_field(text)
                    updates[f"{field}_tags"] = tags
                    if any(tag['label'] in ['GROUP_NAME', 'TOOL_NAME'] for tag in tags):
                        tagged_count += 1
            if updates:
                parsed_content_collection.update_one(
                    {'_id': document['_id']},
                    {'$set': updates}
                )
            processed_count += 1
            if processed_count % 100 == 0:
                logger.info(f"Processed {processed_count} documents, tagged {tagged_count} with GROUP_NAME or TOOL_NAME")
        
        logger.info(f"Completed process_and_update_documents. Processed {processed_count} documents, tagged {tagged_count} with GROUP_NAME or TOOL_NAME")
    except Exception as e:
        logger.exception(f"An error occurred in process_and_update_documents: {e}")
    finally:
        mongo_client.close()

import traceback

def tag_all_content(force_all=True):
    """
    Tags all content in the parsed_content collection.
    If force_all is True, it re-tags all documents, otherwise it only tags untagged documents.
    """
    mongo_client = None
    try:
        logger.info(f"Starting tag_all_content with force_all={force_all}")
        mongo_client = get_mongo_client()
        db = mongo_client[current_app.config['MONGO_DB_NAME']]
        parsed_content_collection = db['parsed_content']

        # Load group and tool names
        allgroups_collection = db['allgroups']
        alltools_collection = db['alltools']

        # Correctly extract group names from the 'values.names' array
        group_names = []
        for group in allgroups_collection.find({}, {'values.names': 1}):
            if 'values' in group and 'names' in group['values']:
                group_names.extend([name['name'] for name in group['values']['names'] if 'name' in name])

        # Extract tool names
        tool_names = [item['name'] for item in alltools_collection.find({}, {'name': 1}) if 'name' in item]
        
        logger.info(f"Loaded {len(group_names)} group names and {len(tool_names)} tool names")
        logger.debug(f"Sample group names: {group_names[:5]}")
        logger.debug(f"Sample tool names: {tool_names[:5]}")

        # Add patterns to matcher
        group_patterns = [nlp.make_doc(name) for name in group_names if name]
        tool_patterns = [nlp.make_doc(name) for name in tool_names if name]
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
            try:
                updates = {}
                for field in fields_to_tag:
                    text = document.get(field)
                    if text:
                        tags = tag_text_field(text)
                        updates[f"{field}_tags"] = tags
                        if any(tag['label'] in ['GROUP_NAME', 'TOOL_NAME'] for tag in tags):
                            tagged_count += 1
                if updates:
                    parsed_content_collection.update_one(
                        {'_id': document['_id']},
                        {'$set': updates}
                    )
                processed_count += 1
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} documents, tagged {tagged_count} with GROUP_NAME or TOOL_NAME")
            except Exception as doc_error:
                logger.error(f"Error processing document {document.get('_id', 'unknown')}: {str(doc_error)}")
                logger.error(f"Document error traceback: {traceback.format_exc()}")
                # Continue with the next document
        
        logger.info(f"Completed tag_all_content. Processed {processed_count} documents, tagged {tagged_count} with GROUP_NAME or TOOL_NAME")
    except Exception as e:
        logger.error(f"An error occurred in tag_all_content: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        if mongo_client:
            mongo_client.close()
        logger.info("tag_all_content function completed execution")

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
        logger.info("Starting auto_tagger main execution")
        tag_all_content()
        logger.info("Finished auto_tagger main execution")
