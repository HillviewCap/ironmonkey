from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from . import bp
from app.extensions import db

@bp.route('/', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        data = request.json
        current_user.update_preferences(**data)
        return jsonify({"message": "Settings updated successfully"}), 200
    return render_template('user_settings.html', user=current_user)
