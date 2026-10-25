from __future__ import annotations

import os
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash


SCHEMA_VERSION = 2
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
    if "category_detail" not in {row["name"] for row in connection.execute("PRAGMA table_info(repair_tickets)")}:
        raise DatabaseVersionError("数据库缺少具体报修类型字段，请先备份并执行显式迁移。")


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
    return f"数据库初始化完成（版本 {SCHEMA_VERSION}）。"


def migrate_database() -> str:
    """Explicit v1 -> v2 migration; preserve rows, constraints and a backup."""
    connection = get_db()
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version == SCHEMA_VERSION:
        verify_schema(connection)
        return "数据库已是最新版本，未修改现有数据。"
    if version != 1 or _user_tables(connection) != REQUIRED_TABLES:
        raise DatabaseVersionError("仅支持完整版本1数据库升级；未知结构不会被修改。")
    # Refuse extensions that would otherwise be silently lost during rebuilding.
    extras = connection.execute(
        "SELECT name FROM sqlite_master WHERE tbl_name='repair_tickets' "
        "AND (type='trigger' OR (type='index' AND sql IS NOT NULL "
        "AND name NOT IN ('idx_tickets_student_created','idx_tickets_assignee_created',"
        "'idx_tickets_status_created')))"
    ).fetchall()
    if extras:
        raise DatabaseVersionError("检测到自定义索引或触发器，请人工迁移，未修改数据。")
    backup_path = Path(str(current_app.config["DATABASE"]) + ".v1-backup-" + secrets.token_hex(6) + ".sqlite3")
    with closing(sqlite3.connect(backup_path)) as backup:
        connection.backup(backup)
    schema = Path(current_app.root_path, "schema.sql").read_text(encoding="utf-8")
    statements = [part.strip() for part in schema.split(";") if part.strip()]
    ticket_sql = next(part for part in statements if part.startswith("CREATE TABLE repair_tickets"))
    indexes = [part for part in statements if part.startswith("CREATE INDEX")]
    try:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise DatabaseVersionError("迁移期间版本发生变化，请停止其他服务后重试。")
        columns = [row["name"] for row in connection.execute("PRAGMA table_info(repair_tickets)")]
        expected = {"id", "student_id", "assignee_id", "building", "room_number", "category", "description", "status", "created_at", "updated_at", "assigned_at", "started_at", "completed_at", "confirmed_at", "rating", "review_text", "reviewed_at", "submission_token"}
        if set(columns) != expected:
            raise DatabaseVersionError("版本1工单字段不匹配，拒绝覆盖未知字段。")
        fields = ", ".join(columns)  # Validated against the fixed schema above.
        before = [tuple(row) for row in connection.execute(f"SELECT {fields} FROM repair_tickets ORDER BY id")]
        connection.execute(ticket_sql.replace("CREATE TABLE repair_tickets", "CREATE TABLE repair_tickets_v2", 1))
        connection.execute(f"INSERT INTO repair_tickets_v2 ({fields}) SELECT {fields} FROM repair_tickets")
        after = [tuple(row) for row in connection.execute(f"SELECT {fields} FROM repair_tickets_v2 ORDER BY id")]
        if after != before:
            raise DatabaseVersionError("迁移数据核对失败，已取消。")
        connection.execute("DROP TABLE repair_tickets")
        connection.execute("ALTER TABLE repair_tickets_v2 RENAME TO repair_tickets")
        for statement in indexes:
            connection.execute(statement)
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise DatabaseVersionError("迁移外键检查失败，已取消。")
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return f"数据库已升级至版本2；旧工单、账号均保留。备份：{backup_path.name}"


@click.command("migrate-db")
@with_appcontext
def migrate_db_command() -> None:
    """Stop the web server before running this explicit migration."""
    try:
        click.echo(migrate_database())
    except (DatabaseVersionError, sqlite3.Error) as error:
        raise click.ClickException(str(error)) from error


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
    app.cli.add_command(migrate_db_command)

