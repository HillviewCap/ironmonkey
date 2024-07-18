import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app

flask_env = os.getenv('FLASK_ENV', 'production')
app = create_app(flask_env)

def create_wsgi_app() -> tuple:
    """Create the WSGI app with port and debug settings."""
    port: int = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() in ['true', '1', 'yes']
    return app, port, debug

if __name__ == "__main__":
    app, port, debug = create_wsgi_app()
    app.run(host='0.0.0.0', port=port, debug=debug)
