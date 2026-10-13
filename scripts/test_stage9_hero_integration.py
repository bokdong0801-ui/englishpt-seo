#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration smoke: render real station×course pages with new audience Hero."""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("station_hero_integration", ROOT / "scripts/stage9-station-renderer.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
data = json.loads((ROOT / "data/stations.json").read_text(encoding="utf-8"))
station = data["stations"][0]
station_map = {x["slug"]: x for x in data["stations"]}
samples = [
    "beginner-english-conv", "elem-tutor", "high-conv",
    "biz-business-conv", "worker-english-conv-academy",
    "toeic", "ielts-academy", "univ-conv", "jobseeker-conv",
]
for intent in samples:
    raw, problems = module.render_station_course(station, intent, station_map)
    assert not problems, f"{intent}: {problems}"
    assert 'data-hero-copy="audience-v2"' in raw, intent
    assert 'class="hero-next-grid"' in raw, intent
    assert raw.count('href="#consultation-preview"') >= 1, intent
    assert 'name="englishpt-consultation"' in raw, intent
    assert 'href="/assets/styles.css"' not in raw or '<link' in raw
    assert len(re.findall(r"<h1\b", raw)) == 1, intent
    if intent == "beginner-english-conv":
        visible = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", raw, flags=re.I | re.S)
        for term in ("훈련", "진단", "실전", "교정", "병목", "재점검", "재검증"):
            assert term not in visible, (intent, term)
hub = module.station_hub(station, station_map)
assert 'class="section soft hero-entry-panel"' in hub
for intent in ("elem-tutor", "beginner-english-conv", "worker-english-conv-academy", "toeic"):
    assert f'/station-{station["slug"]}-{intent}.html' in hub, intent
print("PASS_REAL_STATION_HERO_INTEGRATION", station["slug"], len(samples), "intents")
