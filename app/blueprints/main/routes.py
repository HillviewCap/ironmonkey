from flask import Blueprint, render_template, send_from_directory
import os

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(main.root_path, '..', '..', 'static', 'images'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
