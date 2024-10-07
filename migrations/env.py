from __future__ import with_statement

import logging
import os
from logging.config import fileConfig

from app import create_app
from flask import current_app

# Initialize the Flask application
app = create_app()


from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except TypeError:
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# Import models for Alembic to detect them
from app.models.relational.allgroups import AllGroups, AllGroupsValues, AllGroupsValuesNames
from app.models.relational.awesome_threat_intel_blog import AwesomeThreatIntelBlog
from app.models.relational.parsed_content import ParsedContent
from app.models.relational.rss_feed import RSSFeed
from app.models.relational.user import User
from app.models.relational.user_questionnaire import UserQuestionnaire
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


target_metadata = target_db.metadata


def ensure_versions_directory():
    """Ensure that the versions directory exists."""
    versions_path = os.path.join(os.path.dirname(__file__), 'versions')
    if not os.path.exists(versions_path):
        os.makedirs(versions_path)
        logger.info(f"Created versions directory: {versions_path}")

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    ensure_versions_directory()

    with app.app_context():
        url = config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url, target_metadata=target_metadata, literal_binds=True
        )

        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    ensure_versions_directory()

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    with app.app_context():
        connectable = get_engine()

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                process_revision_directives=process_revision_directives,
                **current_app.extensions['migrate'].configure_args
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
