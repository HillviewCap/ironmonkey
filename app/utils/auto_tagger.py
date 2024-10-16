import spacy
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.content_tag import ContentTag
import uuid
from sqlalchemy import exists
from app.models.relational.allgroups import AllGroupsValues
from app.models.relational.alltools import AllToolsValuesNames
from app.extensions import db
from flask import current_app

nlp = spacy.load("en_core_web_sm")

def get_entities():
    actors = {actor.actor.lower(): (str(actor.uuid), 'actor') for actor in AllGroupsValues.query.all()}
    tools = {tool.name.lower(): (str(tool.uuid), 'tool') for tool in AllToolsValuesNames.query.all()}
    return {**actors, **tools}

def tag_content(content):

    if isinstance(content, str):
        # Process the content string
        # Example tagging logic
        doc = nlp(content)
        tagged_content = []
        for ent in doc.ents:
            tagged_content.append({
                'text': ent.text,
                'label': ent.label_
            })
        return tagged_content
    elif isinstance(content, (int, uuid.UUID)):
        # Retrieve the ParsedContent object and process its content
        parsed_content = ParsedContent.get_by_id(content)
        if parsed_content:
            entities = get_entities()
            text_to_tag = f"{parsed_content.description or ''} {parsed_content.summary or ''}"
            doc = nlp(text_to_tag)

            new_tags = []    
            for ent in doc.ents:        
                lower_ent = ent.text.lower()
                if lower_ent in entities:
                    entity_id, entity_type = entities[lower_ent]
                    # Check for existing tag
                    existing_tag = ContentTag.query.filter_by(
                        parsed_content_id=parsed_content.id,
                        entity_type=entity_type,
                        entity_id=uuid.UUID(entity_id),
                        start_char=ent.start_char,                
                        end_char=ent.end_char
                    ).first()
                    
                    if existing_tag:
                        continue  # Skip adding duplicate tag
                    
                    # No duplicate exists, create new tag
                    new_tag = ContentTag(            
                        id=uuid.uuid4(),
                        parsed_content_id=parsed_content.id,
                        entity_type=entity_type,
                        entity_id=uuid.UUID(entity_id),
                        entity_name=ent.text,
                        start_char=ent.start_char,
                        end_char=ent.end_char
                    )
                    new_tags.append(new_tag)

            try:
                db.session.add_all(new_tags)
                db.session.commit()
                return len(new_tags)
            except Exception as e:
                current_app.logger.error(f"Error tagging content {content}: {str(e)}")
                db.session.rollback()
                return 0
    else:
        current_app.logger.error(f"Invalid content type in tag_content: {type(content)}")
        return content

def tag_all_content():
    from app.models.relational.parsed_content import ParsedContent

    total_tagged = 0
    for content in ParsedContent.query.all():
        total_tagged += tag_content(content.id)
    current_app.logger.info(f"Completed tagging {total_tagged} content items")

def get_tagged_content(content_id):
    from app.models.relational.parsed_content import ParsedContent
    content = ParsedContent.query.get(content_id)
    if not content:
        current_app.logger.warning(f"Content with id {content_id} not found")
        return None

    from app.models.relational.content_tag import ContentTag
    tags = ContentTag.query.filter_by(parsed_content_id=content_id).all()
    sorted_tags = sorted(tags, key=lambda t: t.start_char)

    description = content.description or ''
    summary = content.summary or ''

    tagged_description = _insert_tags(description, sorted_tags)
    tagged_summary = _insert_tags(summary, sorted_tags)

    return {
        'id': str(content.id),
        'title': content.title,
        'description': tagged_description,
        'summary': tagged_summary,
        'link': content.link,
        'published': content.published.isoformat() if content.published else None,
        'feed_id': str(content.feed_id),
        'tags': [tag.to_dict() for tag in tags]
    }

def _insert_tags(text, tags):
    offset = 0
    for tag in tags:
        if tag.start_char < len(text):
            start = tag.start_char + offset
            end = tag.end_char + offset
            link = f'<span class="tagged-entity" data-entity-type="{tag.entity_type}" data-entity-id="{tag.entity_id}" data-entity-name="{tag.entity_name}">{text[start:end]}</span>'
            text = text[:start] + link + text[end:]
            offset += len(link) - (end - start)
    return text

def tag_untagged_content(batch_size=1000):
    from app.models.relational.parsed_content import ParsedContent
    from app.models.relational.content_tag import ContentTag

    with current_app.app_context():
        total_checked = 0
        total_tagged = 0
        
        while True:
            untagged_content = ParsedContent.query.filter(
                ~exists().where(ContentTag.parsed_content_id == ParsedContent.id)
            ).limit(batch_size).all()

            if not untagged_content:
                break  # No more untagged content

            batch_checked = len(untagged_content)
            batch_tagged = 0

            for content in untagged_content:
                tags_added = tag_content(content.id)
                if tags_added > 0:
                    batch_tagged += 1

            total_checked += batch_checked
            total_tagged += batch_tagged

            if batch_checked < batch_size:
                break  # Processed all available untagged content

        current_app.logger.info(f"Auto-tagging complete: Checked {total_checked} items, tagged {total_tagged} previously untagged content items")
