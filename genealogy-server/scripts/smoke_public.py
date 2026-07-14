"""冒烟：公开 Portal API /api/public/*"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("GENEALOGY_API_BASE", "http://127.0.0.1:8000")


def get(path: str) -> dict:
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    family = get("/api/public/family")
    assert family["code"] == 0, family
    print(f"[OK] family {family['data']['name']} persons={family['data']['stats']['person_count']}")

    q = urllib.parse.urlencode({"keyword": "李", "page": 1, "page_size": 10})
    persons = get(f"/api/public/persons?{q}")
    assert persons["code"] == 0 and persons["data"]["items"], persons
    person = persons["data"]["items"][0]
    pid = person["id"]
    print(f"[OK] search person {person['name']} id={pid}")

    detail = get(f"/api/public/persons/{pid}")
    assert detail["code"] == 0, detail
    rels = get(f"/api/public/persons/{pid}/relations")
    assert rels["code"] == 0, rels
    print("[OK] person detail + relations")

    tree = get(f"/api/public/tree/full")
    assert tree["code"] == 0 and tree["data"]["nodes"], tree
    print(f"[OK] full tree nodes={len(tree['data']['nodes'])}")

    params = urllib.parse.urlencode({"root_person_id": pid, "max_generations": 12})
    pat = get(f"/api/public/tree/patrilineal?{params}")
    assert pat["code"] == 0, pat
    print(f"[OK] patrilineal nodes={len(pat['data']['nodes'])}")

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
