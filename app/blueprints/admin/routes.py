from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models.relational import User
from app.models import db
from sqlalchemy import desc

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/")
@login_required
def admin():
    """
    Render the admin page with users table.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    sort = request.args.get('sort', 'created_at')
    search = request.args.get('search', '')

    query = User.query

    if search:
        query = query.filter(User.email.ilike(f'%{search}%'))

    if sort == 'email':
        query = query.order_by(User.email)
    elif sort == 'created_at':
        query = query.order_by(desc(User.created_at))

    users = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template("admin.html", users=users)
