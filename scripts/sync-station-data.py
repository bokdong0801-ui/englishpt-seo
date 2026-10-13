#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync a normalized nationwide station index used by ENGLISH PT.

The station names/line ordering come from a public station index page.
Geographic metadata is enriched from a pinned public station dataset when
available. Only factual station metadata is retained; no third-party prose is
copied.
"""
from __future__ import annotations

import ast
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "stations.json"
INDEX_URL = "https://e-english.kr/sub"
META_URL = "https://gist.githubusercontent.com/lacti/f0d1a0915a32697fe3cf8f7997e18c52/raw/4a71b4b16ee2a25737acd1fdc595b7b8824a0dd1/korean-subway-station-list.json5"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "EnglishPT-StationSync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def load_geo_meta() -> dict[str, dict]:
    raw = fetch(META_URL)
    raw = re.sub(r"//.*", "", raw)
    rows = ast.literal_eval(raw)
    out: dict[str, dict] = {}
    for row in rows:
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        item = out.setdefault(name, {
            "city": row.get("city"),
            "areas": set(),
            "lines": set(),
            "lat": row.get("lat"),
            "lng": row.get("lng"),
        })
        item["areas"].update(row.get("areas") or [])
        item["lines"].update(row.get("lines") or [])
        if item.get("lat") is None and row.get("lat") is not None:
            item["lat"] = row.get("lat")
        if item.get("lng") is None and row.get("lng") is not None:
            item["lng"] = row.get("lng")
    return out


def main() -> int:
    html = fetch(INDEX_URL)
    soup = BeautifulSoup(html, "html.parser")
    geo = load_geo_meta()

    lines: list[dict] = []
    stations: dict[str, dict] = {}

    for label in soup.select("div.sido"):
        label_text = " ".join(label.stripped_strings)
        m = re.fullmatch(r"(.+?)\s*\((\d+)\)", label_text)
        if not m:
            continue
        line_name = m.group(1).strip()
        grid = label.find_next_sibling("div", class_="grid")
        if not grid:
            continue
        ordered = []
        for a in grid.find_all("a", href=True):
            href = a.get("href", "")
            name = " ".join(a.stripped_strings).strip()
            if not re.fullmatch(r"/sub-[a-z0-9-]+", href) or not name.endswith("역"):
                continue
            slug = href[len("/sub-"):]
            ordered.append(slug)
            item = stations.setdefault(slug, {
                "name": name,
                "slug": slug,
                "lines": [],
                "city": None,
                "areas": [],
                "lat": None,
                "lng": None,
            })
            if item["name"] != name:
                raise RuntimeError(f"slug collision: {slug}: {item['name']} != {name}")
            if line_name not in item["lines"]:
                item["lines"].append(line_name)
        if ordered:
            lines.append({"name": line_name, "stations": ordered})

    if len(stations) != 911:
        raise RuntimeError(f"expected 911 unique stations, got {len(stations)}")
    if len(lines) != 37:
        raise RuntimeError(f"expected 37 lines, got {len(lines)}")
    if "dobongsan" not in stations or stations["dobongsan"]["name"] != "도봉산역":
        raise RuntimeError("dobongsan station missing")

    for item in stations.values():
        g = geo.get(item["name"])
        if not g:
            continue
        item["city"] = g.get("city")
        item["areas"] = sorted(g.get("areas") or [])
        item["lat"] = g.get("lat")
        item["lng"] = g.get("lng")
        for line in sorted(g.get("lines") or []):
            if line not in item["lines"]:
                item["lines"].append(line)

    # Nearby stations are based on adjacency in each line, never guessed from city names.
    line_pos = {line["name"]: line["stations"] for line in lines}
    for item in stations.values():
        nearby: list[str] = []
        for line_name in item["lines"]:
            ordered = line_pos.get(line_name)
            if not ordered or item["slug"] not in ordered:
                continue
            idx = ordered.index(item["slug"])
            for j in range(max(0, idx - 3), min(len(ordered), idx + 4)):
                slug = ordered[j]
                if slug != item["slug"] and slug not in nearby:
                    nearby.append(slug)
        item["nearby"] = nearby[:12]

    payload = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "station_count": len(stations),
        "line_count": len(lines),
        "sources": {
            "station_index": INDEX_URL,
            "geo_metadata": META_URL,
        },
        "lines": lines,
        "stations": sorted(stations.values(), key=lambda x: x["name"]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS_STATION_SYNC",
        "station_count": payload["station_count"],
        "line_count": payload["line_count"],
        "geo_enriched": sum(1 for x in payload["stations"] if x["city"]),
        "dobongsan": next(x for x in payload["stations"] if x["slug"] == "dobongsan"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
