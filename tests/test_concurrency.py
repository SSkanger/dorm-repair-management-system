from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

import pytest

from app.db import get_db
from tests.conftest import extract_csrf, login
from tests.test_workflow import prepared_ticket, snapshot


@pytest.mark.parametrize("action", ["accept", "confirm", "review"])
def test_concurrent_actions_use_same_file_independent_connections(app, monkeypatch, action):
    ticket_id = prepared_ticket(
        app, "PENDING" if action == "accept" else "COMPLETED", confirmed=action == "review"
    )
    names = ("repairer_a", "repairer_b") if action == "accept" else ("student_a", "student_a")
    clients = [app.test_client(), app.test_client()]
    tokens = []
    for client, name in zip(clients, names):
        assert login(client, name).status_code == 303
        tokens.append(extract_csrf(client.get("/portal")))
    barrier = Barrier(2, timeout=10)
    connection_ids = set()
    guard = Lock()
    real_get_db = get_db

    def simultaneous_connections():
        db = real_get_db()
        with guard:
            connection_ids.add(id(db))
        barrier.wait()
        return db

    monkeypatch.setattr("app.services.get_db", simultaneous_connections)

    def send(index):
        data = {"csrf_token": tokens[index]}
        if action == "review":
            data.update(rating="1" if index == 0 else "5", review_text=f"winner-{index}")
        response = clients[index].post(f"/tickets/{ticket_id}/{action}", data=data)
        return response.status_code

    before = snapshot(app, ticket_id)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(send, [0, 1]))
    assert len(connection_ids) == 2
    assert sorted(results) == ([303, 404] if action == "accept" else [303, 409])
    winner = results.index(303)
    after = snapshot(app, ticket_id)
    if action == "accept":
        with app.app_context():
            winner_id = get_db().execute("SELECT id FROM users WHERE username=?", (names[winner],)).fetchone()[0]
        assert after["status"] == "ACCEPTED" and after["assignee_id"] == winner_id
        assert after["assigned_at"] == after["updated_at"]
        assert after["started_at"] is after["completed_at"] is None
        changed = {"status", "assignee_id", "assigned_at", "updated_at"}
    elif action == "confirm":
        assert after["status"] == "COMPLETED"
        assert after["confirmed_at"] == after["updated_at"]
        changed = {"confirmed_at", "updated_at"}
    else:
        assert after["rating"] == (1 if winner == 0 else 5)
        assert after["review_text"] == f"winner-{winner}"
        assert after["reviewed_at"] == after["updated_at"]
        changed = {"rating", "review_text", "reviewed_at", "updated_at"}
    assert {k: v for k, v in after.items() if k not in changed} == {
        k: v for k, v in before.items() if k not in changed
    }
