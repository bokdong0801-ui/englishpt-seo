#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 9 copy-quality regression QA.

Catches page-local copy bugs that broad cross-page similarity QA does not:
- duplicate substantive paragraphs inside <main>
- duplicate h1/h2/h3 headings inside <main>
- immediately repeated sentence fragments
- known stale/garbled production tokens and template residue

Navigation/footer/modal repetition is intentionally excluded.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path

TAG_RE = re.compile(r"<[^>]+>", re.S)
MAIN_RE = re.compile(r"<main\b[^>]*>(.*?)</main>", re.S | re.I)
P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S | re.I)
H_RE = re.compile(r"<h([1-3])\b[^>]*>(.*?)</h\1>", re.S | re.I)
SCRIPT_STYLE_RE = re.compile(r"<(?:script|style)\b.*?</(?:script|style)>", re.S | re.I)

STALE_FAQ_QUESTIONS = {
    "오류가 줄었는지는 어떻게 보나요?",
    "변화는 어떻게 확인하나요?",
    "교재 진도보다 실제 상황을 먼저 보나요?",
    "수업 기록은 얼마나 자세해야 하나요?",
    "다른 상황에도 활용이 안 되면 새 표현을 더 배우나요?",
}

KNOWN_BAD = (
    "복습회수",
    "현재범위",
    "차수 차수",
    "상기 차수",
    "회상 차수",
    "기억 회수",
    "암기 차수",
    "후속 기점",
    "재검토 동작",
    "재확인 동작",
    "재확인 행동",
    "재검토 행동",
    "{{",
    "}}",
    "undefined",
    "TODO",
)

def plain(value: str) -> str:
    value = SCRIPT_STYLE_RE.sub(" ", value)
    value = TAG_RE.sub(" ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()

def issue_page(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    main_m = MAIN_RE.search(raw)
    main = main_m.group(1) if main_m else raw
    out: list[dict] = []

    bad = [token for token in KNOWN_BAD if token in main]
    if bad:
        out.append({"type": "known_bad_token", "tokens": bad})

    faq_questions = {
        plain(x) for x in re.findall(r"<summary>(.*?)</summary>", main, re.S | re.I)
    }
    stale_faq = sorted(faq_questions & STALE_FAQ_QUESTIONS)
    if stale_faq:
        out.append({"type": "stale_faq_question", "questions": stale_faq})

    paragraphs = [plain(x) for x in P_RE.findall(main)]
    substantive = [x for x in paragraphs if len(x) >= 45]
    dup_p = [x for x,n in Counter(substantive).items() if n > 1]
    if dup_p:
        out.append({"type": "duplicate_paragraph", "samples": dup_p[:5]})

    headings = [plain(x[1]) for x in H_RE.findall(main)]
    headings = [x for x in headings if len(x) >= 4]
    dup_h = [x for x,n in Counter(headings).items() if n > 1]
    if dup_h:
        out.append({"type": "duplicate_heading", "samples": dup_h[:5]})

    for p in paragraphs:
        if len(p) < 30:
            continue
        sentences = [
            re.sub(r"\s+", " ", s).strip()
            for s in re.split(r"(?<=[.!?。！？])\s+|(?<=다\.)\s*", p)
            if len(re.sub(r"\s+", " ", s).strip()) >= 16
        ]
        for a,b in zip(sentences, sentences[1:]):
            if a == b:
                out.append({"type": "adjacent_repeated_sentence", "sample": a[:180]})
                break

    # Obvious accidental doubled word, but ignore short grammatical repetitions.
    txt = plain(main)
    m = re.search(r"(?<![가-힣A-Za-z])([가-힣A-Za-z]{3,})\s+\1(?![가-힣A-Za-z])", txt)
    if m:
        out.append({"type": "doubled_word", "sample": m.group(0)})

    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--max-report", type=int, default=100)
    args = ap.parse_args()

    root = Path(args.root)
    failures = []
    checked = 0
    for path in sorted(root.glob("*.html")):
        if path.name == "404.html":
            continue
        checked += 1
        issues = issue_page(path)
        if issues:
            failures.append({"file": path.name, "issues": issues})
            if len(failures) >= args.max_report:
                break

    report = {
        "status": "PASS" if not failures else "FAIL_COPY_QUALITY",
        "checked_pages": checked,
        "failure_count": len(failures),
        "failures": failures,
    }
    Path(args.output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
