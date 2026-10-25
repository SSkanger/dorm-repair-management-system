"""Real HTTP check of the category extension using disposable storage."""
import json
from contextlib import closing
import os
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


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="dorm-category-") as folder:
        storage = Path(folder)
        database = storage / "check.sqlite3"
        password = secrets.token_urlsafe(24)
        env = {k:v for k,v in os.environ.items() if not k.startswith("DORM_REPAIR_")}
        env.update(DORM_REPAIR_DATABASE=str(database), DORM_REPAIR_SESSION_DIR=str(storage/'sessions'),
                   DORM_REPAIR_SECRET_KEY=secrets.token_hex(32), DORM_REPAIR_DEMO_PASSWORD=password,
                   DORM_REPAIR_COOKIE_SECURE="0")
        for command in ('init-db','seed-demo'):
            result = subprocess.run([sys.executable,'-m','flask','--app','run:app',command],
                                    cwd=root,env=env,capture_output=True)
            assert result.returncode == 0, command
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        with (storage/'server.log').open('w',encoding='utf-8') as log:
            process = subprocess.Popen([sys.executable,'-m','flask','--app','run:app','run','--host','127.0.0.1','--port',str(port),'--no-reload'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            try:
                for _ in range(100):
                    try:
                        if requests.get(base+'/health',timeout=1).status_code==200:
                            break
                    except requests.RequestException:
                        pass
                    time.sleep(.1)
                else:
                    raise RuntimeError('Temporary server did not become ready')
                session = requests.Session()
                def csrf(page):
                    return re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text).group(1)
                page = session.get(base+'/login',timeout=10)
                assert session.post(base+'/login',data={'username':'student_a','password':password,'csrf_token':csrf(page)},allow_redirects=False,timeout=10).status_code==303
                page = session.get(base+'/tickets/new',timeout=10)
                assert 'value="消防设施类"' in page.text and 'value="空调类"' in page.text
                data = {'csrf_token':csrf(page),'submission_token':re.search(r'name="submission_token"[^>]*value="([^"]+)"',page.text).group(1),
                        'building':'3号楼','room_number':'406','category':'其他','description':'宿舍家具出现损坏需要修复。'}
                assert session.post(base+'/tickets/new',data=data,allow_redirects=False,timeout=10).status_code==400
                data['category_detail']='  家具损坏  '
                created = session.post(base+'/tickets/new',data=data,allow_redirects=False,timeout=10)
                assert created.status_code==303
                assert '家具损坏' in session.get(base+created.headers['Location'],timeout=10).text
                assert session.post(base+'/tickets/new',data=data,allow_redirects=False,timeout=10).status_code==303
                assert session.post(base+'/tickets/new',data={**data,'category_detail':'窗帘脱落'},allow_redirects=False,timeout=10).status_code==409
                page = session.get(base+'/tickets?category=其他',timeout=10)
                counts = json.loads(re.search(r'id="ticket-statistics">(.*?)</script>',page.text,re.S).group(1))
                assert counts['total']==counts['by_category']['其他']==1
                with closing(sqlite3.connect(database)) as db:
                    assert db.execute('SELECT category,category_detail,status FROM repair_tickets').fetchall()==[('其他','家具损坏','PENDING')]
                assert session.get(base+'/static/js/ticket-form.js',timeout=10).status_code==200
                print(json.dumps({'result':'PASS','real_http':True,'other_required':True,'trimmed_and_persisted':True,'replay_303':True,'changed_detail_409':True,'filtered_other_count':1,'local_script_200':True},ensure_ascii=False))
            finally:
                process.terminate()
                process.wait(timeout=10)


if __name__=='__main__':
    main()
