"""R3 person CRUD smoke test."""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
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
    username = f"person_user_{int(time.time())}"
    login = api("POST", "/api/auth/register", {"username": username, "password": "123456"})
    assert login["code"] == 0, login
    token = api("POST", "/api/auth/login", {"username": username, "password": "123456"})[
        "data"
    ]["access_token"]

    family = api("POST", "/api/families", {"name": "李氏家族"}, token=token)
    family_id = family["data"]["id"]

    person_a = api(
        "POST",
        "/api/persons",
        {
            "family_id": family_id,
            "name": "李大明",
            "nickname": "大明",
            "gender": 1,
            "generation": 1,
            "birth_year": 1920,
            "birthplace": "福建",
            "is_alive": 1,
        },
        token=token,
    )
    assert person_a["code"] == 0, person_a
    person_a_id = person_a["data"]["id"]
    print("[OK] create person A")

    person_b = api(
        "POST",
        "/api/persons",
        {
            "family_id": family_id,
            "name": "李小明",
            "nickname": "小明",
            "gender": 1,
            "generation": 2,
            "birth_year": 1950,
            "is_alive": 1,
        },
        token=token,
    )
    person_b_id = person_b["data"]["id"]
    print("[OK] create person B")

    query = urllib.parse.urlencode(
        {"family_id": family_id, "keyword": "李", "generation": 1}
    )
    listed = api("GET", f"/api/persons?{query}", token=token)
    assert listed["code"] == 0 and listed["data"]["total"] >= 1
    assert any(item["name"] == "李大明" for item in listed["data"]["items"])
    print("[OK] list persons with filters")

    detail = api("GET", f"/api/persons/{person_a_id}", token=token)
    assert detail["data"]["name"] == "李大明"
    print("[OK] get person")

    updated = api(
        "PUT",
        f"/api/persons/{person_a_id}",
        {"remark": "始祖", "biography": "开基祖"},
        token=token,
    )
    assert updated["data"]["remark"] == "始祖"
    print("[OK] update person")

    deleted = api("DELETE", f"/api/persons/{person_b_id}", token=token)
    assert deleted["code"] == 0, deleted
    print("[OK] delete person")

    print("\nALL PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
