from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL_LIST = ROOT / "sitemap_95_urls.txt"
THEME_MANIFEST = ROOT / "theme_manifest_v3.json"

THEME_DATA: dict = {}

TARGET_THEME_BY_TOKEN = {
    "elem": "elem",
    "mid": "mid",
    "high": "high",
    "univ": "univ",
    "jobseeker": "job",
    "biz": "worker",
    "adult": "adult",
    "housewife": "housewife",
    "senior": "senior",
    "intl": "intl",
}

# These paths belonged to the retired DB-entity public site direction.
FORBIDDEN_PUBLIC_DIRS = ["region", "station", "newtown", "district", "search"]
FORBIDDEN_TITLE_PATTERNS = [
    r"법정동\s*(안내|목록|정보)",
    r"행정동\s*(안내|목록|정보)",
    r"공식코드",
    r"지역\s*DB",
    r"지역\s*데이터",
]


def fail(message: str) -> None:
    print(f"[service-site-guard] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_one(pattern: str, text: str, label: str, path: Path) -> str:
    matches = re.findall(pattern, text, flags=re.I | re.S)
    if len(matches) != 1:
        fail(f"{path.name}: expected exactly one {label}, found {len(matches)}")
    value = matches[0] if isinstance(matches[0], str) else matches[0][0]
    return re.sub(r"\s+", " ", value).strip()


def load_theme_manifest() -> dict:
    if not THEME_MANIFEST.exists():
        fail("theme_manifest_v3.json is missing")
    try:
        return json.loads(read(THEME_MANIFEST))
    except json.JSONDecodeError as exc:
        fail(f"theme_manifest_v3.json is invalid JSON: {exc}")


def expected_theme_class(path: Path, manifest: dict) -> str | None:
    name = path.name
    for token, theme_key in TARGET_THEME_BY_TOKEN.items():
        if f"-{token}-" in name:
            theme = manifest.get("themes", {}).get(theme_key, {})
            return theme.get("body_class")
    if name == "dalseo-songhyeondong.html":
        return "theme-local"
    return None


def validate_theme_contract(path: Path, text: str, title: str, h1: str, manifest: dict) -> None:
    body_match = re.search(r"<body\b[^>]*class=[\"']([^\"']+)[\"']", text, flags=re.I)
    if not body_match:
        fail(f"{path.name}: body class is missing")
    classes = set(body_match.group(1).split())

    expected = expected_theme_class(path, manifest)
    if expected and expected not in classes:
        fail(f"{path.name}: expected audience theme {expected}, found {sorted(classes)}")

    audience_classes = {
        theme.get("body_class")
        for key, theme in manifest.get("themes", {}).items()
        if key not in {"generic"} and theme.get("body_class")
    }

    if "page-role-region" in classes:
        conflicting = sorted(classes.intersection(audience_classes))
        if conflicting:
            fail(f"{path.name}: region page cannot use audience theme(s): {conflicting}")
        if "theme-local" not in classes:
            fail(f"{path.name}: region page must use theme-local")
        plain_h1 = re.sub(r"<[^>]+>", "", h1)
        if "영어" not in title or "영어" not in plain_h1:
            fail(f"{path.name}: region page must still express an English-service intent")

    if "intent-audience" in classes and "theme-local" in classes:
        fail(f"{path.name}: audience service page cannot use only the neutral region theme")


def validate_html(path: Path) -> None:
    text = read(path)
    title = extract_one(r"<title>(.*?)</title>", text, "title", path)
    extract_one(r"<h1\b[^>]*>(.*?)</h1>", text, "H1", path)
    extract_one(r"<link\b[^>]*rel=[\"']canonical[\"'][^>]*href=[\"']([^\"']+)[\"'][^>]*>", text, "canonical", path)

    plain_title = re.sub(r"<[^>]+>", "", title)
    for pattern in FORBIDDEN_TITLE_PATTERNS:
        if re.search(pattern, plain_title, flags=re.I):
            fail(f"{path.name}: forbidden region-information title detected: {plain_title}")

    # DB internals must never become user-facing page headings/labels.
    visible_db_tokens = ["place_id", "parent_place_id", "official_code", "relation_type"]
    for token in visible_db_tokens:
        if re.search(rf">\s*{re.escape(token)}\s*<", text, flags=re.I):
            fail(f"{path.name}: visible DB token detected: {token}")

    if "FAQPage" in text:
        fail(f"{path.name}: FAQPage schema is disabled by project policy")

    validate_theme_contract(path, text, title, h1, THEME_DATA)


def main() -> None:
    global THEME_DATA
    print("[service-site-guard] ENGLISH PT service-first validation")
    THEME_DATA = load_theme_manifest()

    if not URL_LIST.exists():
        fail("sitemap_95_urls.txt is missing")

    listed = [line.strip() for line in read(URL_LIST).splitlines() if line.strip()]
    if len(listed) < 95:
        fail(f"expected preserved service baseline >= 95 URLs, found {len(listed)}")

    for public_dir in FORBIDDEN_PUBLIC_DIRS:
        path = ROOT / public_dir
        if path.exists():
            html_count = sum(1 for _ in path.rglob("*.html"))
            if html_count:
                fail(f"retired public DB directory exists: /{public_dir}/ ({html_count} html files)")

    checked = 0
    for url in listed:
        if not url.startswith("/") or not url.endswith(".html"):
            fail(f"invalid preserved URL entry: {url}")
        path = ROOT / url.lstrip("/")
        if not path.exists():
            fail(f"preserved page is missing: {url}")
        validate_html(path)
        checked += 1

    local_hub = ROOT / "dalseo-songhyeondong.html"
    if not local_hub.exists():
        fail("Songhyeondong local service hub is missing")
    hub_text = read(local_hub)
    if "영어회화" not in hub_text or "영어과외" not in hub_text:
        fail("Songhyeondong hub no longer expresses the English service intent")

    print(f"[service-site-guard] PASS: {checked} preserved service URLs validated")
    print("[service-site-guard] DB-entity public generation remains disabled")


if __name__ == "__main__":
    main()
