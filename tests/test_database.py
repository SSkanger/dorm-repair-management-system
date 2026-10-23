from __future__ import annotations

import sqlite3

from app import create_app
from app.db import connect_database, get_db, init_database, utc_now


def _ticket_values(student_id, **overrides):
    now = utc_now()
    values = {
        "student_id": student_id,
        "assignee_id": None,
        "building": "3号楼",
        "room_number": "406",
        "category": "照明",
        "description": "宿舍灯具无法正常照明。",
        "status": "PENDING",
        "created_at": now,
        "updated_at": now,
        "assigned_at": None,
        "started_at": None,
        "completed_at": None,
        "confirmed_at": None,
        "rating": None,
        "review_text": None,
        "reviewed_at": None,
        "submission_token": "token-1",
    }
    values.update(overrides)
    return values


def _insert_ticket(db, values):
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    db.execute(
        f"INSERT INTO repair_tickets ({columns}) VALUES ({placeholders})",
        tuple(values.values()),
    )


def test_foreign_keys_checks_and_unique_constraints(app):
    with app.app_context():
        db = get_db()
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        student = db.execute(
            "SELECT id FROM users WHERE username='student_a'"
        ).fetchone()[0]

        invalid_cases = [
            _ticket_values(999999, submission_token="fk"),
            _ticket_values(student, category="未知", submission_token="category"),
            _ticket_values(student, status="BROKEN", submission_token="status"),
            _ticket_values(
                student,
                status="ACCEPTED",
                assignee_id=None,
                assigned_at=None,
                submission_token="cross-field",
            ),
            _ticket_values(
                student,
                rating=1.5,
                submission_token="rating-type",
            ),
        ]
        for values in invalid_cases:
            with __import__("pytest").raises(sqlite3.IntegrityError):
                _insert_ticket(db, values)
            db.rollback()

        _insert_ticket(db, _ticket_values(student))
        db.commit()
        with __import__("pytest").raises(sqlite3.IntegrityError):
            _insert_ticket(db, _ticket_values(student))
        db.rollback()

        with __import__("pytest").raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO users (username,password_hash,display_name,role,created_at) "
                "SELECT username,password_hash,display_name,role,created_at FROM users WHERE username='student_a'"
            )
        db.rollback()


def test_init_is_non_destructive_and_reconnect_persists(app):
    database_path = app.config["DATABASE"]
    with app.app_context():
        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username='student_a'"
        ).fetchone()[0]
        _insert_ticket(db, _ticket_values(student, submission_token="persistent"))
        db.commit()
        assert "未修改现有数据" in init_database()

    reopened = connect_database(database_path)
    try:
        assert reopened.execute(
            "SELECT COUNT(*) FROM repair_tickets WHERE submission_token='persistent'"
        ).fetchone()[0] == 1
    finally:
        reopened.close()


def test_incompatible_database_is_refused_without_deletion(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE legacy_data (value TEXT)")
    connection.execute("INSERT INTO legacy_data VALUES ('keep-me')")
    connection.commit()
    connection.close()

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "legacy-test",
            "DATABASE": str(path),
            "SESSION_DIR": str(tmp_path / "sessions"),
        }
    )
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code != 0
    assert "拒绝初始化不兼容数据库" in result.output

    reopened = sqlite3.connect(path)
    try:
        assert reopened.execute("SELECT value FROM legacy_data").fetchone()[0] == "keep-me"
    finally:
        reopened.close()


def test_test_databases_are_isolated(tmp_path):
    paths = [tmp_path / "one.sqlite3", tmp_path / "two.sqlite3"]
    apps = []
    for index, path in enumerate(paths):
        app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": f"isolation-{index}",
                "DATABASE": str(path),
                "SESSION_DIR": str(tmp_path / f"sessions-{index}"),
            }
        )
        with app.app_context():
            init_database()
        apps.append(app)

    with apps[0].app_context():
        get_db().execute(
            "INSERT INTO users (username,password_hash,display_name,role,created_at) VALUES (?,?,?,?,?)",
            ("only_one", "x" * 21, "仅库一", "student", utc_now()),
        )
        get_db().commit()
    with apps[1].app_context():
        assert get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_test_app_uses_only_configured_storage(tmp_path):
    isolated_database = tmp_path / "isolated.sqlite3"
    isolated_sessions = tmp_path / "isolated-sessions"
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "fully-isolated-test",
            "DATABASE": str(isolated_database),
            "SESSION_DIR": str(isolated_sessions),
        }
    )
    with app.app_context():
        init_database()
    assert isolated_database.exists()
    assert isolated_sessions.exists()
    assert app.config["DATABASE"] == str(isolated_database)
    assert app.config["SESSION_DIR"] == str(isolated_sessions)

