from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .db import get_db, utc_now


CATEGORIES = ("照明", "水管", "门锁", "网络", "其他")


class TicketConflictError(RuntimeError):
    """The request token was already used for different ticket content."""


class TicketStorageError(RuntimeError):
    """SQLite could not complete a ticket write safely."""


@dataclass(frozen=True)
class TicketInput:
    building: str
    room_number: str
    category: str
    description: str

    @classmethod
    def normalized(
        cls, building: str, room_number: str, category: str, description: str
    ) -> "TicketInput":
        return cls(
            building=building.strip(),
            room_number=room_number.strip(),
            category=category.strip(),
            description=description.strip(),
        )


def _same_content(row: sqlite3.Row, data: TicketInput) -> bool:
    return all(
        row[field] == getattr(data, field)
        for field in ("building", "room_number", "category", "description")
    )


def create_ticket(
    *, student_id: int, submission_token: str, data: TicketInput
) -> tuple[int, bool]:
    """Create one pending ticket, or return the prior ticket for an exact replay.

    The transaction serializes writers before checking the unique request key.
    A reused token with changed normalized content is a conflict. The actor,
    initial status and timestamps always come from trusted server state.
    """

    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT id, building, room_number, category, description "
            "FROM repair_tickets WHERE student_id = ? AND submission_token = ?",
            (student_id, submission_token),
        ).fetchone()
        if existing is not None:
            if not _same_content(existing, data):
                raise TicketConflictError(
                    "该提交标识已经用于另一份报修内容，请返回新建页面重新填写。"
                )
            db.commit()
            return existing["id"], False

        now = utc_now()
        cursor = db.execute(
            "INSERT INTO repair_tickets "
            "(student_id, building, room_number, category, description, status, "
            "created_at, updated_at, submission_token) "
            "VALUES (?, ?, ?, ?, ?, 'PENDING', ?, ?, ?)",
            (
                student_id,
                data.building,
                data.room_number,
                data.category,
                data.description,
                now,
                now,
                submission_token,
            ),
        )
        ticket_id = cursor.lastrowid
        db.commit()
        return ticket_id, True
    except TicketConflictError:
        db.rollback()
        raise
    except sqlite3.Error as error:
        db.rollback()
        raise TicketStorageError("报修暂时无法保存，请稍后重试。") from error

