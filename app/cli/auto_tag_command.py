import click
from flask.cli import with_appcontext
from app.utils.auto_tagger import tag_all_content

@click.command('auto-tag')
@click.option('--force', is_flag=True, help='Force re-tagging of all documents, including previously tagged ones.')
@with_appcontext
def auto_tag_command(force):
    """Automatically tag all parsed content."""
    if force:
        click.echo('Force re-tagging all documents...')
    else:
        click.echo('Tagging untagged documents...')
    tag_all_content(force_all=force)
    click.echo('Auto-tagging completed.')

def init_app(app):
    app.cli.add_command(auto_tag_command)
