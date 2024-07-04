from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
from models import SearchParams, SearchResult, User, db
from datetime import datetime
from flask_login import login_required, current_user
from auth import init_auth
import os
from dotenv import load_dotenv
from werkzeug.exceptions import BadRequest
import bleach

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db.init_app(app)
init_auth(app)

with app.app_context():
    db.create_all()


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/search', methods=['POST'])
@login_required
def search():
    try:
        data = request.json
        search_params = SearchParams(**data)
    except ValueError as e:
        raise BadRequest(str(e))

    query = """
        SELECT id, title, description, source_type, date, url
        FROM threats
        WHERE (title LIKE :query OR description LIKE :query)
    """
    
    params = {'query': f'%{bleach.clean(search_params.query)}%'}

    if search_params.start_date:
        query += " AND date >= :start_date"
        params['start_date'] = search_params.start_date

    if search_params.end_date:
        query += " AND date <= :end_date"
        params['end_date'] = search_params.end_date

    if search_params.source_types:
        query += f" AND source_type IN ({','.join([':source_type_' + str(i) for i in range(len(search_params.source_types))])})"
        for i, source_type in enumerate(search_params.source_types):
            params[f'source_type_{i}'] = bleach.clean(source_type)

    if search_params.keywords:
        for i, keyword in enumerate(search_params.keywords):
            query += f" AND (title LIKE :keyword{i} OR description LIKE :keyword{i})"
            params[f'keyword{i}'] = f'%{bleach.clean(keyword)}%'

    query = text(query)

    with db.engine.connect() as conn:
        result = conn.execute(query, params)
        results = [SearchResult(**row._mapping) for row in result]

    return jsonify([result.dict() for result in results])

if __name__ == '__main__':
    app.run(debug=True)
