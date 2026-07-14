"""R4 relation + R5 tree MVP smoke test."""
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
    username = f"mvp_user_{int(time.time())}"
    api("POST", "/api/auth/register", {"username": username, "password": "123456"})
    token = api("POST", "/api/auth/login", {"username": username, "password": "123456"})[
        "data"
    ]["access_token"]

    family_id = api("POST", "/api/families", {"name": "王氏家族"}, token=token)["data"]["id"]
    person_a_id = api(
        "POST",
        "/api/persons",
        {
            "family_id": family_id,
            "name": "王大明",
            "nickname": "大明",
            "gender": 1,
            "generation": 1,
            "birth_year": 1910,
        },
        token=token,
    )["data"]["id"]
    person_b_id = api(
        "POST",
        "/api/persons",
        {
            "family_id": family_id,
            "name": "王小明",
            "nickname": "小明",
            "gender": 1,
            "generation": 2,
            "birth_year": 1940,
        },
        token=token,
    )["data"]["id"]
    person_c_id = api(
        "POST",
        "/api/persons",
        {
            "family_id": family_id,
            "name": "王小华",
            "nickname": "小华",
            "gender": 1,
            "generation": 2,
            "birth_year": 1942,
        },
        token=token,
    )["data"]["id"]

    relation = api(
        "POST",
        "/api/relations",
        {
            "family_id": family_id,
            "from_person_id": person_a_id,
            "to_person_id": person_b_id,
            "relation_type": "parent",
        },
        token=token,
    )
    assert relation["code"] == 0, relation
    print("[OK] create parent relation A -> B")

    api(
        "POST",
        "/api/relations",
        {
            "family_id": family_id,
            "from_person_id": person_a_id,
            "to_person_id": person_c_id,
            "relation_type": "parent",
        },
        token=token,
    )
    print("[OK] create parent relation A -> C")

    rels = api("GET", f"/api/persons/{person_b_id}/relations", token=token)
    assert rels["code"] == 0
    assert any(p["name"] == "王大明" for p in rels["data"]["parents"])
    assert any(p["name"] == "王小华" for p in rels["data"]["siblings"])
    print("[OK] sibling derived from common parent")

    query = urllib.parse.urlencode({"family_id": family_id})
    tree = api("GET", f"/api/tree/full?{query}", token=token)
    assert tree["code"] == 0
    node_ids = {node["id"] for node in tree["data"]["nodes"]}
    assert str(person_a_id) in node_ids and str(person_b_id) in node_ids
    parent_edge = any(
        e["source"] == str(person_a_id)
        and e["target"] == str(person_b_id)
        and e["relation"] == "parent"
        for e in tree["data"]["edges"]
    )
    assert parent_edge
    print("[OK] tree/full returns G6 nodes and edges")

    anc_query = urllib.parse.urlencode(
        {"family_id": family_id, "start_generation": 2, "max_generations": 5}
    )
    ancestors = api("GET", f"/api/tree/ancestors?{anc_query}", token=token)
    assert str(person_a_id) in {n["id"] for n in ancestors["data"]["nodes"]}
    print("[OK] tree/ancestors")

    desc_query = urllib.parse.urlencode(
        {"family_id": family_id, "start_generation": 1, "max_generations": 5}
    )
    descendants = api("GET", f"/api/tree/descendants?{desc_query}", token=token)
    desc_ids = {n["id"] for n in descendants["data"]["nodes"]}
    assert str(person_b_id) in desc_ids and str(person_c_id) in desc_ids
    print("[OK] tree/descendants")

    print("\nMVP ALL PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
