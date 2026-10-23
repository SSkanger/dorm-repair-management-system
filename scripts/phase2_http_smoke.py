"""Exercise the Phase 2 flow through a real running HTTP server."""
from __future__ import annotations

import argparse
import re

import requests


CSRF = re.compile(r'name="csrf_token"[^>]*value="([^"]+)"')
SUBMISSION = re.compile(r'name="submission_token"[^>]*value="([^"]+)"')
TICKET_LOCATION = re.compile(r"/tickets/(\d+)$")


def hidden(pattern: re.Pattern[str], html: str, label: str) -> str:
    match = pattern.search(html)
    if not match:
        raise RuntimeError(f"页面中没有找到 {label}")
    return match.group(1)


def login(session: requests.Session, base_url: str, username: str, password: str) -> None:
    page = session.get(f"{base_url}/login", timeout=5)
    response = session.post(
        f"{base_url}/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": hidden(CSRF, page.text, "CSRF Token"),
        },
        allow_redirects=False,
        timeout=5,
    )
    if response.status_code != 303:
        raise RuntimeError(f"账号 {username} 登录失败：HTTP {response.status_code}")


def logout(session: requests.Session, base_url: str) -> None:
    portal = session.get(f"{base_url}/portal", timeout=5)
    response = session.post(
        f"{base_url}/logout",
        data={"csrf_token": hidden(CSRF, portal.text, "CSRF Token")},
        allow_redirects=False,
        timeout=5,
    )
    if response.status_code != 303:
        raise RuntimeError(f"退出失败：HTTP {response.status_code}")


def assert_student_b_isolated(base_url: str, password: str, ticket_id: int) -> None:
    other = requests.Session()
    login(other, base_url, "student_b", password)
    listing = other.get(f"{base_url}/tickets", timeout=5)
    detail = other.get(f"{base_url}/tickets/{ticket_id}", timeout=5)
    if listing.status_code != 200 or f"#{ticket_id}" in listing.text or detail.status_code != 404:
        raise RuntimeError(
            f"学生数据隔离失败：list={listing.status_code}, detail={detail.status_code}"
        )
    logout(other, base_url)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--password", required=True)
    parser.add_argument("--verify-ticket", type=int)
    args = parser.parse_args()

    student = requests.Session()
    login(student, args.base_url, "student_a", args.password)

    if args.verify_ticket:
        ticket_id = args.verify_ticket
        detail = student.get(f"{args.base_url}/tickets/{ticket_id}", timeout=5)
        listing = student.get(f"{args.base_url}/tickets", timeout=5)
        if detail.status_code != 200 or "真实 HTTP 持久化报修描述" not in detail.text:
            raise RuntimeError("应用重启后未能读取原工单详情")
        if listing.status_code != 200 or f"#{ticket_id}" not in listing.text:
            raise RuntimeError("应用重启后未能在列表读取原工单")
        mode = "restart-verification"
    else:
        form = student.get(f"{args.base_url}/tickets/new", timeout=5)
        response = student.post(
            f"{args.base_url}/tickets/new",
            data={
                "csrf_token": hidden(CSRF, form.text, "CSRF Token"),
                "submission_token": hidden(SUBMISSION, form.text, "submission_token"),
                "building": "7号楼",
                "room_number": "512",
                "category": "网络",
                "description": "真实 HTTP 持久化报修描述，网络端口无法连接。",
            },
            allow_redirects=False,
            timeout=5,
        )
        location = response.headers.get("Location", "")
        match = TICKET_LOCATION.search(location)
        if response.status_code != 303 or not match:
            raise RuntimeError(f"创建工单失败：HTTP {response.status_code}, Location={location}")
        ticket_id = int(match.group(1))
        detail = student.get(f"{args.base_url}{location}", timeout=5)
        listing = student.get(f"{args.base_url}/tickets", timeout=5)
        if detail.status_code != 200 or "真实 HTTP 持久化报修描述" not in detail.text:
            raise RuntimeError("创建后的详情页与提交内容不一致")
        if listing.status_code != 200 or f"#{ticket_id}" not in listing.text:
            raise RuntimeError("创建后的列表没有显示工单")
        mode = "create"

    logout(student, args.base_url)
    assert_student_b_isolated(args.base_url, args.password, ticket_id)
    print(
        {
            "mode": mode,
            "ticket_id": ticket_id,
            "student_a_detail": 200,
            "student_b_detail": 404,
            "isolation": "passed",
        }
    )
    print("Phase 2 HTTP smoke passed")


if __name__ == "__main__":
    main()

