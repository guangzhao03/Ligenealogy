"""R6 media upload smoke test."""
from __future__ import annotations

import json
import sys
import time
import uuid
import urllib.request
from io import BytesIO
from pathlib import Path

BASE = "http://127.0.0.1:8000"

# minimal 1x1 PNG
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def api_json(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload_file(
    token: str,
    person_id: int,
    filename: str,
    content: bytes,
    mime_type: str,
    is_avatar: bool = False,
) -> dict:
    boundary = f"----Boundary{uuid.uuid4().hex}"
    parts: list[bytes] = []

    def add_field(name: str, value: str) -> None:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8")
        )

    add_field("person_id", str(person_id))
    add_field("is_avatar", "true" if is_avatar else "false")
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
        + content
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    req = urllib.request.Request(
        f"{BASE}/api/media/upload",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    username = f"media_user_{int(time.time())}"
    api_json("POST", "/api/auth/register", {"username": username, "password": "123456"})
    token = api_json("POST", "/api/auth/login", {"username": username, "password": "123456"})[
        "data"
    ]["access_token"]

    family_id = api_json("POST", "/api/families", {"name": "陈氏家族"}, token=token)["data"]["id"]
    person_id = api_json(
        "POST",
        "/api/persons",
        {
            "family_id": family_id,
            "name": "陈小明",
            "nickname": "小明",
            "gender": 1,
            "generation": 1,
            "birth_year": 1988,
        },
        token=token,
    )["data"]["id"]

    uploaded = upload_file(token, person_id, "avatar.png", PNG_BYTES, "image/png", is_avatar=True)
    assert uploaded["code"] == 0, uploaded
    media_id = uploaded["data"]["id"]
    file_url = uploaded["data"]["url"]
    print("[OK] upload media")

    listed = api_json("GET", f"/api/persons/{person_id}/media", token=token)
    assert listed["code"] == 0 and len(listed["data"]) == 1
    print("[OK] list person media")

    person = api_json("GET", f"/api/persons/{person_id}", token=token)
    assert person["data"]["avatar_url"] == file_url
    print("[OK] avatar_url updated")

    static_req = urllib.request.Request(f"{BASE}{file_url}")
    with urllib.request.urlopen(static_req, timeout=10) as resp:
        assert resp.status == 200
        assert resp.read() == PNG_BYTES
    print("[OK] static file accessible")

    deleted = api_json("DELETE", f"/api/media/{media_id}", token=token)
    assert deleted["code"] == 0, deleted
    print("[OK] delete media")

    listed_after = api_json("GET", f"/api/persons/{person_id}/media", token=token)
    assert len(listed_after["data"]) == 0

    disk_guess = Path(__file__).resolve().parent.parent / "uploads" / str(family_id) / str(person_id)
    if disk_guess.exists():
        assert not any(disk_guess.iterdir()), "disk file should be removed"
    print("[OK] db and disk cleaned")

    print("\nALL PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)
