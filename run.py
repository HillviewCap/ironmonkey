import os
from dotenv import load_dotenv
from app import create_app
from app.extensions import db
from app.models.relational.user import User
from config import get_config

load_dotenv()

env = os.getenv("FLASK_ENV", "development")
config_obj = get_config(env)
app = create_app(config_obj)

@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User}

def main():
    if app.config['ENV'] == 'production':
        from waitress import serve
        serve(app, 
              host=app.config['WAITRESS_HOST'], 
              port=app.config['WAITRESS_PORT'],
              threads=app.config['WAITRESS_THREADS'])
    else:
        app.run(host=app.config['HOST'],
                port=app.config['PORT'],
                debug=app.config.get('DEBUG', False))

if __name__ == "__main__":
    main()
