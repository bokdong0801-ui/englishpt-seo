#!/usr/bin/env python3
"""Read-only, exhaustive static HTML student-link QA for ENGLISH PT v23.4."""
import argparse
import csv
import json
import re
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

STUDENT_TEXT = re.compile(r"(?:초등|중등|고등|초등학생|중학생|고등학생|학생)\s*(?:학생)?\s*영어|(?:초등|중등|고등)\s*회화")
STUDENT_URL = re.compile(r"student[-_]english|(?:elementary|middle|high)[-_].*english|english.*[-_](?:elementary|middle|high)", re.I)
CHOICES = (
    "사직동 초등학생영어과외", "사직동 초등학생영어회화",
    "사직동 중학생영어과외", "사직동 중학생영어회화",
    "사직동 고등학생영어과외", "사직동 고등학생영어회화",
)
WORKER_PAGE = "seoul-jongno-sajikdong-worker-english-conv-academy.html"


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if attrs.get("name") and tag == "a":
            self.ids.add(attrs["name"])
        if tag == "a":
            self.current = {"href": attrs.get("href", ""), "text": [], "attrs": attrs}
            self.links.append(self.current)

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            self.current = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--json", dest="json_path", type=Path, required=True)
    ap.add_argument("--csv", dest="csv_path", type=Path, required=True)
    ap.add_argument("--expected", type=int, default=140391)
    ap.add_argument("--source-run", default="38689660290")
    ap.add_argument("--source-sha", default="a18b8901ecda7d37f65e35b15f03d579ec63c70f")
    args = ap.parse_args()
    root = args.root.resolve()
    report = {
        "version": "v23.4", "scope": "full extracted HTML; local static student navigation links",
        "source_run": args.source_run, "source_sha": args.source_sha,
        "expected_generated_pages": args.expected, "pages_scanned": 0,
        "generated_pages_scanned": 0, "pages_with_student_links": 0,
        "student_links_checked": 0, "local_targets_verified": 0,
        "external_student_links_unverified": 0, "dynamic_student_links_unverified": 0,
        "failures": 0, "warnings": 0, "failure_samples": [], "warning_samples": [],
        "issue_counts": {}, "grade_label_link_counts": {},
        "netlify_deployed": False, "production_deployed": False,
        "form_submitted": False,
        "status": "FAIL", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    counts = Counter()
    grade_counts = Counter()
    anchor_cache = {}
    args.json_path.parent.mkdir(parents=True, exist_ok=True)
    args.csv_path.parent.mkdir(parents=True, exist_ok=True)

    with args.csv_path.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=["severity", "file", "label", "href", "reason"])
        writer.writeheader()

        def add_issue(severity, page, label, href, reason):
            writer.writerow({"severity": severity, "file": page, "label": label[:180], "href": href[:1000], "reason": reason})
            report["failures" if severity == "ERROR" else "warnings"] += 1
            counts[reason] += 1
            key = "failure_samples" if severity == "ERROR" else "warning_samples"
            if len(report[key]) < 50:
                report[key].append({"file": page, "label": label[:180], "href": href[:500], "reason": reason})

        try:
            if not root.is_dir():
                raise ValueError(f"HTML root missing: {root}")
            all_pages = sorted(root.glob("*.html"))
            generated = [p for p in all_pages if p.name not in ("index.html", "404.html")]
            report["generated_pages_scanned"] = len(generated)
            if len(generated) != args.expected:
                add_issue("ERROR", "(root)", "", "", f"generated_page_count_mismatch:{len(generated)}_vs_{args.expected}")
            if not (root / "student-english.html").is_file():
                add_issue("ERROR", "(root)", "", "student-english.html", "student_hub_missing")

            def anchors_for(target):
                target = target.resolve()
                if target not in anchor_cache:
                    parser = PageLinks()
                    parser.feed(target.read_text(encoding="utf-8", errors="replace"))
                    anchor_cache[target] = parser.ids
                return anchor_cache[target]

            for page in all_pages:
                report["pages_scanned"] += 1
                try:
                    parser = PageLinks()
                    parser.feed(page.read_text(encoding="utf-8", errors="replace"))
                except Exception as e:
                    add_issue("ERROR", page.name, "", "", "html_read_or_parse_error:" + str(e))
                    continue
                student_links_in_page = 0
                for a in parser.links:
                    text = " ".join("".join(a["text"]).split())
                    href = a["href"].strip()
                    path_part = urlsplit(href).path if href else ""
                    student_related = bool(STUDENT_TEXT.search(text) or STUDENT_URL.search(path_part))
                    if not student_related:
                        continue
                    student_links_in_page += 1
                    report["student_links_checked"] += 1
                    if STUDENT_TEXT.search(text):
                        grade_counts["student_label_links"] += 1
                    if not href or href == "#" or href.startswith("javascript:"):
                        report["dynamic_student_links_unverified"] += 1
                        add_issue("WARNING", page.name, text, href, "dynamic_or_non_href_navigation_unverified")
                        continue
                    u = urlsplit(href)
                    if u.scheme or u.netloc or href.startswith(("mailto:", "tel:")):
                        report["external_student_links_unverified"] += 1
                        add_issue("WARNING", page.name, text, href, "external_student_navigation_unverified")
                        continue
                    candidate = unquote(u.path)
                    if candidate.startswith("/"):
                        target = root / candidate.lstrip("/")
                    elif candidate:
                        target = page.parent / candidate
                    else:
                        target = page
                    target = target.resolve()
                    if not target.is_relative_to(root):
                        add_issue("ERROR", page.name, text, href, "target_escapes_release_root")
                        continue
                    if target.is_dir():
                        target = target / "index.html"
                    if not target.is_file():
                        add_issue("ERROR", page.name, text, href, "missing_local_student_target")
                        continue
                    report["local_targets_verified"] += 1
                    if u.fragment and target.name == "student-english.html":
                        if unquote(u.fragment) not in anchors_for(target):
                            add_issue("ERROR", page.name, text, href, "missing_student_hub_anchor")
                if student_links_in_page:
                    report["pages_with_student_links"] += 1
                if page.name == WORKER_PAGE:
                    normalized = {"".join("".join(a["text"]).split()): a["href"] for a in parser.links}
                    for label in CHOICES:
                        match = [v for k, v in normalized.items() if "".join(label.split()) in k]
                        if not match:
                            add_issue("ERROR", page.name, label, "", "sajikdong_student_choice_link_missing")
                        elif not any(v.strip() and v.strip() != "#" and not v.startswith("javascript:") for v in match):
                            add_issue("ERROR", page.name, label, "", "sajikdong_student_choice_non_navigable")
                if report["pages_scanned"] % 20000 == 0:
                    print(f"SCAN_PROGRESS {report['pages_scanned']}/{len(all_pages)} student_links={report['student_links_checked']} failures={report['failures']}", flush=True)
        except Exception:
            add_issue("ERROR", "(scanner)", "", "", "scanner_exception:" + traceback.format_exc()[-1500:])
        finally:
            report["issue_counts"] = dict(counts)
            report["grade_label_link_counts"] = dict(grade_counts)
            report["status"] = ("PASS_V23_ALL_STUDENT_LINKS" if report["failures"] == 0
                                and report["generated_pages_scanned"] == args.expected
                                and report["pages_scanned"] >= args.expected + 2
                                else "FAIL_V23_ALL_STUDENT_LINKS")
            args.json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(report["status"], "pages", report["pages_scanned"], "student_links", report["student_links_checked"], "errors", report["failures"], "warnings", report["warnings"], flush=True)
    print("REPORT_JSON", args.json_path)
    print("REPORT_CSV", args.csv_path)
    for row in report["failure_samples"][:20]:
        print("::error file=" + row["file"] + "::" + row["reason"] + " href=" + row["href"])
    return 0 if report["status"].startswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
