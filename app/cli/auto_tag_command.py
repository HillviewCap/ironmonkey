import click
from flask.cli import with_appcontext
from app.utils.auto_tagger import tag_all_content

@click.command('auto-tag')
@with_appcontext
def auto_tag_command():
    """Automatically tag all parsed content."""
    tag_all_content()
    click.echo('Auto-tagging completed.')

def init_app(app):
    app.cli.add_command(auto_tag_command)
