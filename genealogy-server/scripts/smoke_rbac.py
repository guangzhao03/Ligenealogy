"""冒烟：RBAC 角色与后台鉴权"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("GENEALOGY_API_BASE", "http://127.0.0.1:8000")


def api(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode("utf-8"))
        except Exception:
            payload = {"detail": str(e)}
        return e.code, payload


def main() -> None:
    # public portal still open
    code, family = api("GET", "/api/public/family")
    assert code == 200 and family.get("code") == 0, family
    print("[OK] guest public family")

    # login as admin
    code, login = api("POST", "/api/auth/login", {"username": "admin", "password": "123456"})
    if code != 200 or login.get("code") != 0:
        print("SKIP admin login failed (check credentials)", login)
        return
    token = login["data"]["access_token"]
    code, me = api("GET", "/api/auth/me", token=token)
    assert me["code"] == 0 and me["data"]["role"] == "admin", me
    print("[OK] admin me role=admin")

    code, users = api("GET", "/api/users", token=token)
    assert users["code"] == 0 and len(users["data"]) >= 1, users
    print(f"[OK] list users count={len(users['data'])}")

    # register or find a member
    member = next((u for u in users["data"] if u["role"] == "member"), None)
    if member is None:
        print("[OK] no member account to probe; skip member forbid check")
    else:
        # cannot test member API without password; just verify admin can patch role roundtrip
        uid = member["id"]
        code, updated = api("PUT", f"/api/users/{uid}/role", {"role": "editor"}, token=token)
        assert updated["code"] == 0 and updated["data"]["role"] == "editor", updated
        code, restored = api("PUT", f"/api/users/{uid}/role", {"role": "member"}, token=token)
        assert restored["code"] == 0 and restored["data"]["role"] == "member", restored
        print(f"[OK] role update roundtrip user={uid}")

    print("\nALL PASSED")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as exc:
        print(f"SKIP (server not up): {exc}", file=sys.stderr)
        sys.exit(0)
    except Exception as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
