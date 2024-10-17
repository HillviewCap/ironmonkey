from pymongo import MongoClient
import spacy
from spacy.matcher import PhraseMatcher
import logging

# MongoDB setup
client = MongoClient('your_mongodb_uri')  # Replace with your MongoDB URI
db = client['your_database_name']         # Replace with your database name
parsed_content_collection = db['parsed_content']
allgroups_collection = db['allgroups']
alltools_collection = db['alltools']

# Spacy setup
nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

# Load group and tool names
group_names = [item['name'] for item in allgroups_collection.find({}, {'name': 1})]
tool_names = [item['name'] for item in alltools_collection.find({}, {'name': 1})]

# Add patterns to matcher
group_patterns = [nlp.make_doc(name) for name in group_names]
tool_patterns = [nlp.make_doc(name) for name in tool_names]
matcher.add("GROUP_NAME", group_patterns)
matcher.add("TOOL_NAME", tool_patterns)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def process_and_update_documents():
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

try:
    process_and_update_documents()
except Exception as e:
    logger.error(f"An error occurred: {e}")
