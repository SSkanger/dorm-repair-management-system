from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .db import get_db, utc_now
from .queries import get_visible_ticket


CATEGORIES = ("照明", "水管", "门锁", "网络", "其他")


class TicketConflictError(RuntimeError):
    """The request token was already used for different ticket content."""


class TicketStorageError(RuntimeError):
    """SQLite could not complete a ticket write safely."""


class TicketActionError(RuntimeError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def _action_target(ticket_id: int, actor, action: str):
    required_role = "repairer" if action in {"accept", "start", "complete"} else "student"
    if actor["role"] != required_role:
        raise TicketActionError(403, "当前身份不能执行此操作。")
    if not 1 <= ticket_id <= 2**63 - 1:
        raise TicketActionError(404, "未找到请求的工单。")
    ticket = get_visible_ticket(ticket_id, user_id=actor["id"], role=actor["role"])
    if ticket is None:
        raise TicketActionError(404, "未找到请求的工单。")
    if action in {"start", "complete"} and ticket["assignee_id"] != actor["id"]:
        raise TicketActionError(404, "未找到请求的工单。")
    allowed = {
        "accept": ticket["status"] == "PENDING" and ticket["assignee_id"] is None,
        "start": ticket["status"] == "ACCEPTED",
        "complete": ticket["status"] == "IN_PROGRESS",
        "confirm": ticket["status"] == "COMPLETED" and ticket["confirmed_at"] is None,
        "review": ticket["status"] == "COMPLETED"
        and ticket["confirmed_at"] is not None and ticket["rating"] is None,
    }
    if not allowed[action]:
        raise TicketActionError(409, "当前工单状态不允许此操作，或该操作已经完成。")
    return ticket


def apply_ticket_action(ticket_id: int, *, actor, action: str, form_data) -> None:
    """Validate in a write transaction; the conditional UPDATE decides success.

    User identity is supplied by the server-side session loader. Both predicates
    and all changed timestamps are written in one statement, then committed.
    """
    if action not in {"accept", "start", "complete", "confirm", "review"}:
        raise TicketActionError(404, "未找到请求的操作。")
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        _action_target(ticket_id, actor, action)
        allowed_fields = {"csrf_token", "submit"}
        if action == "review":
            allowed_fields |= {"rating", "review_text"}
        if set(form_data) - allowed_fields or any(
            len(form_data.getlist(key)) != 1 for key in form_data
        ):
            raise TicketActionError(400, "请求包含不允许或重复的字段。")
        now = utc_now()
        if action == "accept":
            sql = (
                "UPDATE repair_tickets SET status='ACCEPTED', assignee_id=?, "
                "assigned_at=?, updated_at=? WHERE id=? "
                "AND status='PENDING' AND assignee_id IS NULL"
            )
            params = (actor["id"], now, now, ticket_id)
        elif action in {"start", "complete"}:
            # Only trusted constants choose the column and state names.
            old, new, column = (
                ("ACCEPTED", "IN_PROGRESS", "started_at")
                if action == "start" else ("IN_PROGRESS", "COMPLETED", "completed_at")
            )
            sql = (
                f"UPDATE repair_tickets SET status=?, {column}=?, updated_at=? "
                "WHERE id=? AND assignee_id=? AND status=?"
            )
            params = (new, now, now, ticket_id, actor["id"], old)
        elif action == "confirm":
            sql = (
                "UPDATE repair_tickets SET confirmed_at=?, updated_at=? "
                "WHERE id=? AND student_id=? AND status='COMPLETED' AND confirmed_at IS NULL"
            )
            params = (now, now, ticket_id, actor["id"])
        else:
            raw_rating = form_data.get("rating", "")
            if raw_rating not in {"1", "2", "3", "4", "5"}:
                raise TicketActionError(400, "评分必须为 1–5 的整数。")
            text = form_data.get("review_text", "").strip()
            if len(text) > 500:
                raise TicketActionError(400, "评价短评最多 500 个字符。")
            sql = (
                "UPDATE repair_tickets SET rating=?, review_text=?, reviewed_at=?, updated_at=? "
                "WHERE id=? AND student_id=? AND status='COMPLETED' "
                "AND confirmed_at IS NOT NULL AND rating IS NULL"
            )
            params = (int(raw_rating), text or None, now, now, ticket_id, actor["id"])
        result = db.execute(sql, params)
        if result.rowcount != 1:
            # Reclassify against current visibility rather than leaking another owner.
            _action_target(ticket_id, actor, action)
            raise TicketActionError(409, "工单已经发生变化，请刷新后重试。")
        db.commit()
    except TicketActionError:
        db.rollback()
        raise
    except sqlite3.Error as error:
        db.rollback()
        raise TicketStorageError("系统繁忙或暂时无法保存，请稍后重试。") from error


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

