from __future__ import annotations

import html
import json
import re

import pytest

from app.db import connect_database, get_db
from tests.conftest import login
from tests.test_tickets import create_via_http
from tests.test_workflow import prepared_ticket, post_action


def statistics(response):
    assert response.status_code == 200, response.text
    match = re.search(r'<script type="application/json" id="ticket-statistics">(.*?)</script>', response.text, re.S)
    assert match
    data = json.loads(match.group(1))
    assert data["total"] == sum(data["by_category"].values()) == sum(data["by_status"].values())
    return data


def ids(response):
    return [int(value) for value in re.findall(r"<td>#(\d+)</td>", response.text)]


@pytest.fixture()
def dataset(app):
    # Eight rows chosen before implementation; no query function determines expectations.
    rows = [
        ("student_a", "照明", "PENDING", None),
        ("student_a", "照明", "ACCEPTED", "repairer_a"),
        ("student_a", "网络", "IN_PROGRESS", "repairer_b"),
        ("student_a", "网络", "COMPLETED", "repairer_a"),
        ("student_a", "其他", "PENDING", None),
        ("student_b", "照明", "PENDING", None),
        ("student_b", "门锁", "ACCEPTED", "repairer_b"),
        ("student_b", "水管", "COMPLETED", "repairer_a"),
    ]
    result = []
    for owner, category, status, assignee in rows:
        ticket_id = prepared_ticket(app, status)
        with app.app_context():
            db = get_db()
            users = {r["username"]: r["id"] for r in db.execute("SELECT id,username FROM users")}
            db.execute("UPDATE repair_tickets SET student_id=?, category=?, assignee_id=? WHERE id=?",
                       (users[owner], category, users[assignee] if assignee else None, ticket_id))
            db.commit()
        result.append(ticket_id)
    return result


def test_student_and_repairer_scope_aggregates_are_private(app, dataset):
    cases = [
        ("student_a", "/tickets", [0,1,2,3,4], {"照明":2,"网络":2,"其他":1,"水管":0,"门锁":0}, {"PENDING":2,"ACCEPTED":1,"IN_PROGRESS":1,"COMPLETED":1}),
        ("student_b", "/tickets", [5,6,7], {"照明":1,"网络":0,"其他":0,"水管":1,"门锁":1}, {"PENDING":1,"ACCEPTED":1,"IN_PROGRESS":0,"COMPLETED":1}),
        ("repairer_a", "/work-queue", [0,1,3,4,5,7], {"照明":3,"网络":1,"其他":1,"水管":1,"门锁":0}, {"PENDING":3,"ACCEPTED":1,"IN_PROGRESS":0,"COMPLETED":2}),
        ("repairer_b", "/work-queue", [0,2,4,5,6], {"照明":2,"网络":1,"其他":1,"水管":0,"门锁":1}, {"PENDING":3,"ACCEPTED":1,"IN_PROGRESS":1,"COMPLETED":0}),
    ]
    for user, path, indexes, categories, statuses in cases:
        client = app.test_client()
        assert login(client, user).status_code == 303
        response = client.get(path)
        data = statistics(response)
        assert data["total"] == len(indexes)
        # User-approved extension: all eleven new categories are explicit zeros
        # in this legacy fixed dataset; the original five counts stay unchanged.
        extra_zeroes = dict.fromkeys(("本体类", "电类", "电梯类", "道路景观类", "给排水类", "空调类", "开水饮水类", "门窗五金类", "暖气类", "洗浴热水类", "消防设施类"), 0)
        assert data["by_category"] == {**categories, **extra_zeroes}
        assert data["by_status"] == statuses
        assert set(ids(response)) == {dataset[i] for i in indexes}
        assert statistics(client.get("/dashboard")) == data


def test_single_combined_clear_and_zero_filters(app, dataset):
    client = app.test_client()
    assert login(client).status_code == 303
    for params, expected in (
        ({"category":"照明"}, [0,1]),
        ({"status":"COMPLETED"}, [3]),
        ({"category":"照明","status":"ACCEPTED"}, [1]),
        ({"category":"门锁","status":"PENDING"}, []),
        ({"category":"","status":""}, [0,1,2,3,4]),
    ):
        response = client.get("/tickets", query_string=params)
        data = statistics(response)
        assert set(ids(response)) == {dataset[i] for i in expected}
        assert data["total"] == len(expected)
        if not expected:
            assert set(data["by_category"].values()) == {0}
            assert set(data["by_status"].values()) == {0}
            assert "暂无匹配工单" in response.text
            assert '<canvas' not in response.text

    repairer = app.test_client()
    assert login(repairer, "repairer_b").status_code == 303
    # OR authorization clause must be enclosed before AND category/status.
    response = repairer.get("/work-queue?category=水管&status=COMPLETED")
    assert statistics(response)["total"] == 0
    assert ids(response) == []


@pytest.mark.parametrize("path,user", [("/tickets","student_a"),("/work-queue","repairer_a"),("/dashboard","student_a")])
def test_invalid_query_parameters_are_400(app, path, user):
    client = app.test_client()
    assert login(client, user).status_code == 303
    for params in (
        {"category":"电梯"}, {"status":"CONFIRMED"}, {"category":"' OR 1=1 --"},
        {"status":"<script>alert(1)</script>"}, {"page":"-1"}, {"page":"0"},
        {"page":"1.5"}, {"page":"abc"}, {"page":""}, {"page":"９"},
        {"page":"9"*5000}, {"page":"999999999999999999"},
        {"student_id":"1"}, {"category":["照明","网络"]},
        {"status":["PENDING","COMPLETED"]}, {"page":["1","2"]},
    ):
        response = client.get(path, query_string=params)
        assert response.status_code == 400, (path, params)
        assert "筛选条件不正确" in response.text


def test_pagination_keeps_filters_but_not_statistical_limit(app):
    for _ in range(25):
        prepared_ticket(app)
    client = app.test_client()
    assert login(client).status_code == 303
    one = client.get("/tickets?category=照明&status=PENDING")
    two = client.get("/tickets?category=照明&status=PENDING&page=2")
    data = statistics(one)
    assert data["total"] == 25 and data["by_category"]["照明"] == 25
    assert data["by_status"]["PENDING"] == 25
    assert statistics(two) == data
    assert len(ids(one)) == 20 and len(ids(two)) == 5
    assert not set(ids(one)) & set(ids(two))
    assert len(set(ids(one) + ids(two))) == 25
    links = re.findall(r'href="([^"]+)">下一页', html.unescape(one.text))
    assert links and "category=" in links[0] and "status=PENDING" in links[0] and "page=2" in links[0]
    form = re.search(r'<form class="filter-bar".*?</form>', two.text, re.S).group()
    assert 'name="page"' not in form  # Applying a different filter resets page 1.
    beyond = client.get("/tickets?category=照明&status=PENDING&page=99")
    assert statistics(beyond)["total"] == 25 and ids(beyond) == []
    assert "category=" in html.unescape(beyond.text)


def test_creation_workflow_and_confirmation_update_correct_statistics(app):
    student, repairer, other = [app.test_client() for _ in range(3)]
    for client, user in ((student,"student_a"),(repairer,"repairer_a"),(other,"repairer_b")):
        assert login(client,user).status_code == 303
    assert statistics(student.get("/tickets"))["total"] == 0
    response = create_via_http(student, category="网络")
    assert response.status_code == 303
    ticket_id = int(response.headers["Location"].rsplit("/",1)[1])
    assert statistics(student.get("/tickets"))["by_category"]["网络"] == 1
    assert statistics(other.get("/work-queue"))["total"] == 1
    for action, expected in (
        ("accept", {"PENDING":0,"ACCEPTED":1,"IN_PROGRESS":0,"COMPLETED":0}),
        ("start", {"PENDING":0,"ACCEPTED":0,"IN_PROGRESS":1,"COMPLETED":0}),
        ("complete", {"PENDING":0,"ACCEPTED":0,"IN_PROGRESS":0,"COMPLETED":1}),
    ):
        assert post_action(repairer,ticket_id,action).status_code == 303
        assert statistics(student.get("/tickets"))["by_status"] == expected
        assert statistics(repairer.get("/work-queue"))["by_status"] == expected
        assert statistics(other.get("/work-queue"))["total"] == 0
    before = statistics(student.get("/tickets"))
    assert post_action(student,ticket_id,"confirm").status_code == 303
    assert statistics(student.get("/tickets")) == before
    assert post_action(student,ticket_id,"review",rating="5").status_code == 303
    assert statistics(student.get("/tickets")) == before


def test_read_snapshot_survives_concurrent_commit(app, dataset, monkeypatch):
    # WAL only for this isolated test permits a writer to commit during the read.
    # Production remains on the approved default journal mode.
    with app.app_context():
        get_db().execute("PRAGMA journal_mode=WAL")
    mutated = []
    real_get_db = get_db

    def trace(sql):
        if sql.startswith("SELECT id, building") and not mutated:
            writer = connect_database(app.config["DATABASE"])
            try:
                writer.execute("UPDATE repair_tickets SET category='门锁' WHERE id=?", (dataset[0],))
                writer.commit()
                mutated.append(True)
            finally:
                writer.close()

    def traced_db():
        db = real_get_db()
        db.set_trace_callback(trace)
        return db

    monkeypatch.setattr("app.queries.get_db", traced_db)
    client = app.test_client()
    assert login(client).status_code == 303
    first = statistics(client.get("/tickets?category=照明"))
    assert mutated == [True]
    assert first["total"] == first["by_category"]["照明"] == 2
    second = statistics(client.get("/tickets?category=照明"))
    assert second["total"] == second["by_category"]["照明"] == 1


def test_dashboard_auth_static_assets_and_zero_state(app):
    client = app.test_client()
    assert client.get("/dashboard").status_code == 302
    assert login(client).status_code == 303
    response = client.get("/dashboard")
    assert statistics(response)["total"] == 0
    assert "暂无匹配工单" in response.text
    assert '/static/vendor/chart.umd.min.js' in response.text
    assert 'https://cdn' not in response.text
    for path in ("/static/vendor/chart.umd.min.js", "/static/vendor/Chart.js-LICENSE.md", "/static/js/charts.js"):
        assert client.get(path).status_code == 200
