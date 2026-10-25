"""User-requested categories, custom Other text, and lossless v1 migration."""
from pathlib import Path
import sqlite3

import pytest

from app import create_app
from app.db import get_db, migrate_database, connect_database
from tests.conftest import login
from tests.test_tickets import new_form, valid_payload, create_via_http
from tests.test_queries_stats import statistics


NEW_TYPES = ("本体类", "电类", "电梯类", "道路景观类", "给排水类", "空调类", "开水饮水类", "门窗五金类", "暖气类", "洗浴热水类", "消防设施类")


def test_all_requested_types_are_saved_and_filterable(app, client):
    assert login(client).status_code == 303
    form = client.get('/tickets/new')
    for category in NEW_TYPES:
        assert f'value="{category}"' in form.text
        response = create_via_http(client, category=category)
        assert response.status_code == 303
        assert category in client.get(response.location).text
        data = statistics(client.get('/tickets', query_string={'category':category}))
        assert data['total'] == data['by_category'][category] == 1
    assert statistics(client.get('/dashboard'))['total'] == 11
    with app.app_context():
        assert [r[0] for r in get_db().execute('SELECT category FROM repair_tickets ORDER BY id')] == list(NEW_TYPES)


def test_other_validation_replay_conflict_and_escaping(app, client):
    assert login(client).status_code == 303
    csrf, token = new_form(client)
    payload = valid_payload(csrf, token, category='其他')
    for invalid in ('', '   ', '字'*51):
        response = client.post('/tickets/new', data={**payload, 'category_detail':invalid})
        assert response.status_code == 400
        assert '具体报修类型' in response.text
        with app.app_context():
            assert get_db().execute('SELECT COUNT(*) FROM repair_tickets').fetchone()[0] == 0
    detail = '<script>alert(1)</script>'
    payload['category_detail'] = '  '+detail+'  '
    response = client.post('/tickets/new', data=payload)
    assert response.status_code == 303
    page = client.get(response.location)
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in page.text
    assert detail not in page.text
    assert client.post('/tickets/new', data=payload).location == response.location
    assert client.post('/tickets/new', data={**payload, 'category_detail':'家具损坏'}).status_code == 409
    with app.app_context():
        rows = get_db().execute('SELECT category,category_detail FROM repair_tickets').fetchall()
        assert [tuple(row) for row in rows] == [('其他',detail)]
    counts = statistics(client.get('/tickets?category=其他'))
    assert counts['total'] == counts['by_category']['其他'] == 1
    for text in ('字', '字'*50):
        assert create_via_http(client, category='其他', category_detail=text).status_code == 303
    assert create_via_http(client, category='空调类', category_detail='不适用').status_code == 400
    assert client.get('/static/js/ticket-form.js').status_code == 200


def legacy_app(tmp_path):
    path = tmp_path/'legacy.sqlite3'
    db = sqlite3.connect(path)
    db.executescript(Path('tests/fixtures/schema_v1.sql').read_text(encoding='utf-8'))
    db.execute("INSERT INTO users VALUES(1,'legacy',?,'历史学生','student','2026-10-23T00:00:00Z')", ('x'*21,))
    db.execute("INSERT INTO repair_tickets (id,student_id,building,room_number,category,description,created_at,updated_at,submission_token) VALUES(17,1,'旧楼','101','其他','历史故障描述内容','2026-10-23T00:00:00Z','2026-10-23T00:00:00Z','old-token')")
    db.commit()
    db.close()
    return create_app({'TESTING':True,'SECRET_KEY':'migration-test','DATABASE':str(path),'SESSION_DIR':str(tmp_path/'sessions')})


def test_explicit_migration_keeps_all_data_backup_constraints_and_is_repeatable(tmp_path):
    app = legacy_app(tmp_path)
    with app.app_context():
        db = get_db()
        old = tuple(db.execute('SELECT * FROM repair_tickets').fetchone())
        names = [r['name'] for r in db.execute('PRAGMA table_info(repair_tickets)')]
        users = [tuple(r) for r in db.execute('SELECT * FROM users')]
    # init-db cannot silently upgrade or reset the existing database.
    assert app.test_cli_runner().invoke(args=['init-db']).exit_code != 0
    result = app.test_cli_runner().invoke(args=['migrate-db'])
    assert result.exit_code == 0, result.output
    backups = list(tmp_path.glob('*.v1-backup-*.sqlite3'))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute('PRAGMA user_version').fetchone()[0] == 1
        assert backup.execute('SELECT * FROM repair_tickets').fetchone() == old
    with app.app_context():
        db = get_db()
        assert db.execute('PRAGMA user_version').fetchone()[0] == 2
        assert tuple(db.execute('SELECT '+','.join(names)+' FROM repair_tickets').fetchone()) == old
        assert db.execute('SELECT category_detail FROM repair_tickets').fetchone()[0] is None
        assert [tuple(r) for r in db.execute('SELECT * FROM users')] == users
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        assert '未修改现有数据' in migrate_database()
        assert len(list(tmp_path.glob('*.v1-backup-*.sqlite3'))) == 1
        for category, detail in [('未知',None),('照明','家具'),('其他','字'*51),('其他','  ')]:
            with pytest.raises(sqlite3.IntegrityError):
                db.execute('UPDATE repair_tickets SET category=?,category_detail=? WHERE id=17',(category,detail))
            db.rollback()
        db.execute("UPDATE repair_tickets SET category='空调类' WHERE id=17")
        db.commit()
    reopened = connect_database(app.config['DATABASE'])
    assert reopened.execute('SELECT category FROM repair_tickets WHERE id=17').fetchone()[0] == '空调类'
    reopened.close()


def test_migration_failure_rolls_back_dropped_table_and_version(tmp_path, monkeypatch):
    app = legacy_app(tmp_path)
    with app.app_context():
        db = get_db()
        before = [tuple(r) for r in db.execute('SELECT * FROM repair_tickets')]
        class FailingConnection:
            def __getattr__(self, name):
                return getattr(db,name)
            def execute(self, sql, *args):
                if sql.startswith('CREATE INDEX'):
                    raise sqlite3.OperationalError('injected index creation failure')
                return db.execute(sql,*args)
        monkeypatch.setattr('app.db.get_db',lambda:FailingConnection())
        with pytest.raises(sqlite3.OperationalError,match='injected'):
            migrate_database()
        assert db.execute('PRAGMA user_version').fetchone()[0] == 1
        assert [tuple(r) for r in db.execute('SELECT * FROM repair_tickets')] == before
        assert 'category_detail' not in [r['name'] for r in db.execute('PRAGMA table_info(repair_tickets)')]
