import json
from flask import Flask

def create_app(config_name):
    app = Flask(__name__)
    # ... other configuration ...

    @app.template_filter('json_loads')
    def json_loads_filter(s):
        return json.loads(s) if s else []

    # ... rest of your create_app function ...

    return app
