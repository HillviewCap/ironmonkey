from __future__ import annotations

import json
import logging
from typing import Dict, List, Any, Optional
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.alltools import AllTools, AllToolsValues, AllToolsValuesNames
from models.allgroups import AllGroups, AllGroupsValues, AllGroupsValuesNames
from config import Config

logger = logging.getLogger(__name__)

import os

def load_json_file(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load JSON data from a local file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        Optional[List[Dict[str, Any]]]: The JSON data as a list of dictionaries, or None if an error occurs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading local file {file_path}: {e}")
    
    return None


def update_alltools(session: Session, data: List[Dict[str, Any]]) -> None:
    """
    Update the AllTools database with the given data.

    Args:
        session (Session): The SQLAlchemy session.
        data (List[Dict[str, Any]]): The data to update the database with.
    """
    for tool in data:
        db_tool = session.query(AllTools).filter_by(uuid=tool['uuid']).first()
        if not db_tool:
            db_tool = AllTools(uuid=tool['uuid'])
            session.add(db_tool)
        
        db_tool.authors = tool.get('authors')
        db_tool.category = tool.get('category')
        db_tool.name = tool.get('name')
        db_tool.type = tool.get('type')
        db_tool.source = tool.get('source')
        db_tool.description = tool.get('description')
        db_tool.tlp = tool.get('tlp')
        db_tool.license = tool.get('license')
        db_tool.last_db_change = tool.get('last_db_change')

        for value in tool.get('values', []):
            db_value = session.query(AllToolsValues).filter_by(uuid=value['uuid']).first()
            if not db_value:
                db_value = AllToolsValues(uuid=value['uuid'])
                db_tool.values.append(db_value)
            
            db_value.tool = value.get('tool')
            db_value.description = value.get('description')
            db_value.category = value.get('category')
            db_value.type = value.get('type')
            db_value.information = value.get('information')
            db_value.last_card_change = value.get('last_card_change')

            for name in value.get('names', []):
                db_name = session.query(AllToolsValuesNames).filter_by(name=name).first()
                if not db_name:
                    db_name = AllToolsValuesNames(name=name)
                    db_value.names.append(db_name)

def update_allgroups(session: Session, data: List[Dict[str, Any]]) -> None:
    """
    Update the AllGroups database with the given data.

    Args:
        session (Session): The SQLAlchemy session.
        data (List[Dict[str, Any]]): The data to update the database with.
    """
    for group in data:
        db_group = session.query(AllGroups).filter_by(uuid=group['uuid']).first()
        if not db_group:
            db_group = AllGroups(uuid=group['uuid'])
            session.add(db_group)
        
        db_group.authors = group.get('authors')
        db_group.category = group.get('category')
        db_group.name = group.get('name')
        db_group.type = group.get('type')
        db_group.source = group.get('source')
        db_group.description = group.get('description')
        db_group.tlp = group.get('tlp')
        db_group.license = group.get('license')
        db_group.last_db_change = group.get('last_db_change')

        for value in group.get('values', []):
            db_value = session.query(AllGroupsValues).filter_by(uuid=value['uuid']).first()
            if not db_value:
                db_value = AllGroupsValues(uuid=value['uuid'])
                db_group.values.append(db_value)
            
            db_value.actor = value.get('actor')
            db_value.country = value.get('country')
            db_value.description = value.get('description')
            db_value.information = value.get('information')
            db_value.last_card_change = value.get('last_card_change')

            for name in value.get('names', []):
                db_name = session.query(AllGroupsValuesNames).filter_by(name=name['name']).first()
                if not db_name:
                    db_name = AllGroupsValuesNames(name=name['name'], name_giver=name.get('name_giver'))
                    db_value.names.append(db_name)

def update_databases() -> None:
    """
    Update the AllTools and AllGroups databases with the latest data from the local JSON files.
    """
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Update AllTools
        tools_data = load_json_file("tgcapt/Threat Group Card - All tools.json")
        if tools_data is not None:
            if isinstance(tools_data, list):
                update_alltools(session, tools_data)
                logger.info("AllTools database updated successfully.")
            else:
                logger.error(f"Unexpected data type for tools_data: {type(tools_data)}. Expected a list.")
                logger.debug(f"tools_data content: {str(tools_data)[:500]}...")  # Log first 500 characters
        else:
            logger.warning("Failed to load AllTools data. Skipping update.")

        # Update AllGroups
        groups_data = load_json_file("tgcapt/Threat Group Card - All groups.json")
        if groups_data is not None:
            if isinstance(groups_data, list):
                update_allgroups(session, groups_data)
                logger.info("AllGroups database updated successfully.")
            elif isinstance(groups_data, dict) and 'values' in groups_data:
                update_allgroups(session, [groups_data])
                logger.info("AllGroups database updated successfully (single group data).")
            else:
                logger.error(f"Unexpected data type for groups_data: {type(groups_data)}. Expected a list or a dict with 'values'.")
                logger.debug(f"groups_data content: {str(groups_data)[:500]}...")  # Log first 500 characters
        else:
            logger.warning("Failed to load AllGroups data. Skipping update.")

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"An error occurred: {str(e)}")
        logger.exception("Exception details:")
    finally:
        session.close()

if __name__ == "__main__":
    update_databases()
