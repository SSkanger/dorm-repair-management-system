from __future__ import annotations

import secrets

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import AnyOf, DataRequired, Length

from .auth import login_required, role_required
from .queries import (
    PAGE_SIZE,
    get_visible_ticket,
    list_repairer_visible_tickets,
    list_student_tickets,
)
from .services import (
    CATEGORIES,
    TicketConflictError,
    TicketInput,
    TicketStorageError,
    create_ticket,
)


bp = Blueprint("tickets", __name__)
STATUS_LABELS = {
    "PENDING": "待处理",
    "ACCEPTED": "已接单",
    "IN_PROGRESS": "维修中",
    "COMPLETED": "已完成",
}
ALLOWED_CREATE_FIELDS = {
    "csrf_token",
    "submission_token",
    "building",
    "room_number",
    "category",
    "description",
    "submit",
}
SESSION_TOKEN_KEY = "ticket_submission_tokens"
MAX_SESSION_TOKENS = 10


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class TicketForm(FlaskForm):
    submission_token = HiddenField(
        validators=[
            DataRequired(message="提交标识无效，请刷新页面后重试。"),
            Length(max=200, message="提交标识无效，请刷新页面后重试。"),
        ]
    )
    building = StringField(
        "楼栋",
        filters=[_strip],
        validators=[
            DataRequired(message="请填写楼栋。"),
            Length(max=30, message="楼栋最多 30 个字符。"),
        ],
    )
    room_number = StringField(
        "宿舍号",
        filters=[_strip],
        validators=[
            DataRequired(message="请填写宿舍号。"),
            Length(max=20, message="宿舍号最多 20 个字符。"),
        ],
    )
    category = SelectField(
        "故障类型",
        choices=[(item, item) for item in CATEGORIES],
        validators=[
            DataRequired(message="请选择故障类型。"),
            AnyOf(CATEGORIES, message="请选择有效的故障类型。"),
        ],
        validate_choice=False,
    )
    description = TextAreaField(
        "故障描述",
        filters=[_strip],
        validators=[
            DataRequired(message="请填写故障描述。"),
            Length(min=5, max=1000, message="故障描述需为 5–1000 个字符。"),
        ],
    )
    submit = SubmitField("提交报修")


def _issue_submission_token() -> str:
    token = secrets.token_urlsafe(24)
    tokens = list(session.get(SESSION_TOKEN_KEY, []))
    tokens.append(token)
    session[SESSION_TOKEN_KEY] = tokens[-MAX_SESSION_TOKENS:]
    return token


def _valid_session_token(token: str) -> bool:
    return bool(token) and token in session.get(SESSION_TOKEN_KEY, [])


def _parse_page() -> int:
    if set(request.args) - {"page"} or len(request.args.getlist("page")) > 1:
        abort(400)
    raw_page = request.args.get("page", "1")
    if not raw_page.isascii() or not raw_page.isdigit():
        abort(400)
    page = int(raw_page)
    if page < 1 or page > (2**63 - 1) // PAGE_SIZE:
        abort(400)
    return page


@bp.route("/tickets/new", methods=("GET", "POST"))
@role_required("student")
def new_ticket():
    form = TicketForm()
    if request.method == "GET":
        form.submission_token.data = _issue_submission_token()
        return render_template("tickets/new.html", form=form)

    unexpected = set(request.form) - ALLOWED_CREATE_FIELDS
    if unexpected:
        abort(400)

    token = form.submission_token.data or ""
    form_valid = form.validate()
    token_valid = _valid_session_token(token)
    if not token_valid:
        form.submission_token.errors.append("提交标识已失效，请刷新页面后重新提交。")
    if form_valid and token_valid:
        data = TicketInput.normalized(
            form.building.data,
            form.room_number.data,
            form.category.data,
            form.description.data,
        )
        try:
            ticket_id, created = create_ticket(
                student_id=g.user["id"], submission_token=token, data=data
            )
        except TicketConflictError as error:
            return render_template("tickets/new.html", form=form, conflict=str(error)), 409
        except TicketStorageError as error:
            return render_template("tickets/new.html", form=form, storage_error=str(error)), 503

        flash("报修提交成功。" if created else "该报修已提交，已为你打开原工单。", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id), code=303)

    return render_template("tickets/new.html", form=form), 400


@bp.get("/tickets")
@role_required("student")
def ticket_list():
    page = list_student_tickets(g.user["id"], _parse_page())
    return render_template("tickets/list.html", ticket_page=page)


@bp.get("/work-queue")
@role_required("repairer")
def work_queue():
    page = list_repairer_visible_tickets(g.user["id"], _parse_page())
    return render_template("tickets/work_queue.html", ticket_page=page)


@bp.get("/tickets/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id: int):
    if ticket_id < 1 or ticket_id > 2**63 - 1:
        abort(404)
    ticket = get_visible_ticket(ticket_id, user_id=g.user["id"], role=g.user["role"])
    if ticket is None:
        abort(404)
    return render_template(
        "tickets/detail.html", ticket=ticket, status_label=STATUS_LABELS[ticket["status"]]
    )

