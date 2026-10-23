from __future__ import annotations

from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf import FlaskForm
from werkzeug.security import check_password_hash
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length

from .db import get_db


bp = Blueprint("auth", __name__)


class LoginForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("密码", validators=[DataRequired(), Length(max=200)])
    submit = SubmitField("登录")


class EmptyForm(FlaskForm):
    submit = SubmitField("退出登录")


@bp.before_app_request
def load_logged_in_user() -> None:
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return
    g.user = get_db().execute(
        "SELECT id, username, display_name, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if g.user is None:
        session.clear()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            if request.method == "GET":
                return redirect(url_for("auth.login", next=request.path))
            abort(401)
        return view(**kwargs)

    return wrapped_view


def role_required(role: str):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped_view(**kwargs):
            if g.user["role"] != role:
                abort(403)
            return view(**kwargs)

        return wrapped_view

    return decorator


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user is not None:
        return redirect(url_for("pages.portal"))
    form = LoginForm()
    if form.validate_on_submit():
        user = get_db().execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (form.username.data.strip(),),
        ).fetchone()
        if user is None or not check_password_hash(user["password_hash"], form.password.data):
            form.password.errors.append("用户名或密码不正确。")
            return render_template("login.html", form=form), 400

        session.clear()
        session["_rotation_marker"] = True
        current_app.session_interface.regenerate(session)
        session.pop("_rotation_marker", None)
        session["user_id"] = user["id"]
        session.permanent = True
        flash("登录成功。", "success")
        return redirect(url_for("pages.portal"), code=303)

    status = 400 if request.method == "POST" else 200
    return render_template("login.html", form=form), status


@bp.post("/logout")
@login_required
def logout():
    form = EmptyForm()
    if not form.validate_on_submit():
        abort(400)
    session.clear()
    flash("你已安全退出。", "success")
    return redirect(url_for("pages.index"), code=303)

