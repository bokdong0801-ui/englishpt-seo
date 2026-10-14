#!/usr/bin/env python3
"""V23 read-only content/CTA integrity audit. Never submits consultation forms."""
import argparse
import json
import re
from pathlib import Path

REPRESENTATIVE = (
    "englishpt.html",
    "student-english.html",
    "english-conversation.html",
    "exam-english.html",
    "seoul-jongno-sajikdong-beginner-english-conv.html",
    "seoul-jongno-sajikdong-toeic.html",
    "seoul-jongno-sajikdong-ielts.html",
    "daegu-dalseo-songhyeondong-toeic.html",
    "station-gangnam.html",
    "station-amsayeoksagongwon.html",
    "seoul-jongno-sajikdong-worker-english-conv-academy.html",
)
STALE = (
    "배운 내용을 실제로 다시 써볼 수 있게 수업 전후를 연결합니다",
    "수업 전후를 연결합니다",
)

def audit(root: Path, *, expected_total: int = 140391) -> dict:
    files = sorted(p for p in root.glob("*.html") if p.name != "404.html")
    names = {p.name for p in files}
    errors = []
    stats = {"examined": 0, "aftercare": 0, "consultation_targets": 0,
             "modal_triggers": 0, "record_examples": 0}
    def error(name: str, cause: str):
        if len(errors) < 150:
            errors.append({"file": name, "reason": cause})
    for missing in set(REPRESENTATIVE) - names:
        error(missing, "representative_missing")
    if expected_total and len(files) != expected_total:
        error("release", f"html_count:{len(files)}_expected:{expected_total}")
    for p in files:
        raw = p.read_text(encoding="utf-8", errors="replace")
        name = p.name
        stats["examined"] += 1
        if "<main" not in raw or "</main>" not in raw:
            error(name, "main_markup_missing")
        for sentence in STALE:
            if sentence in raw:
                error(name, "obsolete_management_copy")
        # A page must not invite consultation through a dead #anchor.
        if 'href="#consultation-preview"' in raw:
            stats["consultation_targets"] += 1
            if not re.search(r'id=["\']consultation-preview["\']', raw):
                error(name, "cta_target_not_found")
        if "data-open-form" in raw:
            stats["modal_triggers"] += 1
            if 'id="applyModal"' not in raw:
                error(name, "cta_modal_not_found")
        if name not in {"stations.html"}:
            found_aftercare = ('class="manage-aftercare"' in raw or
                              'data-v23-aftercare="true"' in raw)
            if found_aftercare:
                stats["aftercare"] += 1
            else:
                error(name, "aftercare_missing")
            if "<section class=\"final\">" in raw:
                marker = raw.find('class="manage-aftercare"')
                if marker < 0:
                    marker = raw.find('data-v23-aftercare="true"')
                if marker >= raw.find('<section class="final">'):
                    error(name, "aftercare_after_final_cta")
        if name in {"englishpt.html", "english-conversation.html"}:
            phases = ("1~3개월", "3~6개월", "6~9개월", "9~12개월")
            if any(raw.count(x) < 1 for x in phases):
                error(name, "four_duration_phases_missing")
            positions = [raw.find(x, raw.find('class="change-grid')) for x in phases]
            if any(x < 0 for x in positions) or positions != sorted(positions):
                error(name, "duration_phase_order_wrong")
            if raw.count('<article class="change-card">') != 4:
                error(name, "four_change_cards_expected")
            if "학습 과정 예시" not in raw:
                error(name, "illustrative_label_missing")
            if "개인" not in raw or ("보장" not in raw and "달라지" not in raw):
                error(name, "duration_disclaimer_missing")
        if name == "englishpt.html":
            if "/student-english.html" not in raw or "/exam-english.html" not in raw:
                error(name, "other_audiences_links_missing")
        if name == "seoul-jongno-sajikdong-beginner-english-conv.html":
            m = re.search(
                r'<p class="kicker">수업 기록 예시</p>.*?<div class="grid4">(.*?)</div>',
                raw, flags=re.S)
            if not m:
                error(name, "record_examples_section_missing")
            else:
                count = m.group(1).count('<article class="card">')
                stats["record_examples"] = count
                if count != 4:
                    error(name, f"record_count:{count}")
                for i in range(1, 5):
                    if not re.search(r"예시\s*" + str(i), m.group(1)):
                        error(name, f"record_label_missing:{i}")
    report = {
        "status": "PASS_V23_CONTENT_CTA_SOURCE" if not errors else "FAIL_V23_CONTENT_CTA_SOURCE",
        "scope": "generated HTML only; no actual browser, HTTP, mail or form submissions",
        "counts": stats,
        "errors": errors,
    }
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-total", type=int, default=140391)
    args = parser.parse_args()
    report = audit(args.root, expected_total=args.expected_total)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["status"], json.dumps(report["counts"], ensure_ascii=False))
    if report["errors"]:
        print(json.dumps(report["errors"][:10], ensure_ascii=False))
        raise SystemExit(1)
