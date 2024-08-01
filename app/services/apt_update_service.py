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
                    ", ".join(value.get("information"))
                    if isinstance(value.get("information"), list)
                    else value.get("information")
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
    for group in data:
        try:
            group_uuid = UUID(group["uuid"])  # Convert string UUID to UUID object
            db_group = (
                session.query(AllGroups).filter(AllGroups.uuid == group_uuid).first()
            )
            if not db_group:
                db_group = AllGroups(uuid=group_uuid)
                session.add(db_group)

            db_group.authors = (
                ", ".join(group.get("authors", []))
                if isinstance(group.get("authors"), list)
                else group.get("authors")
            )
        db_group.category = group.get("category")
        db_group.name = group.get("name")
        db_group.type = group.get("type")
        db_group.source = group.get("source")
        db_group.description = group.get("description")
        db_group.tlp = group.get("tlp")
        db_group.license = group.get("license")
        db_group.last_db_change = group.get("last-db-change")

        for value in group.get("values", []):
            value_uuid = UUID(str(value["uuid"]))  # Convert string to UUID object
            db_value = (
                session.query(AllGroupsValues)
                .filter(AllGroupsValues.uuid == value_uuid)
                .first()
            )
            if not db_value:
                db_value = AllGroupsValues(uuid=value_uuid)
                db_group.values.append(db_value)

            db_value.actor = value.get("actor")
            db_value.country = (
                ", ".join(value.get("country", []))
                if isinstance(value.get("country"), list)
                else value.get("country")
            )
            db_value.description = value.get("description")
            db_value.information = (
                ", ".join(value.get("information", []))
                if isinstance(value.get("information"), list)
                else value.get("information")
            )
            db_value.last_card_change = value.get("last-card-change")
            db_value.motivation = (
                ", ".join(value.get("motivation", []))
                if isinstance(value.get("motivation"), list)
                else value.get("motivation")
            )
            db_value.first_seen = value.get("first-seen")
            db_value.observed_sectors = (
                ", ".join(value.get("observed-sectors", []))
                if isinstance(value.get("observed-sectors"), list)
                else value.get("observed-sectors")
            )
            db_value.observed_countries = (
                ", ".join(value.get("observed-countries", []))
                if isinstance(value.get("observed-countries"), list)
                else value.get("observed-countries")
            )
            db_value.tools = (
                ", ".join(value.get("tools", []))
                if isinstance(value.get("tools"), list)
                else value.get("tools")
            )
            db_value.sponsor = value.get("sponsor")

            # Handle operations separately as it's a list of dictionaries
            if "operations" in value and isinstance(value["operations"], list):
                operations_json = json.dumps(value["operations"])
                db_value.operations = operations_json
            else:
                db_value.operations = None

            # Handle counter-operations
            if "counter-operations" in value and isinstance(
                value["counter-operations"], list
            ):
                counter_operations_json = json.dumps(value["counter-operations"])
                db_value.counter_operations = counter_operations_json
            else:
                db_value.counter_operations = None

            # Handle mitre-attack
            if "mitre-attack" in value and isinstance(value["mitre-attack"], list):
                db_value.mitre_attack = ", ".join(value["mitre-attack"])
            else:
                db_value.mitre_attack = None

            # Handle playbook
            if "playbook" in value and isinstance(value["playbook"], list):
                db_value.playbook = ", ".join(value["playbook"])
            else:
                db_value.playbook = None

            for name_data in value.get("names", []):
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
                        uuid=str(uuid.uuid4()),
                        allgroups_values_uuid=db_value.uuid,
                    )
                    db_value.names.append(db_name)
                else:
                    db_name.name_giver = name_data.get("name-giver")


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
                    logger.debug(
                        f"tools_data content: {str(tools_data)[:500]}..."
                    )  # Log first 500 characters
            else:
                logger.warning("Failed to load AllTools data. Skipping update.")

            # Update AllGroups
            groups_data = load_json_file("app/static/json/Threat Group Card - All groups.json")
            if groups_data is not None:
                if isinstance(groups_data, dict) and "values" in groups_data:
                    update_allgroups(session, [groups_data])
                    logger.info(
                        "AllGroups database updated successfully (single group data)."
                    )
                elif isinstance(groups_data, list):
                    update_allgroups(session, groups_data)
                    logger.info("AllGroups database updated successfully.")
                else:
                    logger.error(
                        f"Unexpected data type for groups_data: {type(groups_data)}. Expected a list or a dict with 'values'."
                    )
                    logger.debug(
                        f"groups_data content: {str(groups_data)[:500]}..."
                    )  # Log first 500 characters
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
