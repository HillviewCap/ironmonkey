from flask import render_template
from app.services.parsed_content_service import ParsedContentService
from app import app  # Import the app object

@app.route('/parsed_content')
def parsed_content():
    content_service = ParsedContentService()
    latest_content = content_service.get_latest_parsed_content()
    return render_template('parsed_content.html', content=latest_content)
