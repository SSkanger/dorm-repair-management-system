from flask import Blueprint

from .auth import login_required
from .tickets import render_ticket_overview

bp = Blueprint("dashboard", __name__)


@bp.get("/dashboard")
@login_required
def index():
    return render_ticket_overview("dashboard.html", include_items=False)
