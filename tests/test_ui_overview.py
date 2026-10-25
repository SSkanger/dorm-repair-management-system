"""Fixed-data checks for the UI's new read-only summaries and owned-work view."""
import re

import pytest

from app.db import get_db
from tests.conftest import login
from tests.test_queries_stats import statistics, ids
from tests.test_workflow import prepared_ticket


@pytest.fixture()
def ui_rows(app):
    inputs = [
        ("student_a", "PENDING", None),
        ("student_a", "ACCEPTED", "repairer_a"),
        ("student_a", "IN_PROGRESS", "repairer_a"),
        ("student_a", "COMPLETED", "repairer_b"),
        ("student_b", "COMPLETED", "repairer_a"),
        ("student_b", "PENDING", None),
    ]
    result = []
    for student, state, repairer in inputs:
        ticket_id = prepared_ticket(app, state)
        with app.app_context():
            db = get_db()
            users = {r["username"]: r["id"] for r in db.execute("SELECT id,username FROM users")}
            db.execute("UPDATE repair_tickets SET student_id=?,assignee_id=? WHERE id=?",
                       (users[student], users[repairer] if repairer else None, ticket_id))
            db.commit()
        result.append(ticket_id)
    return result


@pytest.mark.parametrize("user,counts,visible", [
    ("student_a", [4, 1, 1, 1], [0, 1, 2, 3]),
    ("student_b", [2, 1, 0, 1], [4, 5]),
    ("repairer_a", [2, 1, 1, 1], [0, 1, 2, 4, 5]),
    ("repairer_b", [2, 0, 0, 1], [0, 3, 5]),
])
def test_overview_counts_and_recent_rows_use_authorized_data(app, ui_rows, user, counts, visible):
    with app.app_context():
        before = [tuple(r) for r in get_db().execute("SELECT * FROM repair_tickets ORDER BY id")]
    client = app.test_client()
    assert login(client, user).status_code == 303
    response = client.get("/portal")
    assert response.status_code == 200
    cards = re.findall(r'<article class="metric-card.*?</article>', response.text, re.S)
    assert [int(re.search(r'<strong>(\d+)</strong>', card).group(1)) for card in cards] == counts
    assert ids(response) == [ui_rows[i] for i in reversed(visible)][:5]
    for path in ("/student/portal",) if user.startswith("student") else ("/repairer/portal",):
        assert client.get(path).status_code == 200
    with app.app_context():
        assert [tuple(r) for r in get_db().execute("SELECT * FROM repair_tickets ORDER BY id")] == before


def test_my_work_intersects_owner_filters_and_keeps_pagination(app, ui_rows):
    for _ in range(22):
        prepared_ticket(app, "ACCEPTED")  # owner repairer_a
    client = app.test_client()
    assert login(client, "repairer_a").status_code == 303
    first = client.get("/my-work?category=照明&status=ACCEPTED")
    second = client.get("/my-work?category=照明&status=ACCEPTED&page=2")
    assert len(ids(first)) == 20 and len(ids(second)) == 3
    assert not set(ids(first)) & set(ids(second))
    assert statistics(first)["total"] == statistics(second)["total"] == 23
    all_owned = client.get("/my-work")
    assert statistics(all_owned)["by_status"] == {"PENDING":0,"ACCEPTED":23,"IN_PROGRESS":1,"COMPLETED":1}
    assert ui_rows[0] not in ids(all_owned) and ui_rows[3] not in ids(all_owned)
    other = app.test_client()
    assert login(other, "repairer_b").status_code == 303
    response = other.get("/my-work")
    assert ids(response) == [ui_rows[3]]
    assert statistics(response)["total"] == 1


def test_owned_view_is_read_only_and_has_role_and_parameter_guards(app, client):
    assert client.get("/my-work").status_code == 302
    assert login(client).status_code == 303
    assert client.get("/my-work").status_code == 403
    repairer = app.test_client()
    assert login(repairer, "repairer_a").status_code == 303
    assert repairer.get("/my-work?assignee_id=2").status_code == 400
    assert repairer.get("/my-work?status=CONFIRMED").status_code == 400
    # No POST route exists: Flask has no matching endpoint and returns 405.
    # Existing business POST CSRF priority remains covered by auth/workflow tests.
    assert repairer.post("/my-work").status_code == 405


def test_timeline_only_marks_persisted_nodes_done(app, client):
    ticket_id = prepared_ticket(app)
    assert login(client).status_code == 303
    response = client.get(f"/tickets/{ticket_id}")
    timeline = re.search(r'<ol class="timeline">(.*?)</ol>', response.text, re.S).group(1)
    assert timeline.count('<li class="done">') == 1
    assert timeline.count('尚未发生') == 5
    assert '确认完成</button>' not in response.text


def test_ui_assets_and_session_form_fields_remain_local(client):
    assert login(client).status_code == 303
    for path in ("/portal", "/tickets/new", "/tickets", "/dashboard"):
        response = client.get(path)
        assert response.status_code == 200
        assert 'name="csrf_token"' in response.text
        assert '/static/js/ui.js' in response.text
        assert 'https://cdn' not in response.text
    new = client.get("/tickets/new")
    assert 'name="submission_token"' in new.text
    assert client.get("/static/js/ui.js").status_code == 200
