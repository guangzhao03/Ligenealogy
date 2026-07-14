"""Download wheels using PowerShell Invoke-WebRequest (works when pip SSL fails)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WHEELS = ROOT / "wheels"
PYTHON_VERSION = f"{sys.version_info.major}{sys.version_info.minor}"
PLATFORM = "win_amd64"

PACKAGES = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "pymysql",
    "cryptography",
    "pydantic",
    "pydantic-settings",
    "python-jose",
    "passlib",
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
    candidates: list[tuple[int, str, str]] = []
    for item in urls:
        url = item["url"]
        name = item["filename"]
        if not name.endswith(".whl"):
            continue
        score = 0
        if cp_tag in name:
            score += 10
        elif "abi3" in name:
            score += 8
        elif "py3-none-any" in name or "py2.py3-none-any" in name:
            score += 5
        if PLATFORM in name:
            score += 20
        elif "any" in name:
            score += 1
        candidates.append((score, url, name))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def download_with_powershell(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        f"Invoke-WebRequest -Uri '{url}' -OutFile '{target}' -UseBasicParsing",
    ]
    subprocess.check_call(cmd)


def fetch_json(url: str) -> dict:
    tmp = WHEELS / "_tmp_meta.json"
    download_with_powershell(url, tmp)
    data = json.loads(tmp.read_text(encoding="utf-8"))
    tmp.unlink(missing_ok=True)
    return data


def download_package(name: str) -> None:
    api_name = name.split("[", 1)[0]
    data = fetch_json(f"https://pypi.org/pypi/{api_name}/json")
    version = data["info"]["version"]
    files = data["releases"].get(version, [])
    wheel_url = pick_wheel(files)
    if not wheel_url:
        print(f"skip (no wheel): {name}")
        return
    filename = wheel_url.rsplit("/", 1)[-1]
    target = WHEELS / filename
    if target.exists():
        print(f"exists: {filename}")
        return
    print(f"download: {filename}")
    download_with_powershell(wheel_url, target)


def main() -> None:
    WHEELS.mkdir(exist_ok=True)
    for pkg in PACKAGES:
        download_package(pkg)

    pip = ROOT / ".venv" / "Scripts" / "pip.exe"
    install_targets = [
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
    ]
    cmd = [str(pip), "install", "--no-index", f"--find-links={WHEELS}", *install_targets]
    print("install:", " ".join(cmd))
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
