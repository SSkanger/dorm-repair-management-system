from __future__ import annotations

import sqlite3

from flask import Blueprint, abort, g, jsonify, render_template

from .auth import login_required, role_required
from .db import get_db, verify_schema
from .queries import TicketFilters, ticket_overview


bp = Blueprint("pages", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/health")
def health():
    try:
        connection = get_db()
        connection.execute("SELECT 1").fetchone()
        verify_schema(connection)
    except (sqlite3.Error, RuntimeError):
        return jsonify(status="unhealthy"), 503
    return jsonify(status="ok", database="ready"), 200


@bp.get("/portal")
@login_required
def portal():
    if g.user["role"] == "student":
        return _render_portal("学生入口")
    if g.user["role"] == "repairer":
        return _render_portal("维修人员入口")
    abort(403)


def _render_portal(role_title):
    overview = ticket_overview(g.user["id"], g.user["role"], TicketFilters())
    return render_template("portal.html", role_title=role_title, overview=overview)


@bp.get("/student/portal")
@role_required("student")
def student_portal():
    return _render_portal("学生入口")


@bp.get("/repairer/portal")
@role_required("repairer")
def repairer_portal():
    return _render_portal("维修人员入口")

