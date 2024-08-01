from __future__ import annotations

import json
import logging
from typing import Dict, List, Any, Optional
import httpx
from sqlalchemy import create_engine, inspect
from uuid import UUID
from sqlalchemy.orm import sessionmaker, Session
from app.models.relational.alltools import AllTools, AllToolsValues, AllToolsValuesNames
from app.models.relational.allgroups import AllGroups, AllGroupsValues, AllGroupsValuesNames
import uuid
from flask import current_app

logger = logging.getLogger(__name__)


def load_json_file(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load JSON data from a local file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        Optional[List[Dict[str, Any]]]: The JSON data as a list of dictionaries, or None if an error occurs.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
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
        try:
            with session.no_autoflush:
                tool_uuid = UUID(tool["uuid"])  # Convert string UUID to UUID object
                db_tool = session.query(AllTools).filter(AllTools.uuid == tool_uuid).first()
                if not db_tool:
                    db_tool = AllTools(uuid=tool_uuid)
                    session.add(db_tool)

                db_tool.authors = (
                    ", ".join(tool.get("authors", []))
                if isinstance(tool.get("authors"), list)
                else tool.get("authors")
            )
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
                    name = name_data["name"] if isinstance(name_data, dict) else name_data
                    db_name = (
                        session.query(AllToolsValuesNames)
                        .filter(AllToolsValuesNames.name == name)
                        .first()
                    )
                    if not db_name:
                        db_name = AllToolsValuesNames(
                            name=name,
                            uuid=uuid.uuid4(),  # Generate a new UUID object
                            alltools_values_uuid=db_value.uuid
                        )
                        db_value.names.append(db_name)
        except Exception as e:
            logger.error(f"Error processing tool {tool.get('name', 'Unknown')}: {str(e)}")
            session.rollback()
        else:
            session.commit()


def update_allgroups(session: Session, data: List[Dict[str, Any]]) -> None:
    """
    Update the AllGroups database with the given data.

    Args:
        session (Session): The SQLAlchemy session.
        data (List[Dict[str, Any]]]: The data to update the database with.
    """
    if not isinstance(data, list):
        logger.error(f"Expected a list of groups, but got {type(data)}. Converting to list.")
        data = [data]

    for group in data:
        try:
            if "uuid" not in group:
                logger.error(f"Group is missing UUID: {group.get('name', 'Unknown')}. Skipping this group.")
                continue

            try:
                group_uuid = UUID(group["uuid"])  # Convert string UUID to UUID object
            except ValueError:
                logger.warning(f"Invalid UUID for group: {group.get('name', 'Unknown')} - UUID: {group['uuid']}. Attempting to fix.")
                try:
                    # Try to pad the UUID if it's too short
                    padded_uuid = group["uuid"].ljust(32, '0')
                    group_uuid = UUID(padded_uuid)
                    logger.info(f"Successfully fixed UUID for group: {group.get('name', 'Unknown')} - New UUID: {group_uuid}")
                except ValueError:
                    logger.error(f"Unable to fix UUID for group: {group.get('name', 'Unknown')} - UUID: {group['uuid']}. Skipping this group.")
                    continue

            db_group = session.query(AllGroups).filter(AllGroups.uuid == group_uuid).first()
            if not db_group:
                db_group = AllGroups(uuid=group_uuid)
                session.add(db_group)

            # Update AllGroups fields
            for field in ['authors', 'category', 'name', 'type', 'source', 'description', 'tlp', 'license']:
                setattr(db_group, field, group.get(field, ""))
            db_group.last_db_change = group.get("last-db-change", "")


            # Process AllGroupsValues
            db_value = session.query(AllGroupsValues).filter(AllGroupsValues.uuid == group_uuid).first()
            if not db_value:
                db_value = AllGroupsValues(uuid=group_uuid)
                db_group.values.append(db_value)

            # Update AllGroupsValues fields
            for field in ['actor', 'country', 'description', 'information', 'motivation', 'sponsor']:
                value = group.get(field, "")
                if isinstance(value, list):
                    value = ", ".join(value)
                setattr(db_value, field, value)

            # Handle fields that need special treatment
            db_value.first_seen = group.get("first-seen", "")
            db_value.observed_sectors = ", ".join(group.get("observed-sectors", []))
            db_value.observed_countries = ", ".join(group.get("observed-countries", []))
            db_value.tools = ", ".join(group.get("tools", []))
            db_value.last_card_change = group.get("last-card-change", "")

            # Handle special fields
            for field in ['operations', 'counter_operations']:
                json_field = field.replace('_', '-')
                if json_field in group and isinstance(group[json_field], list):
                    setattr(db_value, field, json.dumps(group[json_field]))
                else:
                    setattr(db_value, field, None)

            for field in ['mitre_attack', 'playbook']:
                json_field = field.replace('_', '-')
                if json_field in group and isinstance(group[json_field], list):
                    setattr(db_value, field, ", ".join(group[json_field]))
                else:
                    setattr(db_value, field, None)


            # Handle names
            for name_data in group.get("names", []):
                db_name = (
                    session.query(AllGroupsValuesNames)
                    .filter(
                        AllGroupsValuesNames.name == name_data["name"],
                        AllGroupsValuesNames.allgroups_values_uuid == db_value.uuid,
                    )
                    .first()
                )
                if not db_name:
                    db_name = AllGroupsValuesNames(
                        name=name_data["name"],
                        name_giver=name_data.get("name-giver"),
                        uuid=uuid.uuid4(),  # Generate a new UUID object
                        allgroups_values_uuid=db_value.uuid,  # Use the UUID object directly
                    )
                    db_value.names.append(db_name)
                else:
                    db_name.name_giver = name_data.get("name-giver")

            session.commit()
            logger.info(f"Successfully updated group: {group.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error processing group {group.get('name', 'Unknown')}: {str(e)}")
            session.rollback()
        else:
            session.commit()


def update_databases() -> None:
    """
    Update the AllTools and AllGroups databases with the latest data from the local JSON files.
    """
    with current_app.app_context():
        engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Check if tables exist
            inspector = inspect(engine)
            if not inspector.has_table("alltools") or not inspector.has_table("allgroups"):
                logger.error(
                    "Required tables do not exist. Creating tables now."
                )
                AllTools.__table__.create(engine)
                AllGroups.__table__.create(engine)
                logger.info("Tables created successfully.")

            # Update AllTools
            tools_data = load_json_file("app/static/json/Threat Group Card - All tools.json")
            if tools_data is not None:
                if isinstance(tools_data, dict) and "values" in tools_data:
                    update_alltools(session, [tools_data])
                    logger.info(
                        "AllTools database updated successfully (single tool data)."
                    )
                elif isinstance(tools_data, list):
                    update_alltools(session, tools_data)
                    logger.info("AllTools database updated successfully.")
                else:
                    logger.error(
                        f"Unexpected data type for tools_data: {type(tools_data)}. Expected a list or a dict with 'values'."
                    )
            else:
                logger.warning("Failed to load AllTools data. Skipping update.")

            # Update AllGroups
            groups_data = load_json_file("app/static/json/Threat Group Card - All groups.json")
            if groups_data is not None:
                if isinstance(groups_data, dict) and "values" in groups_data:
                    logger.info(f"Processing group data with {len(groups_data['values'])} values.")
                    update_allgroups(session, groups_data["values"])
                elif isinstance(groups_data, list):
                    logger.info(f"Processing list of {len(groups_data)} groups.")
                    update_allgroups(session, groups_data)
                else:
                    logger.error(f"Unexpected data type for groups_data: {type(groups_data)}. Expected a list or a dict with 'values'.")
                
                # Check if any groups were actually added
                group_count = session.query(AllGroups).count()
                logger.info(f"Total number of groups in the database after update: {group_count}")
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
