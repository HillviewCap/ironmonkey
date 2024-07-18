from __future__ import annotations

import json
import hashlib
from typing import Dict, List, Any
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.alltools import AllTools, AllToolsValues, AllToolsValuesNames
from models.allgroups import AllGroups, AllGroupsValues, AllGroupsValuesNames
from config import Config

def fetch_json(url: str) -> Dict[str, Any]:
    """
    Fetch JSON data from a given URL.

    Args:
        url (str): The URL to fetch JSON data from.

    Returns:
        Dict[str, Any]: The JSON data as a dictionary.

    Raises:
        httpx.HTTPStatusError: If the HTTP request fails.
    """
    with httpx.Client() as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()

def calculate_hash(data: Dict[str, Any]) -> str:
    """
    Calculate the MD5 hash of the given data.

    Args:
        data (Dict[str, Any]): The data to calculate the hash for.

    Returns:
        str: The MD5 hash of the data.
    """
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

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
    Update the AllTools and AllGroups databases with the latest data from the API.
    """
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Update AllTools
        tools_url = "https://apt.etda.or.th/cgi-bin/getcard.cgi?t=all&o=j"
        tools_data = fetch_json(tools_url)
        tools_hash = calculate_hash(tools_data)

        # Check if the data has changed
        if tools_hash != getattr(Config, 'LAST_TOOLS_HASH', None):
            update_alltools(session, tools_data)
            Config.LAST_TOOLS_HASH = tools_hash
            print("AllTools database updated successfully.")
        else:
            print("AllTools database is already up to date.")

        # Update AllGroups
        groups_url = "https://apt.etda.or.th/cgi-bin/getcard.cgi?g=all&o=j"
        groups_data = fetch_json(groups_url)
        groups_hash = calculate_hash(groups_data)

        # Check if the data has changed
        if groups_hash != getattr(Config, 'LAST_GROUPS_HASH', None):
            update_allgroups(session, groups_data)
            Config.LAST_GROUPS_HASH = groups_hash
            print("AllGroups database updated successfully.")
        else:
            print("AllGroups database is already up to date.")

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    update_databases()
