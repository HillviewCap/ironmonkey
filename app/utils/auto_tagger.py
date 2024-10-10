import spacy
from app.models.relational.allgroups import AllGroupsValues
from app.models.relational.alltools import AllToolsValuesNames
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.content_tag import ContentTag
from app.extensions import db

nlp = spacy.load("en_core_web_sm")

def get_entities():
    actors = {actor.actor.lower(): (str(actor.uuid), 'actor') for actor in AllGroupsValues.query.all()}
    tools = {tool.name.lower(): (str(tool.uuid), 'tool') for tool in AllToolsValuesNames.query.all()}
    return {**actors, **tools}

def tag_content(content_id):
    content = ParsedContent.query.get(content_id)
    if not content:
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
                parsed_content_id=content.id,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=ent.text,
                start_char=ent.start_char,
                end_char=ent.end_char
            )
            new_tags.append(new_tag)

    db.session.add_all(new_tags)
    db.session.commit()

def tag_all_content():
    for content in ParsedContent.query.all():
        tag_content(content.id)
