from flask import Blueprint, render_template
from flask_login import login_required
from app.models.relational import User

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/")
@login_required
def admin():
    """
    Render the admin page with users table.
    """
    users = User.query.all()
    return render_template("admin.html", users=users)
