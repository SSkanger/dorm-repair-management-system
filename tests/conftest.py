from __future__ import annotations

import re

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import DEMO_USERS, init_database, utc_now


CSRF_PATTERN = re.compile(r'name="csrf_token"[^>]*value="([^"]+)"')


def extract_csrf(response) -> str:
    match = CSRF_PATTERN.search(response.get_data(as_text=True))
    assert match, "response did not contain a CSRF token"
    return match.group(1)


def seed_users(app, password="DemoPass123!") -> None:
    with app.app_context():
        from app.db import get_db

        db = get_db()
        for username, display_name, role in DEMO_USERS:
            db.execute(
                "INSERT INTO users (username, password_hash, display_name, role, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, generate_password_hash(password), display_name, role, utc_now()),
            )
        db.commit()


def login(client, username="student_a", password="DemoPass123!"):
    token = extract_csrf(client.get("/login"))
    return client.post(
        "/login",
        data={"username": username, "password": password, "csrf_token": token},
        follow_redirects=False,
    )


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-only",
            "DATABASE": str(tmp_path / "test.sqlite3"),
            "SESSION_DIR": str(tmp_path / "sessions"),
            "SESSION_COOKIE_SECURE": False,
        }
    )
    with application.app_context():
        init_database()
    seed_users(application)
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()

