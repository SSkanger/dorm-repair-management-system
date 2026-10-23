from __future__ import annotations

from werkzeug.security import check_password_hash

from app import create_app
from app.db import get_db, init_database, utc_now


def test_seed_demo_is_idempotent_and_preserves_existing_data(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "cli-test",
            "DATABASE": str(tmp_path / "cli.sqlite3"),
            "SESSION_DIR": str(tmp_path / "sessions"),
        }
    )
    with app.app_context():
        init_database()

    runner = app.test_cli_runner()
    first = runner.invoke(args=["seed-demo", "--password", "FirstPass123!"])
    assert first.exit_code == 0, first.output

    with app.app_context():
        db = get_db()
        hashes = {
            row["username"]: row["password_hash"]
            for row in db.execute("SELECT username,password_hash FROM users")
        }
        student = db.execute("SELECT id FROM users WHERE username='student_a'").fetchone()[0]
        now = utc_now()
        db.execute(
            "INSERT INTO repair_tickets "
            "(student_id,building,room_number,category,description,status,created_at,updated_at,submission_token) "
            "VALUES (?,?,?,?,?,'PENDING',?,?,?)",
            (student, "3号楼", "406", "网络", "测试数据保持，不由种子删除。", now, now, "keep-ticket"),
        )
        db.commit()

    second = runner.invoke(args=["seed-demo", "--password", "SecondPass123!"])
    assert second.exit_code == 0, second.output
    init_again = runner.invoke(args=["init-db"])
    assert init_again.exit_code == 0
    assert "未修改现有数据" in init_again.output

    with app.app_context():
        db = get_db()
        current = {
            row["username"]: row["password_hash"]
            for row in db.execute("SELECT username,password_hash FROM users")
        }
        assert current == hashes
        assert check_password_hash(current["student_a"], "FirstPass123!")
        assert not check_password_hash(current["student_a"], "SecondPass123!")
        assert db.execute("SELECT COUNT(*) FROM repair_tickets").fetchone()[0] == 1


def test_seed_rejects_short_password_without_users(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "short-password",
            "DATABASE": str(tmp_path / "short.sqlite3"),
            "SESSION_DIR": str(tmp_path / "sessions"),
        }
    )
    with app.app_context():
        init_database()
    result = app.test_cli_runner().invoke(args=["seed-demo", "--password", "short"])
    assert result.exit_code != 0
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
