"""Independent HTTP/SQLite acceptance; no application service functions imported."""
from __future__ import annotations

import json
import os
from contextlib import closing
from pathlib import Path
import re
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

import requests


ROOT = Path(__file__).resolve().parents[1]


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="dorm-independent-") as folder:
        storage = Path(folder)
        database = storage / "acceptance.sqlite3"
        password = secrets.token_urlsafe(20)
        env = {k: v for k, v in os.environ.items() if not k.startswith("DORM_REPAIR_")}
        env.update(DORM_REPAIR_DATABASE=str(database), DORM_REPAIR_SESSION_DIR=str(storage / "sessions"),
                   DORM_REPAIR_SECRET_KEY=secrets.token_hex(32), DORM_REPAIR_DEMO_PASSWORD=password,
                   DORM_REPAIR_COOKIE_SECURE="0", PYTHONIOENCODING="utf-8")
        for command in ("init-db", "seed-demo", "init-db", "seed-demo"):
            result = subprocess.run([sys.executable, "-m", "flask", "--app", "run:app", command],
                                    cwd=ROOT, env=env, capture_output=True)
            assert result.returncode == 0, f"CLI {command} exit={result.returncode}"

        def rows():
            with closing(sqlite3.connect(database)) as connection:
                connection.row_factory = sqlite3.Row
                return [dict(r) for r in connection.execute("SELECT * FROM repair_tickets ORDER BY id")]

        def token(session, path="/portal"):
            response = session.get(base + path, timeout=10)
            assert response.status_code == 200
            match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', response.text)
            assert match
            return match.group(1)

        def login(name):
            session = requests.Session()
            response = session.post(base + "/login", data={"username": name, "password": password,
                "csrf_token": token(session, "/login")}, allow_redirects=False, timeout=10)
            assert response.status_code == 303
            return session

        def post(session, path, expected, **values):
            response = session.post(base + path, data={"csrf_token": token(session), **values},
                                    allow_redirects=False, timeout=10)
            assert response.status_code == expected, (path, response.status_code, expected)
            return response

        def rejected(session, path, expected, **values):
            before = rows()
            post(session, path, expected, **values)
            assert rows() == before, f"Rejected action modified data: {path}"
            checks.append({"path": path, "rejected": expected, "all_rows_unchanged": True})

        def create(session, category, description, expected=303):
            page = session.get(base + "/tickets/new", timeout=10)
            submission = re.search(r'name="submission_token"[^>]*value="([^"]+)"', page.text).group(1)
            data = {"building":"3号楼", "room_number":"406", "category":category,
                    "description":description, "submission_token":submission}
            response = post(session, "/tickets/new", expected, **data)
            return response, data

        def stats(session, params=None):
            response = session.get(base + "/dashboard", params=params, timeout=10)
            assert response.status_code == 200
            data = json.loads(re.search(r'id="ticket-statistics">(.*?)</script>', response.text, re.S).group(1))
            actual = rows()
            # Expectations below use fixed two-row input, not a business query helper.
            assert data["total"] == sum(data["by_category"].values()) == sum(data["by_status"].values())
            assert len(actual) == 2
            return data

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        process = None
        with (storage / "server.log").open("w", encoding="utf-8") as log:
            def start():
                server = subprocess.Popen([sys.executable, "-m", "flask", "--app", "run:app", "run",
                    "--host", "127.0.0.1", "--port", str(port), "--no-reload"], cwd=ROOT, env=env,
                    stdout=log, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError("Independent server exited before health check")
                    try:
                        if requests.get(base + "/health", timeout=1).status_code == 200:
                            return server
                    except requests.RequestException:
                        pass
                    time.sleep(0.1)
                server.terminate(); server.wait(timeout=10)
                raise RuntimeError("Independent server startup timed out")

            try:
                process = start()
                assert requests.get(base + "/", timeout=10).status_code == 200
                assert requests.get(base + "/login", timeout=10).status_code == 200
                anonymous = requests.Session()
                assert anonymous.post(base + "/tickets/new", timeout=10).status_code == 400
                response = anonymous.post(base + "/tickets/new", data={"csrf_token":token(anonymous,"/login")}, timeout=10)
                assert response.status_code == 401
                users = {name:login(name) for name in ("student_a","student_b","repairer_a","repairer_b")}
                student, repairer = users["student_a"], users["repairer_a"]
                rejected(repairer, "/tickets/new", 403)
                for description in ("", "   ", "四个字符"):
                    before = rows(); create(student,"照明",description,400); assert rows() == before
                created, data = create(student,"照明","独立验收：宿舍灯具无法正常点亮。")
                ticket_id = int(created.headers["Location"].rsplit("/",1)[1])
                path = f"/tickets/{ticket_id}"
                assert rows()[0]["status"] == "PENDING" and rows()[0]["assignee_id"] is None
                post(student, "/tickets/new", 303, **data); assert len(rows()) == 1
                rejected(student,"/tickets/new",409,**{**data,"description":"同一标识的不同描述应当拒绝。"})
                create(student,"网络","独立验收：网络接口无法连接。")
                assert users["student_b"].get(base+path,timeout=10).status_code == 404
                expected_types = {"照明":1,"网络":1,"水管":0,"门锁":0,"其他":0,
                    **dict.fromkeys(("本体类","电类","电梯类","道路景观类","给排水类","空调类","开水饮水类","门窗五金类","暖气类","洗浴热水类","消防设施类"),0)}
                assert stats(student)["by_category"] == expected_types
                assert stats(users["student_b"])["total"] == 0
                rejected(student,path+"/confirm",409)
                rejected(student,path+"/review",409,rating="5")
                rejected(student,path+"/accept",403)
                post(repairer,path+"/accept",303)
                rejected(users["repairer_b"],path+"/accept",404)
                rejected(repairer,path+"/accept",409)
                rejected(repairer,path+"/complete",409)
                assert stats(users["repairer_b"])["total"] == 1
                post(repairer,path+"/start",303)
                post(repairer,path+"/complete",303)
                rejected(repairer,path+"/accept",409)
                rejected(repairer,path+"/start",409)
                rejected(users["student_b"],path+"/confirm",404)
                rejected(student,path+"/review",409,rating="5")
                post(student,path+"/confirm",303)
                rejected(student,path+"/confirm",409)
                for rating in ("", "0", "6", "1.5", "文字"):
                    rejected(student,path+"/review",400,rating=rating)
                post(student,path+"/review",303,rating="5",review_text="独立验收通过，照明恢复。")
                rejected(student,path+"/review",409,rating="1",review_text="不能覆盖")
                before=rows()
                assert repairer.get(base+path+"/complete",timeout=10).status_code == 405
                assert student.post(base+path+"/confirm",data={"csrf_token":"invalid"},timeout=10).status_code == 400
                assert rows() == before
                expected_states={"PENDING":1,"ACCEPTED":0,"IN_PROGRESS":0,"COMPLETED":1}
                assert stats(student)["by_status"] == expected_states
                filtered=stats(student,{"category":"照明","status":"COMPLETED"})
                assert filtered["total"] == filtered["by_status"]["COMPLETED"] == 1
                assert stats(student,{"category":"门锁"})["total"] == 0
                assert student.get(base+"/tickets",params={"category":"' OR 1=1 --"},timeout=10).status_code == 400
                for asset in ("vendor/chart.umd.min.js","vendor/Chart.js-LICENSE.md","css/app.css","js/charts.js"):
                    assert student.get(base+"/static/"+asset,timeout=10).status_code == 200
                final=rows()
                assert final[0]["rating"] == 5 and final[0]["confirmed_at"] and final[0]["reviewed_at"]
                assert all(final[0][k] for k in ("assigned_at","started_at","completed_at"))
                with closing(sqlite3.connect(database)) as db:
                    owner=db.execute("SELECT id FROM users WHERE username='repairer_a'").fetchone()[0]
                    assert final[0]["assignee_id"] == owner
                process.terminate();process.wait(timeout=10)
                process=start()
                restarted=login("student_a")
                assert rows() == final and stats(restarted)["by_status"] == expected_states
                assert "独立验收通过，照明恢复。" in restarted.get(base+path,timeout=10).text
                logout=post(restarted,"/logout",303)
                assert restarted.get(base+"/portal",allow_redirects=False,timeout=10).status_code == 302
                print(json.dumps({"result":"PASS","independent_http":True,
                    "database_full_rows_checked":True,"restart_persistence":"PASS",
                    "final_type_counts":expected_types,
                    "final_status_counts":expected_states,"rejection_checks":checks},ensure_ascii=False,indent=2))
            finally:
                if process is not None and process.poll() is None:
                    process.terminate();process.wait(timeout=10)


if __name__ == "__main__":
    main()
