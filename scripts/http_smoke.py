"""Run a small real-HTTP Phase 1 smoke test against an already running server."""
from __future__ import annotations

import argparse
import re

import requests


TOKEN = re.compile(r'name="csrf_token"[^>]*value="([^"]+)"')


def csrf(html: str) -> str:
    match = TOKEN.search(html)
    if not match:
        raise RuntimeError("页面中没有找到 CSRF Token")
    return match.group(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    session = requests.Session()
    home = session.get(f"{args.base_url}/", timeout=5)
    health = session.get(f"{args.base_url}/health", timeout=5)
    login_page = session.get(f"{args.base_url}/login", timeout=5)
    login = session.post(
        f"{args.base_url}/login",
        data={
            "username": args.username,
            "password": args.password,
            "csrf_token": csrf(login_page.text),
        },
        allow_redirects=False,
        timeout=5,
    )
    portal = session.get(f"{args.base_url}/portal", timeout=5)
    logout = session.post(
        f"{args.base_url}/logout",
        data={"csrf_token": csrf(portal.text)},
        allow_redirects=False,
        timeout=5,
    )
    after_logout = session.get(f"{args.base_url}/portal", allow_redirects=False, timeout=5)

    results = {
        "home": home.status_code,
        "health": health.status_code,
        "login_page": login_page.status_code,
        "login": login.status_code,
        "portal": portal.status_code,
        "logout": logout.status_code,
        "after_logout": after_logout.status_code,
    }
    expected = {
        "home": 200,
        "health": 200,
        "login_page": 200,
        "login": 303,
        "portal": 200,
        "logout": 303,
        "after_logout": 302,
    }
    print(results)
    if results != expected:
        raise SystemExit(f"HTTP smoke failed; expected {expected}")
    print("HTTP smoke passed")


if __name__ == "__main__":
    main()
