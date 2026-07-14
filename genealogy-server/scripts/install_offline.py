"""Download wheels from PyPI JSON API and install offline."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WHEELS = ROOT / "wheels"
PYTHON_VERSION = f"{sys.version_info.major}{sys.version_info.minor}"
PLATFORM = "win_amd64"

PACKAGES = [
    "fastapi",
    "uvicorn[standard]",
    "sqlalchemy",
    "pymysql",
    "cryptography",
    "pydantic",
    "pydantic-settings",
    "python-jose[cryptography]",
    "passlib[bcrypt]",
    "python-multipart",
    "openpyxl",
    "alembic",
    "starlette",
    "anyio",
    "annotated-doc",
    "annotated-types",
    "typing-extensions",
    "typing-inspection",
    "idna",
    "sniffio",
    "exceptiongroup",
    "pydantic-core",
    "bcrypt",
    "pyasn1",
    "rsa",
    "ecdsa",
    "cffi",
    "pycparser",
    "greenlet",
    "Mako",
    "MarkupSafe",
    "et-xmlfile",
    "click",
    "h11",
    "httptools",
    "watchfiles",
    "websockets",
    "python-dotenv",
    "colorama",
    "pyyaml",
]


def pick_wheel(urls: list[dict]) -> str | None:
    cp_tag = f"cp{PYTHON_VERSION}"
    candidates: list[tuple[int, str]] = []
    for item in urls:
        url = item["url"]
        name = item["filename"]
        if not name.endswith(".whl"):
            continue
        score = 0
        if cp_tag in name:
            score += 10
        elif "py3-none-any" in name or "py2.py3-none-any" in name:
            score += 5
        if PLATFORM in name:
            score += 20
        elif "any" in name:
            score += 1
        candidates.append((score, url))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def download_package(name: str) -> list[str]:
    api_name = name.split("[", 1)[0]
    meta_url = f"https://pypi.org/pypi/{api_name}/json"
    with urllib.request.urlopen(meta_url, timeout=60) as resp:
        data = json.load(resp)

    version = data["info"]["version"]
    files = data["releases"].get(version, [])
    downloaded: list[str] = []

    wheel_url = pick_wheel(files)
    if wheel_url:
        filename = wheel_url.rsplit("/", 1)[-1]
        target = WHEELS / filename
        if not target.exists():
            print(f"download wheel: {filename}")
            urllib.request.urlretrieve(wheel_url, target)
        downloaded.append(str(target))
        return downloaded

    for item in files:
        if item["filename"].endswith(".tar.gz"):
            filename = item["filename"]
            target = WHEELS / filename
            if not target.exists():
                print(f"download sdist: {filename}")
                urllib.request.urlretrieve(item["url"], target)
            downloaded.append(str(target))
            break
    return downloaded


def main() -> None:
    WHEELS.mkdir(exist_ok=True)
    artifacts: list[str] = []
    for pkg in PACKAGES:
        print(f"resolve: {pkg}")
        artifacts.extend(download_package(pkg))

    if not artifacts:
        raise SystemExit("no artifacts downloaded")

    pip = ROOT / ".venv" / "Scripts" / "pip.exe"
    if not pip.exists():
        raise SystemExit(f"pip not found: {pip}")

    artifacts = sorted({a for a in artifacts if Path(a).exists()})
    cmd = [str(pip), "install", "--no-index", f"--find-links={WHEELS}", *PACKAGES]
    print("install:", " ".join(cmd))
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
