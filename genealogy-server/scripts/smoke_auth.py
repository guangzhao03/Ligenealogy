"""R1 auth integration smoke test (stdlib only)."""
from __future__ import annotations

import json
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:8000"
PASSWORD = "123456"
USERNAME = f"testuser_{int(time.time())}"


def request(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    health_req = urllib.request.Request(f"{BASE}/health")
    with urllib.request.urlopen(health_req, timeout=10) as resp:
        assert resp.status == 200
    print("[OK] health")

    reg = request(
        "POST",
        "/api/auth/register",
        {"username": USERNAME, "password": PASSWORD, "nickname": "自动测试"},
    )
    assert reg["code"] == 0, reg
    assert reg["data"]["username"] == USERNAME
    print("[OK] register")

    login = request(
        "POST",
        "/api/auth/login",
        {"username": USERNAME, "password": PASSWORD},
    )
    assert login["code"] == 0, login
    token = login["data"]["access_token"]
    assert token
    print("[OK] login")

    me = request("GET", "/api/auth/me", token=token)
    assert me["code"] == 0, me
    assert me["data"]["username"] == USERNAME
    print("[OK] me")

    dup = request("POST", "/api/auth/register", {"username": USERNAME, "password": PASSWORD})
    assert dup["code"] == 409, dup
    print("[OK] duplicate register rejected")

    print("\nALL PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
