import os
from dotenv import load_dotenv
from app import create_app
from app.extensions import db
from app.models.relational.user import User
from app.models.init_db import init_db

load_dotenv()

app = create_app()
init_db(app)  # Initialize the database

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

def main():
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )

if __name__ == '__main__':
    main()
