from __future__ import annotations

from dataclasses import dataclass, field

from .db import get_db, utc_now
from .constants import CATEGORIES, STATUS_LABELS


PAGE_SIZE = 20


class QueryInputError(ValueError):
    pass


@dataclass(frozen=True)
class TicketFilters:
    category: str = ""
    status: str = ""
    page: int = 1

    def params(self):
        return {key: value for key, value in (
            ("category", self.category), ("status", self.status)
        ) if value}


def parse_filters(args) -> TicketFilters:
    if set(args) - {"category", "status", "page"}:
        raise QueryInputError("查询参数不受支持，请使用类型、状态和页码筛选。")
    if any(len(args.getlist(key)) != 1 for key in args):
        raise QueryInputError("同一筛选参数只能出现一次。")
    category = args.get("category", "")
    status = args.get("status", "")
    if category and category not in CATEGORIES:
        raise QueryInputError("故障类型无效，请选择列表中的类型。")
    if status and status not in STATUS_LABELS:
        raise QueryInputError("工单状态无效，请选择列表中的状态。")
    raw = args.get("page", "1")
    # Bound text length before int() to avoid Python's large-number parse limit.
    if not raw or len(raw) > 18 or not raw.isascii() or not raw.isdigit():
        raise QueryInputError("页码必须为有效的正整数。")
    page = int(raw)
    if not 1 <= page <= (2**63 - 1) // PAGE_SIZE:
        raise QueryInputError("页码超出允许范围。")
    return TicketFilters(category, status, page)


def visible_scope(user_id: int, role: str):
    if role == "student":
        return "(student_id = ?)", (user_id,)
    if role == "repairer":
        return "((status = 'PENDING' AND assignee_id IS NULL) OR assignee_id = ?)", (user_id,)
    # Fail closed even if called without the route's role check.
    return "(0 = 1)", ()


@dataclass(frozen=True)
class TicketPage:
    items: list
    page: int
    total: int
    page_size: int = PAGE_SIZE
    by_category: dict = field(default_factory=dict)
    by_status: dict = field(default_factory=dict)
    snapshot_at: str = ""

    @property
    def chart_data(self):
        return {
            "total": self.total,
            "by_category": self.by_category,
            "by_status": self.by_status,
            "status_labels": STATUS_LABELS,
            "category_order": list(CATEGORIES),
            "status_order": list(STATUS_LABELS),
        }

    @property
    def total_pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)

    @property
    def has_previous(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages


def ticket_overview(user_id: int, role: str, filters: TicketFilters, *, include_items=True, assigned_only=False) -> TicketPage:
    scope, params = visible_scope(user_id, role)
    clauses = [scope]
    if assigned_only:
        # Read-only "my work" view always intersects the existing authorization.
        clauses.append("assignee_id = ?")
        params += (user_id,)
    for column, value in (("category", filters.category), ("status", filters.status)):
        if value:
            clauses.append(f"{column} = ?")  # column is a trusted constant.
            params += (value,)
    where = " AND ".join(clauses)
    db = get_db()
    # All SELECTs share one SQLite snapshot, including COUNT, page and aggregates.
    db.execute("BEGIN")
    try:
        total = db.execute(f"SELECT COUNT(*) FROM repair_tickets WHERE {where}", params).fetchone()[0]
        items = db.execute(
            "SELECT id, building, room_number, category, status, created_at, category_detail "
            f"FROM repair_tickets WHERE {where} "
            "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
            params + (PAGE_SIZE, (filters.page - 1) * PAGE_SIZE),
        ).fetchall() if include_items else []
        categories = dict.fromkeys(CATEGORIES, 0)
        statuses = dict.fromkeys(STATUS_LABELS, 0)
        for row in db.execute(f"SELECT category, COUNT(*) AS n FROM repair_tickets WHERE {where} GROUP BY category", params):
            categories[row["category"]] = row["n"]
        for row in db.execute(f"SELECT status, COUNT(*) AS n FROM repair_tickets WHERE {where} GROUP BY status", params):
            statuses[row["status"]] = row["n"]
        result = TicketPage(items, filters.page, total, by_category=categories, by_status=statuses, snapshot_at=utc_now())
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


def list_student_tickets(student_id: int, page: int) -> TicketPage:
    return ticket_overview(student_id, "student", TicketFilters(page=page))


def list_repairer_visible_tickets(repairer_id: int, page: int) -> TicketPage:
    return ticket_overview(repairer_id, "repairer", TicketFilters(page=page))


def get_visible_ticket(ticket_id: int, *, user_id: int, role: str):
    db = get_db()
    columns = (
        "id, student_id, assignee_id, building, room_number, category, category_detail, description, "
        "status, created_at, updated_at, assigned_at, started_at, completed_at, "
        "confirmed_at, rating, review_text, reviewed_at"
        ", (SELECT u.display_name FROM users AS u WHERE u.id = repair_tickets.assignee_id) "
        "AS assignee_name"
    )
    scope, params = visible_scope(user_id, role)
    return db.execute(
        f"SELECT {columns} FROM repair_tickets WHERE id = ? AND {scope}",
        (ticket_id,) + params,
    ).fetchone()

