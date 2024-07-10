from app import create_app
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

flask_env = os.getenv('FLASK_ENV', 'production')
app = create_app(flask_env)

if __name__ == "__main__":
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
