import click
from flask.cli import with_appcontext

@click.command('initialize-awesome-feeds')
@with_appcontext
def initialize_awesome_feeds_command():
    """Initialize Awesome Threat Intel Feeds."""
    from app.services.awesome_threat_intel_service import AwesomeThreatIntelService
    AwesomeThreatIntelService.initialize_awesome_feeds()
    click.echo('Initialized the Awesome Threat Intel Feeds.')

@click.command('update-apt-databases')
@with_appcontext
def update_apt_databases_command():
    """Update APT databases."""
    from app.services.apt_update_service import update_databases
    update_databases()
    click.echo('APT databases updated.')
