"""测试指定人物族谱接口 /api/tree/person"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get("GENEALOGY_API_BASE", "http://127.0.0.1:8000")


def api(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    login = api("POST", "/api/auth/login", {"username": "admin", "password": "123456"})
    if login["code"] != 0:
        login = api("POST", "/api/auth/login", {"username": "test", "password": "123456"})
    assert login["code"] == 0, login
    token = login["data"]["access_token"]
    print("[OK] login")

    families = api("GET", "/api/families", token=token)
    assert families["code"] == 0 and families["data"], "no families"
    family = max(families["data"], key=lambda item: item["id"])
    family_id = family["id"]
    print(f"[OK] use family {family_id} ({family['name']})")

    query = urllib.parse.urlencode({"family_id": family_id, "keyword": "明远", "page": 1, "page_size": 10})
    persons = api("GET", f"/api/persons?{query}", token=token)
    assert persons["code"] == 0 and persons["data"]["items"], persons
    person = persons["data"]["items"][0]
    person_id = person["id"]
    print(f"[OK] search person: {person['name']} (id={person_id})")

    for direction in ("center", "ancestors", "descendants", "patrilineal"):
        params = urllib.parse.urlencode(
            {
                "family_id": family_id,
                "person_id": person_id,
                "direction": direction,
                "up_generations": 5,
                "down_generations": 5,
            }
        )
        tree = api("GET", f"/api/tree/person?{params}", token=token)
        assert tree["code"] == 0, tree
        data = tree["data"]
        assert data["focus_person_id"] == str(person_id), data
        assert len(data["nodes"]) > 0, f"{direction} empty nodes"
        print(f"[OK] direction={direction} nodes={len(data['nodes'])} focus={data['focus_person_id']}")

    bad = api(
        "GET",
        f"/api/tree/person?{urllib.parse.urlencode({'family_id': family_id, 'person_id': 999999, 'direction': 'center'})}",
        token=token,
    )
    assert bad["code"] != 0, "should fail for missing person"
    print("[OK] invalid person_id rejected")

    print("\nALL PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
