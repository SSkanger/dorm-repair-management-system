from app import create_app


def test_application_factory_and_basic_pages(client):
    home = client.get("/")
    login = client.get("/login")
    health = client.get("/health")

    assert home.status_code == 200
    assert "宿舍报修管理系统" in home.get_data(as_text=True)
    assert login.status_code == 200
    assert 'name="csrf_token"' in login.get_data(as_text=True)
    assert health.status_code == 200
    assert health.get_json() == {"status": "ok", "database": "ready"}


def test_health_is_unhealthy_before_database_initialization(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "health-test",
            "DATABASE": str(tmp_path / "empty.sqlite3"),
            "SESSION_DIR": str(tmp_path / "sessions"),
        }
    )
    response = app.test_client().get("/health")
    assert response.status_code == 503
    assert response.get_json() == {"status": "unhealthy"}

