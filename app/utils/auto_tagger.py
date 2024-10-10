import spacy
import uuid
from app.models.relational.allgroups import AllGroupsValues
from app.models.relational.alltools import AllToolsValuesNames
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.content_tag import ContentTag
from app.extensions import db
from flask import current_app

nlp = spacy.load("en_core_web_sm")

def get_entities():
    actors = {actor.actor.lower(): (str(actor.uuid), 'actor') for actor in AllGroupsValues.query.all()}
    tools = {tool.name.lower(): (str(tool.uuid), 'tool') for tool in AllToolsValuesNames.query.all()}
    return {**actors, **tools}

def tag_content(content_id):
    content = ParsedContent.query.get(content_id)
    if not content:
        current_app.logger.warning(f"Content with id {content_id} not found")
        return

    entities = get_entities()
    text_to_tag = f"{content.description or ''} {content.summary or ''}"
    doc = nlp(text_to_tag)

    new_tags = []
    for ent in doc.ents:
        lower_ent = ent.text.lower()
        if lower_ent in entities:
            entity_id, entity_type = entities[lower_ent]
            new_tag = ContentTag(
                id=uuid.uuid4(),  # Generate a new UUID for each tag
                parsed_content_id=content.id,
                entity_type=entity_type,
                entity_id=uuid.UUID(entity_id),  # Convert string to UUID
                entity_name=ent.text,
                start_char=ent.start_char,
                end_char=ent.end_char
            )
            new_tags.append(new_tag)

    try:
        db.session.add_all(new_tags)
        db.session.commit()
        current_app.logger.info(f"Tagged content {content_id} with {len(new_tags)} tags")
    except Exception as e:
        current_app.logger.error(f"Error tagging content {content_id}: {str(e)}")
        db.session.rollback()

def tag_all_content():
    total_tagged = 0
    for content in ParsedContent.query.all():
        tag_content(content.id)
        total_tagged += 1
    current_app.logger.info(f"Completed tagging {total_tagged} content items")
