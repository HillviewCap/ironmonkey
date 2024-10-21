from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Any, Optional, Union
import httpx
from sqlalchemy import create_engine, inspect
from uuid import UUID
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from app.models.relational.alltools import AllTools, AllToolsValues, AllToolsValuesNames
import re
from app.models.relational.allgroups import (
    AllGroups,
    AllGroupsValues,
    AllGroupsValuesNames,
)
import uuid
from flask import current_app
from app import db

logger = logging.getLogger(__name__)

def ensure_db_directory_exists():
    """Ensure the directory for the database file exists."""
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not db_uri:
        logger.error("SQLALCHEMY_DATABASE_URI is not set in the configuration.")
        raise ValueError("SQLALCHEMY_DATABASE_URI must be set in the configuration.")

    db_path = db_uri.replace('sqlite:///', '')
    db_dir = os.path.dirname(db_path)
    if not db_dir:
        logger.error("Database directory path is empty. Check SQLALCHEMY_DATABASE_URI configuration.")
        raise ValueError("Database directory path is empty. Check SQLALCHEMY_DATABASE_URI configuration.")
        os.makedirs(db_dir)
        logger.info(f"Created directory for database: {db_dir}")

def create_db_tables():
    """Create database tables if they don't exist."""
    try:
        engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
        db.session = scoped_session(sessionmaker(bind=engine))
        
        inspector = inspect(engine)
        tables_to_create = [
            AllTools.__table__,
            AllToolsValues.__table__,
            AllToolsValuesNames.__table__,
            AllGroups.__table__,
            AllGroupsValues.__table__,
            AllGroupsValuesNames.__table__
        ]
        
        for table in tables_to_create:
            if not inspector.has_table(table.name):
                logger.info(f"Creating table: {table.name}")
                table.create(engine)
        
        logger.info("All necessary tables have been created.")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load JSON data from a local file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        List[Dict[str, Any]]: The JSON data as a list of dictionaries.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            else:
                logger.error(f"Unexpected data type in {file_path}: {type(data)}")
                return []
    except Exception as e:
        logger.error(f"Error reading local file {file_path}: {e}")
        return []


def update_alltools(session: Session, data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> None:
    """
    Update the AllTools database with the given data.

    Args:
        session (Session): The SQLAlchemy session.
        data (Union[List[Dict[str, Any]], Dict[str, Any]]): The data to update the database with.
    """
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        logger.error(f"Invalid data type for update_alltools: {type(data)}")
        return

    for tool in data:
        if not isinstance(tool, dict):
            logger.error(f"Invalid tool data type: {type(tool)}. Skipping.")
            continue

        try:
            with session.no_autoflush:
                tool_uuid = UUID(str(tool.get("uuid", "")))
                db_tool = (
                    session.query(AllTools).filter(AllTools.uuid == tool_uuid).first()
                )
                if not db_tool:
                    db_tool = AllTools(uuid=tool_uuid)
                    session.add(db_tool)

                authors = tool.get("authors", [])
                db_tool.authors = ", ".join(authors) if isinstance(authors, list) else str(authors)

            db_tool.category = tool.get("category")
            db_tool.name = tool.get("name")
            db_tool.type = tool.get("type")
            db_tool.source = tool.get("source")
            db_tool.description = tool.get("description")
            db_tool.tlp = tool.get("tlp")
            db_tool.license = tool.get("license")
            db_tool.last_db_change = tool.get("last-db-change")

            for value in tool.get("values", []):
                value_uuid = UUID(str(value["uuid"]))  # Convert string to UUID object
                db_value = (
                    session.query(AllToolsValues)
                    .filter(AllToolsValues.uuid == value_uuid)
                    .first()
                )
                if not db_value:
                    db_value = AllToolsValues(uuid=value_uuid)
                    db_tool.values.append(db_value)

                db_value.tool = value.get("tool")
                db_value.description = value.get("description")
                db_value.category = value.get("category")
                db_value.type = (
                    ", ".join(value.get("type"))
                    if isinstance(value.get("type"), list)
                    else value.get("type") or "Unknown"  # Set default value if None
                )
                db_value.information = (
                    ", ".join(value.get("information", []))
                    if isinstance(value.get("information"), list)
                    else (value.get("information") or "")
                )
                db_value.last_card_change = value.get("last-card-change")

                for name_data in value.get("names", []):
                    name = (
                        name_data["name"] if isinstance(name_data, dict) else name_data
                    )
                    db_name = (
                        session.query(AllToolsValuesNames)
                        .filter(AllToolsValuesNames.name == name)
                        .first()
                    )
                    if not db_name:
                        db_name = AllToolsValuesNames(
                            name=name,
                            uuid=uuid.uuid4(),  # Generate a new UUID object
                            alltools_values_uuid=db_value.uuid,
                        )
                        db_value.names.append(db_name)
        except Exception as e:
            logger.error(
                f"Error processing tool {tool.get('name', 'Unknown')}: {str(e)}"
            )
            session.rollback()
        else:
            session.commit()


import json
import uuid
from uuid import UUID

def update_allgroups(session: Session, data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> None:
    if isinstance(data, dict):
        data = [data]

    for group in data:
        try:
            logger.debug(f"Processing group: {group.get('actor', 'Unknown')}")
            
            if "uuid" not in group:
                logger.error(f"Group is missing UUID: {group.get('actor', 'Unknown')}. Skipping this group.")
                continue

            try:
                group_uuid = UUID(group["uuid"])
            except ValueError as e:
                logger.error(f"Invalid UUID for group {group.get('actor', 'Unknown')}: {group['uuid']}. Error: {str(e)}")
                continue

            db_group = session.query(AllGroups).filter(AllGroups.uuid == group_uuid).first()
            if not db_group:
                db_group = AllGroups(uuid=group_uuid)
                session.add(db_group)

            # Update AllGroups fields
            db_group.category = group.get("category", "")
            db_group.name = group.get("name", "")
            db_group.type = group.get("type", "")
            db_group.source = group.get("source", "")
            db_group.description = group.get("description", "")
            db_group.tlp = group.get("tlp", "")
            db_group.license = group.get("license", "")
            db_group.last_db_change = group.get("last-card-change", "")

            # Process AllGroupsValues
            db_value = session.query(AllGroupsValues).filter(AllGroupsValues.uuid == group_uuid).first()
            if not db_value:
                db_value = AllGroupsValues(uuid=group_uuid, allgroups_uuid=group_uuid)
                db_group.values.append(db_value)

            # Update AllGroupsValues fields
            db_value.actor = group.get("actor", "")
            db_value.country = ", ".join(group["country"]) if isinstance(group.get("country"), list) else group.get("country", "")
            db_value.description = group.get("description", "")
            db_value.information = ", ".join(group["information"]) if isinstance(group.get("information"), list) else group.get("information", "")
            db_value.last_card_change = group.get("last-card-change", "")
            db_value.motivation = ", ".join(group["motivation"]) if isinstance(group.get("motivation"), list) else group.get("motivation", "")
            db_value.first_seen = group.get("first-seen", "")
            db_value.observed_sectors = ", ".join(group.get("observed-sectors", []))
            db_value.observed_countries = ", ".join(group.get("observed-countries", []))
            db_value.tools = ", ".join(group.get("tools", []))
            db_value.sponsor = group.get("sponsor", "")
            
            # Handle operations
            operations = group.get("operations", [])
            db_value.operations = json.dumps(operations) if operations else ""

            # Handle counter-operations
            counter_operations = group.get("counter-operations", [])
            db_value.counter_operations = json.dumps(counter_operations) if counter_operations else ""

            # Handle MITRE ATT&CK
            db_value.mitre_attack = ", ".join(group.get("mitre-attack", []))

            # Handle names
            existing_names = {name.name: name for name in db_value.names}
            for name_data in group.get("names", []):
                name = name_data.get("name")
                name_giver = name_data.get("name-giver")

                if not name:
                    logger.warning(f"Empty name found for group {group.get('actor', 'Unknown')}")
                    continue

                if name in existing_names:
                    db_name = existing_names[name]
                    db_name.name_giver = name_giver
                else:
                    db_name = AllGroupsValuesNames(
                        name=name,
                        name_giver=name_giver,
                        uuid=uuid.uuid4(),
                        allgroups_values_uuid=db_value.uuid
                    )
                    db_value.names.append(db_name)
                
                logger.debug(f"Processed name: {name}, name_giver: {name_giver}")

            session.add(db_value)
            session.flush()  # This will assign IDs to new objects without committing

        except Exception as e:
            logger.error(f"Error processing group {group.get('actor', 'Unknown')}: {str(e)}")
            logger.exception("Exception details:")
            session.rollback()
        else:
            session.commit()  # Commit after each group is processed successfully

    # Final commit to ensure all changes are saved
    session.commit()


def update_databases() -> None:
    """
    Update the AllTools and AllGroups databases with the latest data from the local JSON files.
    """
    with current_app.app_context():
        create_db_tables()

        engine = create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"])
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Update AllTools
            tools_data = load_json_file(
                "app/static/json/Threat Group Card - All tools.json"
            )
            if tools_data is not None:
                if isinstance(tools_data, list):
                    logger.info(f"Loaded AllTools data: {len(tools_data)} items")
                elif isinstance(tools_data, dict):
                    logger.info("Loaded AllTools data: 1 item")
                    tools_data = [tools_data]  # Convert single dict to list
                else:
                    logger.error(f"Invalid AllTools data type: {type(tools_data)}")
                    tools_data = None

                if tools_data:
                    update_alltools(session, tools_data)
                    logger.info("AllTools database updated successfully.")
            else:
                logger.warning("Failed to load AllTools data. Skipping update.")

            # Update AllGroups
            groups_data = load_json_file(
                "app/static/json/Threat Group Card - All groups.json"
            )
            if groups_data is not None:
                logger.info(f"Loaded AllGroups data: {len(groups_data)} items")
                
                # Print a sample of the loaded data
                if groups_data:
                    sample_group = groups_data[0]
                    logger.debug(f"Sample group data: {json.dumps(sample_group, indent=2)}")
                    
                    if 'values' in sample_group and sample_group['values']:
                        sample_value = sample_group['values'][0]
                        logger.debug(f"Sample value data: {json.dumps(sample_value, indent=2)}")
                        
                        if 'names' in sample_value and sample_value['names']:
                            sample_name = sample_value['names'][0]
                            logger.debug(f"Sample name data: {json.dumps(sample_name, indent=2)}")
                
                update_allgroups(session, groups_data)
                logger.info("AllGroups database updated successfully.")

                # Verify data insertion
                groups_count = session.query(AllGroups).count()
                values_count = session.query(AllGroupsValues).count()
                names_count = session.query(AllGroupsValuesNames).count()
                logger.info(f"AllGroups count: {groups_count}")
                logger.info(f"AllGroupsValues count: {values_count}")
                logger.info(f"AllGroupsValuesNames count: {names_count}")

                # Add detailed counts per group
                for group in session.query(AllGroups).all():
                    values_count = len(group.values)
                    names_count = sum(len(value.names) for value in group.values)
                    logger.info(f"Group {group.name}: Values count: {values_count}, Names count: {names_count}")
            else:
                logger.warning("Failed to load AllGroups data. Skipping update.")

            # Check if any data was actually added
            tool_count = session.query(AllTools).count()
            group_count = session.query(AllGroups).count()
            logger.info(f"Total number of tools in the database after update: {tool_count}")
            logger.info(f"Total number of groups in the database after update: {group_count}")

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"An error occurred: {str(e)}")
            logger.exception("Exception details:")
        finally:
            session.close()


if __name__ == "__main__":
    update_databases()
