from __future__ import annotations

import re

import pytest

from app import create_app
from app.db import get_db, init_database, utc_now
from app.services import TicketStorageError
from tests.conftest import extract_csrf, login, seed_users


TOKEN_PATTERN = re.compile(r'name="submission_token"[^>]*value="([^"]+)"')


def new_form(client):
    response = client.get("/tickets/new")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    match = TOKEN_PATTERN.search(html)
    assert match, "new-ticket form did not contain a submission token"
    return extract_csrf(response), match.group(1)


def valid_payload(csrf_token: str, submission_token: str, **overrides):
    payload = {
        "csrf_token": csrf_token,
        "submission_token": submission_token,
        "building": "3号楼",
        "room_number": "406",
        "category": "照明",
        "description": "宿舍天花板照明灯不亮。",
    }
    payload.update(overrides)
    return payload


def create_via_http(client, **overrides):
    csrf_token, submission_token = new_form(client)
    return client.post(
        "/tickets/new",
        data=valid_payload(csrf_token, submission_token, **overrides),
        follow_redirects=False,
    )


def user_id(db, username: str) -> int:
    return db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0]


def insert_ticket(db, student_id: int, sequence: int, *, token_prefix="page") -> int:
    now = f"2026-10-23T00:00:{sequence:02d}.000000Z"
    cursor = db.execute(
        "INSERT INTO repair_tickets "
        "(student_id, building, room_number, category, description, status, "
        "created_at, updated_at, submission_token) "
        "VALUES (?, ?, ?, '网络', ?, 'PENDING', ?, ?, ?)",
        (
            student_id,
            "5号楼",
            str(100 + sequence),
            f"分页测试故障描述 {sequence}",
            now,
            now,
            f"{token_prefix}-{sequence}",
        ),
    )
    return cursor.lastrowid


def test_student_creates_normalized_pending_ticket(app, client):
    assert login(client, "student_a").status_code == 303
    response = create_via_http(
        client,
        building=" 3号楼 ",
        room_number=" 406 ",
        description="  宿舍天花板照明灯不亮。  ",
        student_id="999999",
        status="COMPLETED",
        assignee_id="999999",
    )
    # Unexpected trusted fields are rejected instead of silently accepting tampering.
    assert response.status_code == 400

    response = create_via_http(
        client,
        building=" 3号楼 ",
        room_number=" 406 ",
        description="  宿舍天花板照明灯不亮。  ",
    )
    assert response.status_code == 303
    assert re.search(r"/tickets/\d+$", response.headers["Location"])

    with app.app_context():
        row = get_db().execute("SELECT * FROM repair_tickets").fetchone()
        student = user_id(get_db(), "student_a")
        assert row["student_id"] == student
        assert row["building"] == "3号楼"
        assert row["room_number"] == "406"
        assert row["description"] == "宿舍天花板照明灯不亮。"
        assert row["status"] == "PENDING"
        assert row["assignee_id"] is None
        assert row["assigned_at"] is None
        assert row["started_at"] is None
        assert row["completed_at"] is None
        assert row["created_at"] == row["updated_at"]

    detail = client.get(response.headers["Location"])
    assert detail.status_code == 200
    assert "宿舍天花板照明灯不亮。" in detail.get_data(as_text=True)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("building", "", "请填写楼栋"),
        ("building", "   ", "请填写楼栋"),
        ("building", "楼" * 31, "最多 30"),
        ("room_number", "", "请填写宿舍号"),
        ("room_number", "   ", "请填写宿舍号"),
        ("room_number", "房" * 21, "最多 20"),
        ("description", "", "请填写故障描述"),
        ("description", "　　", "请填写故障描述"),
        ("description", "四字符啊", "5–1000"),
        ("description", "长" * 1001, "5–1000"),
        ("category", "电梯", "有效的故障类型"),
    ],
)
def test_invalid_ticket_fields_are_rejected(app, client, field, value, message):
    assert login(client).status_code == 303
    response = create_via_http(client, **{field: value})
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM repair_tickets").fetchone()[0] == 0


@pytest.mark.parametrize("length", [5, 1000])
def test_description_boundary_values_are_accepted(app, client, length):
    assert login(client).status_code == 303
    response = create_via_http(client, description="修" * length)
    assert response.status_code == 303
    with app.app_context():
        assert get_db().execute("SELECT length(description) FROM repair_tickets").fetchone()[0] == length


def test_invalid_form_does_not_consume_submission_token(app, client):
    assert login(client).status_code == 303
    csrf_token, submission_token = new_form(client)
    invalid = valid_payload(csrf_token, submission_token, description="短")
    response = client.post("/tickets/new", data=invalid)
    assert response.status_code == 400

    valid = valid_payload(csrf_token, submission_token)
    response = client.post("/tickets/new", data=valid)
    assert response.status_code == 303
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM repair_tickets").fetchone()[0] == 1


def test_missing_or_unknown_business_submission_token_is_rejected(app, client):
    assert login(client).status_code == 303
    csrf_token, _submission_token = new_form(client)
    for token in ("", "not-issued-by-this-session"):
        response = client.post(
            "/tickets/new", data=valid_payload(csrf_token, token)
        )
        assert response.status_code == 400
        assert "提交标识" in response.get_data(as_text=True)
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM repair_tickets").fetchone()[0] == 0


def test_csrf_authentication_and_role_rules_for_creation(app):
    anonymous = app.test_client()
    assert anonymous.post("/tickets/new").status_code == 400
    anonymous_csrf = extract_csrf(anonymous.get("/login"))
    assert anonymous.post("/tickets/new", data={"csrf_token": anonymous_csrf}).status_code == 401

    repairer = app.test_client()
    assert login(repairer, "repairer_a").status_code == 303
    assert repairer.get("/tickets/new").status_code == 403
    valid_csrf = extract_csrf(repairer.get("/portal"))
    assert repairer.post("/tickets/new", data={"csrf_token": valid_csrf}).status_code == 403
    assert repairer.post("/tickets/new", data={"csrf_token": "bad"}).status_code == 400

    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM repair_tickets").fetchone()[0] == 0


def test_submission_token_exact_replay_is_idempotent_and_changed_content_conflicts(app, client):
    assert login(client).status_code == 303
    csrf_token, submission_token = new_form(client)
    payload = valid_payload(csrf_token, submission_token)

    first = client.post("/tickets/new", data=payload)
    replay = client.post("/tickets/new", data=payload)
    assert first.status_code == replay.status_code == 303
    assert first.headers["Location"] == replay.headers["Location"]

    changed = dict(payload, description="同一标识下被修改的故障描述。")
    conflict = client.post("/tickets/new", data=changed)
    assert conflict.status_code == 409
    assert "已经用于另一份报修内容" in conflict.get_data(as_text=True)
    with app.app_context():
        rows = get_db().execute("SELECT description FROM repair_tickets").fetchall()
        assert [row["description"] for row in rows] == [payload["description"]]


def test_new_token_allows_similar_second_ticket(app, client):
    assert login(client).status_code == 303
    assert create_via_http(client).status_code == 303
    assert create_via_http(client).status_code == 303
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM repair_tickets").fetchone()[0] == 2


def test_student_list_and_detail_are_private_and_match_database(app):
    student_a = app.test_client()
    student_b = app.test_client()
    assert login(student_a, "student_a").status_code == 303
    created = create_via_http(student_a, category="水管", description="洗手池下方水管持续漏水。")
    ticket_url = created.headers["Location"]

    own_list = student_a.get("/tickets")
    assert own_list.status_code == 200
    html = own_list.get_data(as_text=True)
    assert "水管" in html and "3号楼" in html and "待处理" in html
    assert student_a.get(ticket_url).status_code == 200

    assert login(student_b, "student_b").status_code == 303
    other_list = student_b.get("/tickets")
    assert other_list.status_code == 200
    assert "还没有报修记录" in other_list.get_data(as_text=True)
    assert student_b.get(ticket_url).status_code == 404
    assert student_b.get("/tickets/999999").status_code == 404


def test_xss_like_description_is_rendered_as_text(client):
    assert login(client).status_code == 303
    description = "<script>alert('x')</script> 故障"
    created = create_via_http(client, description=description)
    detail = client.get(created.headers["Location"])
    html = detail.get_data(as_text=True)
    assert "&lt;script&gt;" in html
    assert "<script>alert('x')</script>" not in html


def test_pagination_is_stable_without_missing_or_duplicate_rows(app, client):
    with app.app_context():
        db = get_db()
        student = user_id(db, "student_a")
        ids = [insert_ticket(db, student, index) for index in range(1, 42)]
        db.commit()

    assert login(client).status_code == 303
    pages = [client.get(f"/tickets?page={page}") for page in (1, 2, 3)]
    assert all(response.status_code == 200 for response in pages)
    found = []
    for response in pages:
        found.extend(int(value) for value in re.findall(r"<td>#(\d+)</td>", response.get_data(as_text=True)))
    assert len(found) == 41
    assert len(set(found)) == 41
    assert found == list(reversed(ids))

    beyond = client.get("/tickets?page=999")
    assert beyond.status_code == 200
    assert "本页没有工单" in beyond.get_data(as_text=True)
    assert "?page=3" in beyond.get_data(as_text=True)

    for url in (
        "/tickets?page=0",
        "/tickets?page=-1",
        "/tickets?page=x",
        "/tickets?page=999999999999999999999999999999999999",
        "/tickets?page=1&page=2",
        "/tickets?status=PENDING",
    ):
        assert client.get(url).status_code == 400

    assert client.get("/tickets/999999999999999999999999999999999999").status_code == 404


def test_repairer_read_only_scope_and_wrong_list_role(app):
    with app.app_context():
        db = get_db()
        student = user_id(db, "student_a")
        pending_id = insert_ticket(db, student, 1, token_prefix="scope")
        db.commit()

    repairer = app.test_client()
    assert login(repairer, "repairer_a").status_code == 303
    assert repairer.get("/tickets").status_code == 403
    queue = repairer.get("/work-queue")
    assert queue.status_code == 200
    assert f"#{pending_id}" in queue.get_data(as_text=True)
    assert repairer.get(f"/tickets/{pending_id}").status_code == 200
    assert repairer.post(f"/tickets/{pending_id}/accept").status_code in {400, 404, 405}

    student_client = app.test_client()
    assert login(student_client, "student_a").status_code == 303
    assert student_client.get("/work-queue").status_code == 403


def test_storage_error_is_friendly_and_does_not_create_partial_ticket(app, client, monkeypatch):
    assert login(client).status_code == 303
    csrf_token, submission_token = new_form(client)

    def fail_write(**_kwargs):
        raise TicketStorageError("报修暂时无法保存，请稍后重试。")

    monkeypatch.setattr("app.tickets.create_ticket", fail_write)
    response = client.post(
        "/tickets/new", data=valid_payload(csrf_token, submission_token)
    )
    assert response.status_code == 503
    assert "报修暂时无法保存" in response.get_data(as_text=True)
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM repair_tickets").fetchone()[0] == 0


def test_ticket_persists_across_database_close_and_new_application(tmp_path):
    database = tmp_path / "persistent.sqlite3"
    first = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "restart-one",
            "DATABASE": str(database),
            "SESSION_DIR": str(tmp_path / "sessions-one"),
        }
    )
    with first.app_context():
        init_database()
    seed_users(first)
    first_client = first.test_client()
    assert login(first_client).status_code == 303
    created = create_via_http(first_client, category="门锁", description="宿舍门锁转动困难无法正常上锁。")
    ticket_id = int(created.headers["Location"].rsplit("/", 1)[1])

    second = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "restart-two",
            "DATABASE": str(database),
            "SESSION_DIR": str(tmp_path / "sessions-two"),
        }
    )
    second_client = second.test_client()
    assert login(second_client).status_code == 303
    detail = second_client.get(f"/tickets/{ticket_id}")
    assert detail.status_code == 200
    assert "宿舍门锁转动困难无法正常上锁。" in detail.get_data(as_text=True)

