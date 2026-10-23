from __future__ import annotations

from dataclasses import dataclass

from .db import get_db


PAGE_SIZE = 20


@dataclass(frozen=True)
class TicketPage:
    items: list
    page: int
    total: int
    page_size: int = PAGE_SIZE

    @property
    def total_pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages


def list_student_tickets(student_id: int, page: int) -> TicketPage:
    db = get_db()
    total = db.execute(
        "SELECT COUNT(*) FROM repair_tickets WHERE student_id = ?", (student_id,)
    ).fetchone()[0]
    items = db.execute(
        "SELECT id, building, room_number, category, status, created_at "
        "FROM repair_tickets WHERE student_id = ? "
        "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        (student_id, PAGE_SIZE, (page - 1) * PAGE_SIZE),
    ).fetchall()
    return TicketPage(items=items, page=page, total=total)


def list_repairer_visible_tickets(repairer_id: int, page: int) -> TicketPage:
    scope = "((status = 'PENDING' AND assignee_id IS NULL) OR assignee_id = ?)"
    db = get_db()
    total = db.execute(
        f"SELECT COUNT(*) FROM repair_tickets WHERE {scope}", (repairer_id,)
    ).fetchone()[0]
    items = db.execute(
        "SELECT id, building, room_number, category, status, created_at "
        f"FROM repair_tickets WHERE {scope} "
        "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        (repairer_id, PAGE_SIZE, (page - 1) * PAGE_SIZE),
    ).fetchall()
    return TicketPage(items=items, page=page, total=total)


def get_visible_ticket(ticket_id: int, *, user_id: int, role: str):
    db = get_db()
    columns = (
        "id, student_id, assignee_id, building, room_number, category, description, "
        "status, created_at, updated_at, assigned_at, started_at, completed_at, "
        "confirmed_at, rating, review_text, reviewed_at"
        ", (SELECT u.display_name FROM users AS u WHERE u.id = repair_tickets.assignee_id) "
        "AS assignee_name"
    )
    if role == "student":
        return db.execute(
            f"SELECT {columns} FROM repair_tickets WHERE id = ? AND student_id = ?",
            (ticket_id, user_id),
        ).fetchone()
    if role == "repairer":
        return db.execute(
            f"SELECT {columns} FROM repair_tickets WHERE id = ? AND "
            "((status = 'PENDING' AND assignee_id IS NULL) OR assignee_id = ?)",
            (ticket_id, user_id),
        ).fetchone()
    return None

