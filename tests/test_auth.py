from __future__ import annotations

from pathlib import Path

from werkzeug.security import check_password_hash

from app.auth import role_required
from app.db import get_db
from tests.conftest import extract_csrf, login


def test_students_and_repairers_can_login_with_correct_roles(app, client):
    response = login(client, "student_a")
    assert response.status_code == 303
    portal = client.get("/portal")
    assert portal.status_code == 200
    assert "学生入口" in portal.get_data(as_text=True)

    token = extract_csrf(portal)
    assert client.post("/logout", data={"csrf_token": token}).status_code == 303

    response = login(client, "repairer_a")
    assert response.status_code == 303
    portal = client.get("/portal")
    assert "维修人员入口" in portal.get_data(as_text=True)


def test_wrong_password_is_rejected(client):
    response = login(client, "student_a", "wrong-password")
    assert response.status_code == 400
    assert "用户名或密码不正确" in response.get_data(as_text=True)
    assert client.get("/portal").status_code == 302


def test_passwords_are_hashes(app):
    with app.app_context():
        row = get_db().execute(
            "SELECT password_hash FROM users WHERE username = ?", ("student_a",)
        ).fetchone()
        assert row["password_hash"] != "DemoPass123!"
        assert check_password_hash(row["password_hash"], "DemoPass123!")


def test_protected_routes_and_wrong_role(client):
    response = client.get("/student/portal")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    assert login(client, "student_a").status_code == 303
    assert client.get("/student/portal").status_code == 200
    assert client.get("/repairer/portal").status_code == 403


def test_csrf_authentication_and_role_error_priority(app, client):
    @app.post("/_test/repairer-only")
    @role_required("repairer")
    def repairer_only_probe():
        return "ok", 200

    # CSRF runs first, even when the request is unauthenticated.
    assert client.post("/_test/repairer-only").status_code == 400

    anonymous_token = extract_csrf(client.get("/login"))
    unauthenticated = client.post(
        "/_test/repairer-only", data={"csrf_token": anonymous_token}
    )
    assert unauthenticated.status_code == 401

    assert login(client, "student_a").status_code == 303
    portal = client.get("/portal")
    valid_token = extract_csrf(portal)
    wrong_role = client.post(
        "/_test/repairer-only", data={"csrf_token": valid_token}
    )
    assert wrong_role.status_code == 403

    invalid_token = client.post(
        "/_test/repairer-only", data={"csrf_token": "not-a-valid-token"}
    )
    assert invalid_token.status_code == 400


def test_login_rotates_session_id_and_old_id_cannot_authenticate(app):
    client = app.test_client()
    login_page = client.get("/login")
    token = extract_csrf(login_page)
    cookie_name = app.config["SESSION_COOKIE_NAME"]
    old_sid = client.get_cookie(cookie_name).value

    response = client.post(
        "/login",
        data={"username": "student_a", "password": "DemoPass123!", "csrf_token": token},
    )
    assert response.status_code == 303
    authenticated_sid = client.get_cookie(cookie_name).value
    assert authenticated_sid != old_sid
    assert "student_a" not in authenticated_sid

    replay = app.test_client()
    replay.set_cookie(cookie_name, old_sid)
    assert replay.get("/portal").status_code == 302


def test_logout_invalidates_authenticated_session(app):
    client = app.test_client()
    assert login(client).status_code == 303
    cookie_name = app.config["SESSION_COOKIE_NAME"]
    authenticated_sid = client.get_cookie(cookie_name).value
    token = extract_csrf(client.get("/portal"))
    assert client.post("/logout", data={"csrf_token": token}).status_code == 303
    assert client.get("/portal").status_code == 302

    replay = app.test_client()
    replay.set_cookie(cookie_name, authenticated_sid)
    assert replay.get("/portal").status_code == 302


def test_session_data_is_stored_server_side(app, client):
    assert login(client).status_code == 303
    cookie = client.get_cookie(app.config["SESSION_COOKIE_NAME"])
    assert cookie is not None
    assert "student_a" not in cookie.value
    assert "user_id" not in cookie.value
    session_files = list(Path(app.config["SESSION_DIR"]).iterdir())
    assert session_files

