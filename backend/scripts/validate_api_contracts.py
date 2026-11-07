from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"


def normalize_path(path: str) -> str:
    cleaned = path.split("?", 1)[0]
    cleaned = re.sub(r"\$\{encodeURIComponent\(([^}]+)\)\}", "/{param}", cleaned)
    cleaned = re.sub(r"\$\{[^}]+\}", "/{param}", cleaned)
    cleaned = re.sub(r"/\{[A-Za-z_]+\}", "/{param}", cleaned)
    cleaned = re.sub(r"/{2,}", "/", cleaned)
    cleaned = re.sub(r"/+$", "", cleaned)
    return cleaned or "/"


def get_backend_routes() -> set[str]:
    routes: set[str] = set()
    for api_file in (BACKEND_DIR / "app" / "api").glob("*.py"):
        content = api_file.read_text(encoding="utf-8")
        prefix_match = re.search(r"APIRouter\((.*?)\)", content, re.S)
        prefix = "/"
        if prefix_match:
            prefix_match_text = prefix_match.group(1)
            prefix_value_match = re.search(r"prefix\s*=\s*['\"]([^'\"]+)['\"]", prefix_match_text)
            if prefix_value_match:
                prefix = prefix_value_match.group(1)

        for match in re.finditer(r"@router\.(get|post|put|patch|delete)\((.*?)\)", content, re.S):
            path_part = match.group(2)
            string_match = re.search(r'["\']([^"\']*)["\']', path_part)
            if not string_match:
                continue
            raw_path = string_match.group(1)
            full_path = prefix.rstrip("/") + "/" + raw_path.lstrip("/")
            routes.add(normalize_path(full_path))
    return routes


def get_frontend_routes() -> set[str]:
    routes: set[str] = set()
    for api_file in (FRONTEND_DIR / "src" / "api").glob("*.ts"):
        content = api_file.read_text(encoding="utf-8")
        for match in re.finditer(r"apiRequest(?:<[^>]+>)?\(\s*['\"]([^'\"]+)['\"]", content):
            raw_path = match.group(1)
            routes.add(normalize_path(raw_path))
    return routes


def main() -> None:
    backend_routes = get_backend_routes()
    frontend_routes = get_frontend_routes()

    missing = sorted(
        route for route in frontend_routes if route not in backend_routes
    )

    if missing:
        raise SystemExit(
            "Frontend API routes missing from the backend contract:\n"
            + "\n".join(f" - {route}" for route in missing)
        )

    print(f"Validated {len(frontend_routes)} frontend route calls against {len(backend_routes)} backend routes.")


if __name__ == "__main__":
    main()
