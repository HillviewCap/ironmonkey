from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text
from models import SearchParams, SearchResult, User, db, RSSFeed
from datetime import datetime
from flask_login import login_required, current_user
from auth import init_auth, login, logout, register
import os
from dotenv import load_dotenv
from werkzeug.exceptions import BadRequest
import bleach
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db.init_app(app)
csrf = CSRFProtect(app)
init_auth(app)
migrate = Migrate(app, db)

app.route('/login', methods=['GET', 'POST'])(login)
app.route('/logout')(logout)
app.route('/register', methods=['GET', 'POST'])(register)

from rss_manager import rss_manager
app.register_blueprint(rss_manager)

with app.app_context():
    db.create_all()

from auth import index

app.route('/')(index)

@app.route('/search', methods=['POST'])
@login_required
def search():
    try:
        data = request.json
        search_params = SearchParams(**data)
    except ValueError as e:
        raise BadRequest(str(e))

    query = db.session.query(Threat)
    
    query = query.filter(
        db.or_(
            Threat.title.ilike(f'%{bleach.clean(search_params.query)}%'),
            Threat.description.ilike(f'%{bleach.clean(search_params.query)}%')
        )
    )

    if search_params.start_date:
        query = query.filter(Threat.date >= search_params.start_date)

    if search_params.end_date:
        query = query.filter(Threat.date <= search_params.end_date)

    if search_params.source_types:
        query = query.filter(Threat.source_type.in_([bleach.clean(st) for st in search_params.source_types]))

    if search_params.keywords:
        for keyword in search_params.keywords:
            query = query.filter(
                db.or_(
                    Threat.title.ilike(f'%{bleach.clean(keyword)}%'),
                    Threat.description.ilike(f'%{bleach.clean(keyword)}%')
                )
            )

    results = query.all()
    return jsonify([SearchResult(
        id=str(threat.id),
        title=threat.title,
        description=threat.description,
        source_type=threat.source_type,
        date=threat.date,
        url=threat.url
    ).dict() for threat in results])

if __name__ == '__main__':
    app.run(debug=True)
