#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V23.2 beginner-first copy audit. HTML-only inspection; never submits forms.

Keeps public exam names, place names, URLs, SEO metadata and official test
terminology unchanged. Reports remaining expert language without pretending that
an automated check proves a human learner understands every page.
"""
from __future__ import annotations
import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path

HUBS = ("englishpt.html", "courses.html", "student-english.html",
        "english-conversation.html", "exam-english.html")
FOUR_PHASES = ("1~3개월", "3~6개월", "6~9개월", "9~12개월")
HARD_BLOCKERS = (
    "최소 루틴", "목표 Level", "프리토킹", "과정 중심 탐색과 겹치지 않도록",
)
WARNING_WORDS = ("피드백", "레벨", "교정", "실전", "첨삭", "오답")
MEANINGFUL_ENGLISH = re.compile(r'class="change-dialogue-english"')
MEANINGFUL_KOREAN = re.compile(r'class="change-dialogue-korean"')

def visible(raw: str) -> str:
    src = raw.split("</head>", 1)[-1]
    src = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", src, flags=re.S | re.I)
    src = re.sub(r"<[^>]*>", " ", src)
    return re.sub(r"\s+", " ", html.unescape(src)).strip()

def audit(root: Path, *, source_only: bool = False):
    errors = []
    counts = Counter()
    warnings = Counter()
    examples = {}
    pages = [root/p for p in HUBS] if source_only else sorted(p for p in root.glob("*.html") if p.name!="404.html")
    for page in pages:
        if not page.exists():
            errors.append({"page":page.name,"problem":"missing"})
            continue
        raw = page.read_text(encoding="utf-8", errors="replace")
        body = visible(raw)
        counts["pages"] += 1
        for t in HARD_BLOCKERS:
            # Full standalone terms, but do not treat a similar place name as a problem.
            if t in body:
                counts["hard_blocker_uses"] += 1
                if len(errors) < 100:
                    errors.append({"page":page.name, "problem":"unclear_jargon", "term":t})
        for t in WARNING_WORDS:
            n = body.count(t)
            if n:
                warnings[t] += n
                if len(examples.get(t, [])) < 3:
                    examples.setdefault(t, []).append(page.name)
        if page.name in HUBS:
            counts["hubs"] += 1
            if 'id="applyModal"' not in raw or "data-open-form" not in raw:
                errors.append({"page":page.name,"problem":"consultation_cta_missing"})
            if "저가형 대량" in body or ">TEACHER<" in raw:
                errors.append({"page":page.name,"problem":"sales_or_english_heading_regression"})
        if page.name in ("englishpt.html", "english-conversation.html"):
            if raw.count('class="change-card"') != 4 or not all(x in raw for x in FOUR_PHASES):
                errors.append({"page":page.name, "problem":"four_change_stages_missing"})
            if len(MEANINGFUL_ENGLISH.findall(raw)) < 8 or (
                len(MEANINGFUL_ENGLISH.findall(raw)) != len(MEANINGFUL_KOREAN.findall(raw))
            ):
                errors.append({"page":page.name,"problem":"translated_dialogues_missing"})
            if 'change-note' not in raw:
                errors.append({"page":page.name,"problem":"illustrative_timeline_disclaimer_missing"})
        if page.name == "exam-english.html":
            if not all(x in body for x in ("듣기(LC)", "읽기(RC)", "Band(밴드)")):
                errors.append({"page":page.name,"problem":"exam_term_meaning_missing"})
        if page.name.endswith("-beginner-english-conv.html") and 'class="section management"' in raw:
            counts["locality_beginner_pages"] += 1
            if 'class="beginner-sample"' not in raw or raw.count('class="beginner-sample-line"') != 2:
                if len(errors) < 100:
                    errors.append({"page":page.name,"problem":"beginner_example_not_translated"})
    expected = len(HUBS) if source_only else 140391
    if counts["pages"] != expected:
        errors.append({"page":"entire-release","problem":"wrong_page_count","got":counts["pages"],"wanted":expected})
    result={
        "status":"PASS_V23_EASY_COPY_"+("SOURCE" if source_only else "FULL") if not errors else "FAIL_V23_EASY_COPY",
        "mode":"source_hubs" if source_only else "all_generated_html",
        "counts":dict(counts),
        "unexplained_jargon_warnings":dict(warnings),
        "warning_examples":examples,
        "errors":errors,
        "limitations":"Automated glossary and structure check, not a substitute for learner comprehension testing; browser visuals are a separate gate.",
    }
    return result

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--source-only",action="store_true")
    x=p.parse_args()
    report=audit(x.root,source_only=x.source_only)
    x.output.parent.mkdir(parents=True,exist_ok=True)
    x.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(report["status"],json.dumps({"counts":report["counts"],"errors":report["errors"][:10],"warnings":report["unexplained_jargon_warnings"]},ensure_ascii=False))
    if report["errors"]:raise SystemExit(1)
