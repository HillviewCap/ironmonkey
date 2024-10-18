import click
from flask.cli import with_appcontext
from app.utils.auto_tagger import tag_all_content
from app.utils.logging_config import setup_logger
import logging
import traceback
import sys

logger = setup_logger('auto_tag_command', 'auto_tag_command.log', level=logging.DEBUG)

@click.command('auto-tag')
@click.option('--force', is_flag=True, help='Force re-tagging of all documents, including previously tagged ones.')
@with_appcontext
def auto_tag_command(force):
    """Automatically tag all parsed content."""
    try:
        if force:
            logger.info('Force re-tagging all documents...')
            click.echo('Force re-tagging all documents...')
        else:
            logger.info('Tagging untagged documents...')
            click.echo('Tagging untagged documents...')
        
        tag_all_content(force_all=force)
        
        logger.info('Auto-tagging completed.')
        click.echo('Auto-tagging completed.')
    except Exception as e:
        logger.error(f"An error occurred during auto-tagging: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        click.echo(f"An error occurred during auto-tagging. Check the logs for details.")
        sys.exit(1)  # Exit with an error code

def init_app(app):
    app.cli.add_command(auto_tag_command)
