from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
from models import SearchParams, SearchResult
from datetime import datetime

app = Flask(__name__)
engine = create_engine('sqlite:///threats.db')  # Replace with your actual database URL

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    search_params = SearchParams(
        query=request.args.get('query', ''),
        start_date=request.args.get('start_date'),
        end_date=request.args.get('end_date'),
        source_types=request.args.getlist('source_types'),
        keywords=request.args.getlist('keywords')
    )

    query = """
        SELECT id, title, description, source_type, date, url
        FROM threats
        WHERE title LIKE :query OR description LIKE :query
    """
    
    params = {'query': f'%{search_params.query}%'}

    if search_params.start_date:
        query += " AND date >= :start_date"
        params['start_date'] = search_params.start_date

    if search_params.end_date:
        query += " AND date <= :end_date"
        params['end_date'] = search_params.end_date

    if search_params.source_types:
        query += " AND source_type IN :source_types"
        params['source_types'] = tuple(search_params.source_types)

    if search_params.keywords:
        for i, keyword in enumerate(search_params.keywords):
            query += f" AND (title LIKE :keyword{i} OR description LIKE :keyword{i})"
            params[f'keyword{i}'] = f'%{keyword}%'

    query = text(query)

    with engine.connect() as conn:
        result = conn.execute(query, params)
        results = [SearchResult(**row._mapping) for row in result]

    return render_template('search_results.html', results=results, search_params=search_params)

if __name__ == '__main__':
    app.run(debug=True)
