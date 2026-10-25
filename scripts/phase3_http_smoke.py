"""Run the full workflow and a real process restart in isolated temporary storage."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time

import requests

# Running this script directly places scripts/ first on the import path.
from phase2_http_smoke import CSRF, SUBMISSION, hidden, login

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.db import connect_database, init_database


def main(*, verify_statistics=False):
    with tempfile.TemporaryDirectory(prefix="dorm-phase3-") as directory:
        storage = Path(directory)
        database = storage / "verification.sqlite3"
        password = secrets.token_urlsafe(18)
        environment = dict(os.environ)
        environment.update(
            DORM_REPAIR_DATABASE=str(database),
            DORM_REPAIR_SESSION_DIR=str(storage / "sessions"),
            DORM_REPAIR_SECRET_KEY=secrets.token_hex(32),
            DORM_REPAIR_COOKIE_SECURE="0",
            PYTHONIOENCODING="utf-8",
        )
        app = create_app({
            "DATABASE": str(database), "SESSION_DIR": str(storage / "setup-sessions"),
            "SECRET_KEY": secrets.token_hex(32),
        })
        with app.app_context():
            init_database()
        result = app.test_cli_runner().invoke(args=["seed-demo", "--password", password])
        assert result.exit_code == 0, result.output

        with socket.socket() as candidate:
            candidate.bind(("127.0.0.1", 0))
            port = candidate.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        process = None
        log = (storage / "http.log").open("w", encoding="utf-8")

        def start():
            server = subprocess.Popen(
                [sys.executable, "-m", "flask", "--app", "run:app", "run", "--host", "127.0.0.1", "--port", str(port), "--no-reload"],
                cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError("Flask process exited before becoming healthy")
                try:
                    if requests.get(f"{base}/health", timeout=.3).status_code == 200:
                        return server
                except requests.RequestException:
                    pass
                time.sleep(.1)
            server.terminate()
            server.wait(timeout=10)
            raise RuntimeError("Flask health readiness timeout")

        def stop(server):
            server.terminate()
            server.wait(timeout=10)

        def row(ticket_id):
            db = connect_database(str(database))
            try:
                return dict(db.execute("SELECT * FROM repair_tickets WHERE id=?", (ticket_id,)).fetchone())
            finally:
                db.close()

        def action(session, ticket_id, name, expected=303, **values):
            portal = session.get(f"{base}/portal", timeout=5)
            response = session.post(
                f"{base}/tickets/{ticket_id}/{name}",
                data={"csrf_token": hidden(CSRF, portal.text, "CSRF"), **values},
                allow_redirects=False, timeout=10,
            )
            assert response.status_code == expected, (name, response.status_code, response.text)

        def reject_without_changes(session, ticket_id, name, code, **values):
            before = row(ticket_id)
            action(session, ticket_id, name, expected=code, **values)
            assert row(ticket_id) == before

        def read_statistics(session, path="/dashboard", params=None):
            response = session.get(f"{base}{path}", params=params, timeout=5)
            assert response.status_code == 200
            match = re.search(r'id="ticket-statistics">(.*?)</script>', response.text, re.S)
            assert match
            data = json.loads(match.group(1))
            assert data["total"] == sum(data["by_category"].values()) == sum(data["by_status"].values())
            return data

        try:
            process = start()
            first_pid = process.pid
            sessions = {name: requests.Session() for name in ("student_a", "student_b", "repairer_a", "repairer_b")}
            for name, session in sessions.items():
                login(session, base, name, password)
            student = sessions["student_a"]
            form = student.get(f"{base}/tickets/new", timeout=5)
            created = student.post(
                f"{base}/tickets/new", data={
                    "csrf_token": hidden(CSRF, form.text, "CSRF"),
                    "submission_token": hidden(SUBMISSION, form.text, "submission"),
                    "building": "3号楼", "room_number": "406", "category": "照明",
                    "description": "真实 HTTP 闭环验证，宿舍灯具无法照明。",
                }, allow_redirects=False, timeout=5,
            )
            assert created.status_code == 303
            ticket_id = int(created.headers["Location"].rsplit("/", 1)[1])
            if verify_statistics:
                form = student.get(f"{base}/tickets/new", timeout=5)
                second = student.post(f"{base}/tickets/new", data={
                    "csrf_token": hidden(CSRF, form.text, "CSRF"),
                    "submission_token": hidden(SUBMISSION, form.text, "submission"),
                    "building": "3号楼", "room_number": "406", "category": "网络",
                    "description": "真实 HTTP 统计验证，网络端口无法连接。",
                }, allow_redirects=False, timeout=5)
                assert second.status_code == 303
                initial = read_statistics(student, "/tickets")
                assert initial["total"] == initial["by_status"]["PENDING"] == 2
                assert initial["by_category"] == {"照明":1,"网络":1,"水管":0,"门锁":0,"其他":0,
                    **dict.fromkeys(("本体类","电类","电梯类","道路景观类","给排水类","空调类","开水饮水类","门窗五金类","暖气类","洗浴热水类","消防设施类"),0)}
                assert read_statistics(sessions["student_b"])["total"] == 0
            action(sessions["repairer_a"], ticket_id, "accept")
            if verify_statistics:
                accepted = read_statistics(student)
                assert accepted["by_status"] == {"PENDING":1,"ACCEPTED":1,"IN_PROGRESS":0,"COMPLETED":0}
                assert read_statistics(sessions["repairer_b"])["total"] == 1
            reject_without_changes(sessions["repairer_b"], ticket_id, "accept", 404)
            reject_without_changes(sessions["repairer_a"], ticket_id, "complete", 409)
            action(sessions["repairer_a"], ticket_id, "start")
            if verify_statistics:
                assert read_statistics(student)["by_status"] == {"PENDING":1,"ACCEPTED":0,"IN_PROGRESS":1,"COMPLETED":0}
            action(sessions["repairer_a"], ticket_id, "complete")
            if verify_statistics:
                complete_stats = read_statistics(student)
                assert complete_stats["by_status"] == {"PENDING":1,"ACCEPTED":0,"IN_PROGRESS":0,"COMPLETED":1}
            reject_without_changes(sessions["student_b"], ticket_id, "confirm", 404)
            reject_without_changes(student, ticket_id, "review", 409, rating="5")
            # Explicit logout/re-login before the student's completion actions.
            portal = student.get(f"{base}/portal", timeout=5)
            assert student.post(f"{base}/logout", data={"csrf_token": hidden(CSRF, portal.text, "CSRF")}, allow_redirects=False, timeout=5).status_code == 303
            login(student, base, "student_a", password)
            action(student, ticket_id, "confirm")
            action(student, ticket_id, "review", rating="5", review_text="维修及时，照明已恢复。")
            if verify_statistics:
                assert read_statistics(student) == complete_stats
                filtered = read_statistics(student, "/tickets", {"category":"照明","status":"COMPLETED"})
                assert filtered["total"] == filtered["by_category"]["照明"] == filtered["by_status"]["COMPLETED"] == 1
                zero = read_statistics(student, "/dashboard", {"category":"门锁","status":"PENDING"})
                assert zero["total"] == 0
                assert student.get(f"{base}/tickets", params={"category":"' OR 1=1 --"}, timeout=5).status_code == 400
                assert student.get(f"{base}/static/vendor/chart.umd.min.js", timeout=5).status_code == 200
            reject_without_changes(student, ticket_id, "review", 409, rating="1", review_text="覆盖尝试")
            reject_without_changes(sessions["repairer_a"], ticket_id, "start", 409)
            reject_without_changes(sessions["repairer_a"], ticket_id, "accept", 409)
            saved = row(ticket_id)
            assert saved["status"] == "COMPLETED" and saved["rating"] == 5
            assert saved["review_text"] == "维修及时，照明已恢复。"
            db = connect_database(str(database))
            try:
                assignee = db.execute("SELECT id FROM users WHERE username='repairer_a'").fetchone()[0]
            finally:
                db.close()
            assert saved["assignee_id"] == assignee
            stamps = [saved[k] for k in ("created_at", "assigned_at", "started_at", "completed_at", "confirmed_at", "reviewed_at")]
            assert all(stamps) and stamps == sorted(stamps)
            assert saved["updated_at"] == saved["reviewed_at"]
            stop(process)
            process = None
            # New process, new sessions and new secret: persistence depends on SQLite.
            environment["DORM_REPAIR_SESSION_DIR"] = str(storage / "sessions-restarted")
            environment["DORM_REPAIR_SECRET_KEY"] = secrets.token_hex(32)
            process = start()
            restarted = requests.Session()
            login(restarted, base, "student_a", password)
            page = restarted.get(f"{base}/tickets/{ticket_id}", timeout=5)
            assert page.status_code == 200 and "5 / 5 分" in page.text and "维修及时，照明已恢复。" in page.text
            assert row(ticket_id) == saved
            if verify_statistics:
                assert read_statistics(restarted) == complete_stats
                assert read_statistics(restarted, "/tickets", {"category":"照明","status":"COMPLETED"}) == filtered
                print("Phase 4 filters, scoped statistics, local assets and restart passed")
            print(json.dumps({
                "workflow": "passed", "atomic_fields": "passed", "private_rejections": [404, 404],
                "illegal_transition": 409, "duplicate_review": 409,
                "restart_new_process": first_pid != process.pid,
                "restart_all_fields_equal": True, "rating": saved["rating"],
            }, ensure_ascii=False))
            print("Phase 3 real HTTP and process restart passed")
        finally:
            if process is not None and process.poll() is None:
                stop(process)
            log.close()


if __name__ == "__main__":
    main()
