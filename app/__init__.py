from __future__ import annotations

import os
import secrets
from datetime import timedelta
from pathlib import Path

from cachelib.file import FileSystemCache
from flask import Flask, render_template
from flask_session import Session
from flask_wtf.csrf import CSRFError, CSRFProtect


server_session = Session()
csrf = CSRFProtect()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_or_create_secret(instance_path: Path) -> str:
    secret_file = instance_path / "secret_key"
    if secret_file.exists():
        return secret_file.read_text(encoding="utf-8").strip()
    value = secrets.token_hex(32)
    secret_file.write_text(value, encoding="utf-8")
    return value


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    instance_path = Path(app.instance_path)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("DORM_REPAIR_SECRET_KEY"),
        DATABASE=os.environ.get(
            "DORM_REPAIR_DATABASE", str(instance_path / "dorm_repair.sqlite3")
        ),
        SESSION_DIR=os.environ.get(
            "DORM_REPAIR_SESSION_DIR", str(instance_path / "sessions")
        ),
        SESSION_TYPE="cachelib",
        SESSION_SERIALIZATION_FORMAT="json",
        SESSION_PERMANENT=True,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
        SESSION_COOKIE_NAME="dorm_repair_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_env_bool("DORM_REPAIR_COOKIE_SECURE"),
        SESSION_REFRESH_EACH_REQUEST=True,
        # Flask-WTF passes this value to itsdangerous as max_age seconds.
        WTF_CSRF_TIME_LIMIT=7200,
    )

    if test_config:
        app.config.from_mapping(test_config)

    if not app.config.get("SECRET_KEY"):
        instance_path.mkdir(parents=True, exist_ok=True)
        app.config["SECRET_KEY"] = _load_or_create_secret(instance_path)

    configured_session_dir = Path(app.config["SESSION_DIR"])
    configured_session_dir.mkdir(parents=True, exist_ok=True)
    app.config["SESSION_CACHELIB"] = FileSystemCache(
        cache_dir=str(configured_session_dir),
        threshold=100 if app.config.get("TESTING") else 500,
        default_timeout=7200,
    )

    database_path = Path(app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)

    server_session.init_app(app)
    csrf.init_app(app)

    from . import auth, db, pages

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(pages.bp)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error: CSRFError):
        return render_template(
            "error.html", code=400, title="请求验证失败", message=error.description
        ), 400

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(405)
    def handle_http_error(error):
        descriptions = {
            400: "请求内容不正确，请检查后重试。",
            401: "请先登录后再执行此操作。",
            403: "当前账号没有执行此操作的权限。",
            404: "未找到请求的页面或资源。",
            405: "该页面不支持当前请求方式。",
        }
        return render_template(
            "error.html",
            code=error.code,
            title=error.name,
            message=descriptions.get(error.code, error.description),
        ), error.code

    return app

