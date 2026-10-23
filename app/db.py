from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash


SCHEMA_VERSION = 1
REQUIRED_TABLES = {"users", "repair_tickets"}
DEMO_USERS = (
    ("student_a", "学生甲", "student"),
    ("student_b", "学生乙", "student"),
    ("repairer_a", "维修员甲", "repairer"),
    ("repairer_b", "维修员乙", "repairer"),
)


class DatabaseVersionError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def connect_database(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect_database(current_app.config["DATABASE"])
    return g.db


def close_db(_exception=None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def _user_tables(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row["name"] for row in rows}


def verify_schema(connection: sqlite3.Connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version != SCHEMA_VERSION:
        raise DatabaseVersionError(
            f"数据库版本不兼容：检测到 {version}，应用要求 {SCHEMA_VERSION}。"
            "请先备份并执行显式迁移，程序不会自动删除数据。"
        )
    tables = _user_tables(connection)
    if not REQUIRED_TABLES.issubset(tables):
        missing = ", ".join(sorted(REQUIRED_TABLES - tables))
        raise DatabaseVersionError(f"数据库结构不完整，缺少表：{missing}。")


def init_database() -> str:
    connection = get_db()
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    tables = _user_tables(connection)
    if version == SCHEMA_VERSION:
        verify_schema(connection)
        return "数据库已是最新版本，未修改现有数据。"
    if version != 0 or tables:
        raise DatabaseVersionError(
            f"拒绝初始化不兼容数据库（版本 {version}，已有表："
            f"{', '.join(sorted(tables)) or '无'}）。请先备份并显式迁移。"
        )

    schema = Path(current_app.root_path, "schema.sql").read_text(encoding="utf-8")
    try:
        connection.executescript(schema)
        verify_schema(connection)
    except Exception:
        connection.rollback()
        raise
    return "数据库初始化完成（版本 1）。"


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    try:
        message = init_database()
    except DatabaseVersionError as error:
        raise click.ClickException(str(error)) from error
    click.echo(message)


@click.command("seed-demo")
@click.option(
    "--password",
    envvar="DORM_REPAIR_DEMO_PASSWORD",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="四个演示账号共用的初始密码；也可用环境变量提供。",
)
@with_appcontext
def seed_demo_command(password: str) -> None:
    if len(password) < 8:
        raise click.ClickException("演示密码至少需要 8 个字符。")
    connection = get_db()
    try:
        verify_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        existing = {
            row["username"]: row
            for row in connection.execute(
                "SELECT username, display_name, role FROM users WHERE username IN (?, ?, ?, ?)",
                tuple(user[0] for user in DEMO_USERS),
            ).fetchall()
        }
        for username, display_name, role in DEMO_USERS:
            if username in existing:
                row = existing[username]
                if row["role"] != role or row["display_name"] != display_name:
                    raise click.ClickException(
                        f"账号 {username} 已存在但身份信息冲突；未修改任何账号。"
                    )
                continue
            connection.execute(
                "INSERT INTO users (username, password_hash, display_name, role, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, generate_password_hash(password), display_name, role, utc_now()),
            )
        connection.commit()
    except DatabaseVersionError as error:
        connection.rollback()
        raise click.ClickException(str(error)) from error
    except Exception:
        connection.rollback()
        raise
    click.echo("演示账号准备完成；已有匹配账号保持不变。")


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_demo_command)

