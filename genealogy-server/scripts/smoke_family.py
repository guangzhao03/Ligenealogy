"""R2 family CRUD smoke test."""
from __future__ import annotations

import json
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:8000"


def api(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    username = f"family_user_{int(time.time())}"
    reg = api("POST", "/api/auth/register", {"username": username, "password": "123456"})
    assert reg["code"] == 0, reg
    login = api("POST", "/api/auth/login", {"username": username, "password": "123456"})
    token = login["data"]["access_token"]

    created = api(
        "POST",
        "/api/families",
        {"name": "张氏家族", "description": "测试家族", "origin_place": "福建"},
        token=token,
    )
    assert created["code"] == 0, created
    family_id = created["data"]["id"]
    print("[OK] create family")

    listed = api("GET", "/api/families", token=token)
    assert listed["code"] == 0 and len(listed["data"]) >= 1
    print("[OK] list families")

    detail = api("GET", f"/api/families/{family_id}", token=token)
    assert detail["data"]["name"] == "张氏家族"
    print("[OK] get family")

    updated = api(
        "PUT",
        f"/api/families/{family_id}",
        {"name": "张氏族谱"},
        token=token,
    )
    assert updated["data"]["name"] == "张氏族谱"
    print("[OK] update family")

    deleted = api("DELETE", f"/api/families/{family_id}", token=token)
    assert deleted["code"] == 0, deleted
    print("[OK] delete family")

    print("\nALL PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
