from __future__ import annotations

import sqlite3
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.db import connect_database, get_db
from tests.conftest import extract_csrf, login
from tests.test_tickets import create_via_http


def actors(app):
    clients = {}
    for name in ("student_a", "student_b", "repairer_a", "repairer_b"):
        client = app.test_client()
        assert login(client, name).status_code == 303
        clients[name] = client
    return clients


def post_action(client, ticket_id, action, **values):
    token = extract_csrf(client.get("/portal"))
    return client.post(
        f"/tickets/{ticket_id}/{action}",
        data={"csrf_token": token, **values}, follow_redirects=False,
    )


def snapshot(app, ticket_id):
    with app.app_context():
        return dict(get_db().execute(
            "SELECT * FROM repair_tickets WHERE id=?", (ticket_id,)
        ).fetchone())


def prepared_ticket(app, state="PENDING", *, confirmed=False):
    """Independent legal fixture, with explicit fixed historical timestamps."""
    with app.app_context():
        db = get_db()
        users = {r["username"]: r["id"] for r in db.execute("SELECT id, username FROM users")}
        t0 = "2026-01-01T00:00:00.000000Z"
        assigned = None if state == "PENDING" else "2026-01-01T01:00:00.000000Z"
        started = "2026-01-01T02:00:00.000000Z" if state in {"IN_PROGRESS", "COMPLETED"} else None
        completed = "2026-01-01T03:00:00.000000Z" if state == "COMPLETED" else None
        confirmation = "2026-01-01T04:00:00.000000Z" if confirmed else None
        cursor = db.execute(
            "INSERT INTO repair_tickets (student_id, assignee_id, building, room_number, "
            "category, description, status, created_at, updated_at, assigned_at, started_at, "
            "completed_at, confirmed_at, submission_token) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (users["student_a"], users["repairer_a"] if assigned else None,
             "3号楼", "406", "照明", "宿舍照明灯无法点亮。", state, t0,
             confirmation or completed or started or assigned or t0,
             assigned, started, completed, confirmation, uuid4().hex),
        )
        db.commit()
        return cursor.lastrowid


def test_fixture_request_tokens_remain_unique_when_clock_is_frozen(app, monkeypatch):
    # A clock tick is not a unique request identifier, including on Windows.
    frozen = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    monkeypatch.setattr("app.db.datetime", SimpleNamespace(now=lambda _tz: frozen))
    ticket_ids = [prepared_ticket(app) for _ in range(25)]
    with app.app_context():
        tokens = [row[0] for row in get_db().execute(
            "SELECT submission_token FROM repair_tickets"
        )]
    assert len(set(ticket_ids)) == 25
    assert len(tokens) == len(set(tokens)) == 25


def test_web_full_workflow_fields_and_buttons(app):
    users = actors(app)
    student, repairer = users["student_a"], users["repairer_a"]
    response = create_via_http(student)
    assert response.status_code == 303
    ticket_id = int(response.headers["Location"].rsplit("/", 1)[1])
    original = snapshot(app, ticket_id)
    assert "确认完成</button>" not in student.get(response.headers["Location"]).text
    assert "接单</button>" in repairer.get(response.headers["Location"]).text
    with app.app_context():
        assignee = get_db().execute("SELECT id FROM users WHERE username='repairer_a'").fetchone()[0]

    for action, status, field in (
        ("accept", "ACCEPTED", "assigned_at"),
        ("start", "IN_PROGRESS", "started_at"),
        ("complete", "COMPLETED", "completed_at"),
    ):
        before = snapshot(app, ticket_id)
        result = post_action(repairer, ticket_id, action)
        assert result.status_code == 303
        assert result.headers["Location"] == f"/tickets/{ticket_id}"
        after = snapshot(app, ticket_id)
        assert after["status"] == status
        assert after["assignee_id"] == assignee
        assert after[field] == after["updated_at"]
        assert after[field] >= before["updated_at"]
        assert after["student_id"] == original["student_id"]
        assert "维修员甲" in student.get(f"/tickets/{ticket_id}").text

    assert "确认完成</button>" in student.get(f"/tickets/{ticket_id}").text
    assert "完成维修</button>" not in repairer.get(f"/tickets/{ticket_id}").text
    assert post_action(student, ticket_id, "confirm").status_code == 303
    confirmed = snapshot(app, ticket_id)
    assert confirmed["status"] == "COMPLETED"
    assert confirmed["confirmed_at"] == confirmed["updated_at"]
    assert 'name="rating"' in student.get(f"/tickets/{ticket_id}").text
    assert post_action(student, ticket_id, "review", rating="5", review_text="  维修及时  ").status_code == 303
    reviewed = snapshot(app, ticket_id)
    assert reviewed["rating"] == 5
    assert reviewed["review_text"] == "维修及时"
    assert reviewed["reviewed_at"] == reviewed["updated_at"]
    assert reviewed["reviewed_at"] >= reviewed["confirmed_at"]
    page = student.get(f"/tickets/{ticket_id}").text
    assert "5 / 5 分" in page and "维修及时" in page
    assert 'name="rating"' not in page


def test_all_invalid_transitions_and_permission_boundaries_leave_full_row_unchanged(app):
    users = actors(app)
    # Expectations are fixed by DESIGN sections 3.3 and 4, before exercising endpoints.
    cases = [
        ("PENDING", "repairer_a", "start", 404),
        ("PENDING", "repairer_a", "complete", 404),
        ("ACCEPTED", "repairer_a", "accept", 409),
        ("ACCEPTED", "repairer_a", "complete", 409),
        ("IN_PROGRESS", "repairer_a", "accept", 409),
        ("IN_PROGRESS", "repairer_a", "start", 409),
        ("COMPLETED", "repairer_a", "accept", 409),
        ("COMPLETED", "repairer_a", "start", 409),
        ("COMPLETED", "repairer_a", "complete", 409),
        ("ACCEPTED", "repairer_b", "accept", 404),
        ("ACCEPTED", "repairer_b", "start", 404),
        ("IN_PROGRESS", "repairer_b", "complete", 404),
        ("COMPLETED", "repairer_b", "accept", 404),
        ("PENDING", "student_a", "accept", 403),
        ("ACCEPTED", "student_a", "start", 403),
        ("IN_PROGRESS", "student_a", "complete", 403),
        ("COMPLETED", "student_b", "confirm", 404),
        ("COMPLETED", "student_b", "review", 404),
        ("COMPLETED", "repairer_a", "confirm", 403),
        ("COMPLETED", "repairer_a", "review", 403),
    ]
    for state, user, action, code in cases:
        ticket_id = prepared_ticket(app, state)
        before = snapshot(app, ticket_id)
        response = post_action(users[user], ticket_id, action, **({"rating": "5"} if action == "review" else {}))
        assert response.status_code == code, (state, user, action, response.text)
        assert snapshot(app, ticket_id) == before


def test_early_and_repeated_confirmation_and_review(app):
    users = actors(app)
    for state in ("PENDING", "ACCEPTED", "IN_PROGRESS"):
        ticket_id = prepared_ticket(app, state)
        before = snapshot(app, ticket_id)
        assert post_action(users["student_a"], ticket_id, "confirm").status_code == 409
        # State priority must be 409 even when the rating would also be invalid.
        assert post_action(users["student_a"], ticket_id, "review", rating="bad").status_code == 409
        assert snapshot(app, ticket_id) == before
    ticket_id = prepared_ticket(app, "COMPLETED")
    before = snapshot(app, ticket_id)
    assert post_action(users["student_a"], ticket_id, "review", rating="5").status_code == 409
    assert snapshot(app, ticket_id) == before
    assert post_action(users["student_a"], ticket_id, "confirm").status_code == 303
    confirmed = snapshot(app, ticket_id)
    assert post_action(users["student_a"], ticket_id, "confirm").status_code == 409
    assert snapshot(app, ticket_id) == confirmed
    assert post_action(users["student_a"], ticket_id, "review", rating="5", review_text="原始评价").status_code == 303
    reviewed = snapshot(app, ticket_id)
    assert post_action(users["student_a"], ticket_id, "review", rating="1", review_text="覆盖尝试").status_code == 409
    assert snapshot(app, ticket_id) == reviewed


def test_strict_rating_and_review_text_boundaries(app):
    client = app.test_client()
    assert login(client).status_code == 303
    for raw in ("", "0", "6", "1.5", "abc", "1.0", "True", " 5", "５", "01"):
        ticket_id = prepared_ticket(app, "COMPLETED", confirmed=True)
        before = snapshot(app, ticket_id)
        response = post_action(client, ticket_id, "review", rating=raw, review_text="保留合法短评")
        assert response.status_code == 400, raw
        assert "评分必须" in response.text
        assert "保留合法短评" in response.text
        assert snapshot(app, ticket_id) == before
    for rating, text, expected in (("1", "", None), ("5", "　　", None), ("5", "好" * 500, "好" * 500)):
        ticket_id = prepared_ticket(app, "COMPLETED", confirmed=True)
        assert post_action(client, ticket_id, "review", rating=rating, review_text=text).status_code == 303
        row = snapshot(app, ticket_id)
        assert row["rating"] == int(rating) and row["review_text"] == expected
    ticket_id = prepared_ticket(app, "COMPLETED", confirmed=True)
    before = snapshot(app, ticket_id)
    assert post_action(client, ticket_id, "review", rating="5", review_text="长" * 501).status_code == 400
    assert snapshot(app, ticket_id) == before


def test_review_text_escaping_and_missing_or_duplicate_rating(app):
    client = app.test_client()
    assert login(client).status_code == 303
    ticket_id = prepared_ticket(app, "COMPLETED", confirmed=True)
    before = snapshot(app, ticket_id)
    assert post_action(client, ticket_id, "review", review_text="没有评分").status_code == 400
    from werkzeug.datastructures import MultiDict
    token = extract_csrf(client.get("/portal"))
    response = client.post(f"/tickets/{ticket_id}/review", data=MultiDict([
        ("csrf_token", token), ("rating", "1"), ("rating", "5"),
    ]))
    assert response.status_code == 400
    assert snapshot(app, ticket_id) == before
    assert post_action(client, ticket_id, "review", rating="5", review_text="<script>alert('x')</script>").status_code == 303
    page = client.get(f"/tickets/{ticket_id}").text
    assert "&lt;script&gt;" in page and "<script>alert('x')</script>" not in page


def test_action_csrf_get_tampering_and_auth_priority(app):
    users = actors(app)
    ticket_id = prepared_ticket(app)
    before = snapshot(app, ticket_id)
    anonymous = app.test_client()
    anonymous_token = extract_csrf(anonymous.get("/login"))
    for action in ("accept", "start", "complete", "confirm", "review"):
        path = f"/tickets/{ticket_id}/{action}"
        assert users["repairer_a"].get(path).status_code == 405
        assert anonymous.post(path).status_code == 400
        assert anonymous.post(path, data={"csrf_token": anonymous_token}).status_code == 401
        assert users["student_a"].post(path, data={"csrf_token": "bad"}).status_code == 400
    assert post_action(users["repairer_a"], ticket_id, "accept", assignee_id="999", status="COMPLETED").status_code == 400
    assert snapshot(app, ticket_id) == before
    assert post_action(users["repairer_a"], 999999, "accept").status_code == 404
    assert post_action(users["repairer_a"], 99999999999999999999999, "accept").status_code == 404
    token = extract_csrf(users["repairer_a"].get("/portal"))
    assert users["repairer_a"].post(
        f"/tickets/{ticket_id}/rollback", data={"csrf_token": token}
    ).status_code == 404
    assert snapshot(app, ticket_id) == before


@pytest.mark.parametrize("failure", ["after_update", "commit"])
@pytest.mark.parametrize("action,state", [
    ("accept", "PENDING"), ("start", "ACCEPTED"), ("complete", "IN_PROGRESS"),
    ("confirm", "COMPLETED"), ("review", "COMPLETED"),
])
def test_transaction_failure_rolls_back_real_update(app, monkeypatch, failure, action, state):
    client = app.test_client()
    assert login(client, "student_a" if action in {"confirm", "review"} else "repairer_a").status_code == 303
    ticket_id = prepared_ticket(app, state, confirmed=action == "review")
    before = snapshot(app, ticket_id)
    real_get_db = get_db

    class FailingConnection:
        def __init__(self, connection):
            self.connection = connection

        def execute(self, sql, params=()):
            result = self.connection.execute(sql, params)
            if failure == "after_update" and sql.startswith("UPDATE repair_tickets"):
                raise sqlite3.OperationalError("injected failure after real UPDATE")
            return result

        def commit(self):
            if failure == "commit":
                raise sqlite3.OperationalError("injected commit failure")
            self.connection.commit()

        def rollback(self):
            self.connection.rollback()

    monkeypatch.setattr("app.services.get_db", lambda: FailingConnection(real_get_db()))
    values = {"rating": "5", "review_text": "正常评价"} if action == "review" else {}
    assert post_action(client, ticket_id, action, **values).status_code == 503
    assert snapshot(app, ticket_id) == before


def test_database_lock_timeout_is_503_without_change(app, monkeypatch):
    client = app.test_client()
    assert login(client, "repairer_a").status_code == 303
    ticket_id = prepared_ticket(app)
    before = snapshot(app, ticket_id)
    real_get_db = get_db

    def short_timeout_connection():
        connection = real_get_db()
        connection.execute("PRAGMA busy_timeout=30")
        return connection

    monkeypatch.setattr("app.services.get_db", short_timeout_connection)
    lock = connect_database(app.config["DATABASE"])
    try:
        lock.execute("BEGIN IMMEDIATE")
        assert post_action(client, ticket_id, "accept").status_code == 503
    finally:
        lock.rollback()
        lock.close()
    assert snapshot(app, ticket_id) == before
