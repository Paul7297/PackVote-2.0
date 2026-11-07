from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def normalize_path(path: str) -> str:
    cleaned = path.split("?", 1)[0]
    cleaned = re.sub(r"\$\{encodeURIComponent\(([^}]+)\)\}", "/{param}", cleaned)
    cleaned = re.sub(r"\$\{[^}]+\}", "/{param}", cleaned)
    cleaned = re.sub(r"/\{[A-Za-z_]+\}", "/{param}", cleaned)
    cleaned = re.sub(r"/{2,}", "/", cleaned)
    cleaned = re.sub(r"/+$", "", cleaned)
    return cleaned or "/"


def test_backend_and_frontend_route_contracts_match():
    backend_routes = set()
    for path in (ROOT / "app" / "api").glob("*.py"):
        content = path.read_text(encoding="utf-8")
        prefix_match = re.search(r"APIRouter\((.*?)\)", content, re.S)
        prefix = "/"
        if prefix_match:
            prefix_value_match = re.search(r"prefix\s*=\s*['\"]([^'\"]+)['\"]", prefix_match.group(1))
            if prefix_value_match:
                prefix = prefix_value_match.group(1)

        for match in re.finditer(r"@router\.(get|post|put|patch|delete)\((.*?)\)", content, re.S):
            path_part = match.group(2)
            string_match = re.search(r'["\']([^"\']*)["\']', path_part)
            if string_match:
                raw_path = string_match.group(1)
                full_path = prefix.rstrip("/") + "/" + raw_path.lstrip("/")
                backend_routes.add(normalize_path(full_path))

    frontend_routes = set()
    for path in (ROOT.parent / "frontend" / "src" / "api").glob("*.ts"):
        content = path.read_text(encoding="utf-8")
        for match in re.finditer(r"apiRequest(?:<[^>]+>)?\(\s*['\"]([^'\"]+)['\"]", content):
            frontend_routes.add(normalize_path(match.group(1)))

    missing = sorted(route for route in frontend_routes if route not in backend_routes)
    assert not missing, f"Missing backend route matches: {missing}"
