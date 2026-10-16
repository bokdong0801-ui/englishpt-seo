#!/usr/bin/env python3
"""v23.5 existing immutable Draft: read-only live HTTP, in-use OG & student navigation QA.

Do not download a 140,391-page source release, deploy to Netlify, or submit a form.
Uses an already-published Draft, the immutable original live QA artifact and
the exact 29 PNG templates created by the v23.4 square-safe OG renderer.
Old unreferenced legacy PNGs are deliberately excluded from OG:IMAGE validation.
"""
import ast
import html
import json
import re
import struct
import sys
import time
import traceback
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

OUT = Path("draft-recheck-report")
INPUT = Path("prior-live-qa")
DRAFT_HOST_SUFFIX = "--englishpt-final-ia-review-bokdong.netlify.app"
RUN_ID = 38845014645
EXPECTED_SOURCE_SHA = "a18b8901ecda7d37f65e35b15f03d579ec63c70f"
CHOICES = [
    "초등학생영어과외", "중학생영어과외", "고등학생영어과외",
    "초등학생영어회화", "중학생영어회화", "고등학생영어회화"
]
HUB_IDS = [
    "elementary-tutor", "middle-tutor", "high-tutor",
    "elementary", "middle", "high"
]
STUDENT_GROUP = re.compile(
    r'<article class="related-group"><h3>학생 영어</h3>'
    r'<div class="related-course-links">(.*?)</div></article>',
    re.S
)
LINK_TAG = re.compile(r'<a\b[^>]*>.*?</a>', re.I | re.S)
HEAD = re.compile(r'<head\b[^>]*>(.*?)</head>', re.I | re.S)


class TagParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.attrs = {}
        self.ids = set()
        self.meta = []

    def handle_starttag(self, tag, attrs):
        d = {k.lower(): v for k, v in attrs}
        if not self.attrs and tag == "a":
            self.attrs = d
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "meta":
            self.meta.append(d)


def meta_values(document, prop, key="property"):
    parser = TagParser()
    head_match = HEAD.search(document)
    parser.feed(head_match.group(1) if head_match else document[:120000])
    return [m.get("content", "") for m in parser.meta if m.get(key) == prop]


def fetch(url, attempts=3):
    last = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "ENGLISHPT-v235-immutable-preview-QA-only",
                              "Accept": "*/*"})
            with urllib.request.urlopen(request, timeout=35) as response:
                data = response.read()
                return response.status, data, response.url, dict(response.headers)
        except Exception as exc:
            last = exc
            if attempt < attempts - 1:
                time.sleep(1.7 * (attempt + 1))
    raise last


def guard_draft(url):
    parts = urlsplit(url)
    if (parts.scheme != "https" or
            not (parts.hostname or "").endswith(DRAFT_HOST_SUFFIX) or
            (parts.hostname or "").startswith(("englishpt.kr", "www.englishpt.kr"))):
        raise ValueError("Outside isolated Netlify Draft: " + url)
    return url


def require_noindex(headers, url):
    lower = {str(k).lower(): str(v) for k, v in headers.items()}
    found = lower.get("x-robots-tag", "")
    if "noindex" not in found.lower():
        raise ValueError("Draft noindex header missing: " + url)


def get_og_template_names():
    source = Path("scripts/v23_4_og_landscape_all_pages.py")
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    for node in tree.body:
        if (isinstance(node, ast.Assign) and
                any(isinstance(t, ast.Name) and t.id == "CATS" for t in node.targets)):
            categories = ast.literal_eval(node.value)
            names = [item[0] + ".png" for item in categories]
            if len(names) != 29 or len(set(names)) != 29:
                raise ValueError("Expected 29 unique v23.4 square-safe OG designs")
            return names
    raise ValueError("Cannot identify approved OG template list")


def validate_six_navigation(html_text, page_url, draft, result, cached):
    match = STUDENT_GROUP.search(html_text)
    if not match:
        raise ValueError("Student 6-card group missing from live Sajikdong page")
    anchors = LINK_TAG.findall(match.group(1))
    if len(anchors) != 6:
        raise ValueError(f"Student six-card count mismatch: {len(anchors)}")
    for index, raw in enumerate(anchors):
        label = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        label = " ".join(label.split())
        required_label = "사직동 " + CHOICES[index]
        if required_label not in label:
            raise ValueError(f"Student choice {index}: {required_label} not in {label!r}")
        parser = TagParser()
        parser.feed(raw)
        href = (parser.attrs.get("href") or "").strip()
        if not href or href in ("#", "javascript:void(0)"):
            raise ValueError(f"Student choice {index} has no usable href: {href!r}")
        destination = guard_draft(urljoin(page_url, href))
        parts = urlsplit(destination)
        if not parts.path.startswith("/") or not parts.path.endswith(
                (".html", "-tutor", "student-english", "-conv")):
            raise ValueError(f"Unexpected student destination path: {href!r}")
        expected_anchor = HUB_IDS[index]
        if index >= 1 and parts.fragment != expected_anchor:
            raise ValueError(f"Wrong tutoring/conversation grade anchor: {href!r}")
        target_no_fragment = destination.split("#", 1)[0]
        if target_no_fragment not in cached:
            status, raw_content, redirected_to, headers = fetch(target_no_fragment)
            require_noindex(headers, target_no_fragment)
            if status != 200:
                raise ValueError(f"Student page non-200: {href!r} {status}")
            parser_target = TagParser()
            parser_target.feed(raw_content.decode("utf-8", "replace"))
            if "<h1" not in raw_content.decode("utf-8", "replace").lower():
                raise ValueError(f"Student destination has no H1: {href!r}")
            cached[target_no_fragment] = parser_target.ids
        if parts.fragment and parts.fragment not in cached[target_no_fragment]:
            raise ValueError(f"Student fragment anchor missing: {href!r}")
        result["student_links"].append({
            "choice": required_label, "href": href,
            "validated_url": destination, "status": "PASS_HTTP_200"
        })
        print("V235_NAV_LINK_PASS", index + 1, href, flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "RUNNING",
        "version": "v23.5",
        "recheck_mode": "EXISTING_DRAFT_ONLY_NO_UPLOAD",
        "original_deploy_run": RUN_ID,
        "source_run": 38689660290,
        "source_sha": EXPECTED_SOURCE_SHA,
        "offline_all_page_preflight_run": 38843408620,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "http_pages_passed": 0,
        "og_images_passed": 0,
        "expected_og_templates": 29,
        "student_links": [],
        "errors": [],
        "tested_page_names": [],
        "images": [],
        "prior_chromium_checks": 0,
        "prior_chromium_screenshots": 0,
        "prior_chromium_status": "NOT_VERIFIED",
        "production_deployed": False,
        "draft_deployed": False,
        "form_submitted": False,
        "limitations": [
            "All generated pages previously passed v23.5 offline SEO, OG and Hero QA; not all live pages are requested.",
            "Live Chromium results are reused from the already completed immutable Draft run; no new browser test is performed.",
            "Unused legacy PNG files may have dimensions different from 1200x630 but are NOT used as current og:image.",
            "No live form submissions or social platform card-cache appearance tests."
        ],
    }
    try:
        deploy = json.loads((INPUT / "V235_DRAFT_DEPLOY.json").read_text(encoding="utf-8"))
        old_http = json.loads((INPUT / "V235_DRAFT_HTTP_OG_SEO.json").read_text(encoding="utf-8"))
        chromium = json.loads((INPUT / "V235_DRAFT_CHROMIUM.json").read_text(encoding="utf-8"))
        old_final = json.loads((INPUT / "V235_FINAL_PREPRODUCTION_REPORT.json").read_text(encoding="utf-8"))
        assert deploy["status"] == "PASS_V235_DRAFT_DEPLOY_URL"
        assert deploy["id"] == "6ad1988e906a5d8e1bb920c9"
        assert old_final["source_sha"] == EXPECTED_SOURCE_SHA
        assert str(old_final["all_page_v235_hero_og_qa_run"]) == "38843408620"
        draft = guard_draft(deploy["url"].rstrip("/"))
        alias = guard_draft(deploy["alias"].rstrip("/"))
        assert draft != alias
        assert chromium["status"] == "PASS_V235_DRAFT_CHROMIUM"
        assert not chromium.get("errors", [])
        assert len(chromium.get("tested", [])) == 26
        assert chromium.get("screenshots", 0) == 22
        report["draft_unique_url"] = draft
        report["og_alias_url"] = alias
        report["prior_chromium_status"] = chromium["status"]
        report["prior_chromium_checks"] = len(chromium["tested"])
        report["prior_chromium_screenshots"] = chromium["screenshots"]

        prior_names = [x["name"] for x in old_http.get("checks", [])
                       if x.get("name", "").endswith(".html")]
        worker = "seoul-jongno-sajikdong-worker-english-conv-academy.html"
        names = list(dict.fromkeys(prior_names + [worker]))
        if len(names) < 36:
            raise ValueError(f"Unexpectedly small sampled HTML coverage: {len(names)}")
        cached = {}
        observed_images = set()
        for name in names:
            url = guard_draft(draft + "/" + name)
            try:
                status, body, final_url, headers = fetch(url)
                if status != 200 or urlsplit(final_url).hostname != urlsplit(draft).hostname:
                    raise ValueError(f"Unexpected HTTP status or redirect {status} {final_url}")
                require_noindex(headers, url)
                doc = body.decode("utf-8", "replace")
                if not re.search(r'<h1\b[^>]*data-v235-hero-wrap="(?:regular|long|xlong)"', doc, re.I):
                    raise ValueError("v23.5 adaptive H1 marker missing")
                image = meta_values(doc, "og:image")
                twitter = meta_values(doc, "twitter:image", "name")
                width = meta_values(doc, "og:image:width")
                height = meta_values(doc, "og:image:height")
                if (len(image) != 1 or image != twitter or width != ["1200"]
                        or height != ["630"]):
                    raise ValueError("OG meta tags missing or inconsistent")
                if not image[0].startswith(alias + "/assets/images/og-pages/"):
                    raise ValueError("OG image not pointing at isolated Draft alias")
                observed_images.add(image[0].rsplit("/", 1)[-1])
                if name == worker:
                    validate_six_navigation(doc, url, draft, report, cached)
                report["http_pages_passed"] += 1
                report["tested_page_names"].append(name)
                print("V235_EXISTING_DRAFT_HTTP_PASS", name, flush=True)
            except Exception as exc:
                report["errors"].append({"page": name, "reason": repr(exc)})
                print("::error::Live page " + name + " " + str(exc), flush=True)

        template_names = get_og_template_names()
        if not observed_images.issubset(set(template_names)):
            report["errors"].append({
                "reason": "sampled_OG_references_unapproved_template",
                "names": sorted(observed_images - set(template_names))
            })
        for name in template_names:
            try:
                url = guard_draft(alias + "/assets/images/og-pages/" + name)
                status, blob, redirected, headers = fetch(url)
                if status != 200 or not blob.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError("Image not reachable as PNG")
                dims = struct.unpack(">II", blob[16:24])
                if dims != (1200, 630):
                    raise ValueError(f"Square-safe OG design has wrong dimensions: {dims}")
                report["og_images_passed"] += 1
                report["images"].append({"name": name, "width": dims[0], "height": dims[1],
                                         "bytes": len(blob), "status": "PASS"})
                print("V235_APPROVED_OG_IMAGE_PASS", name, dims, flush=True)
            except Exception as exc:
                report["errors"].append({"image": name, "reason": repr(exc)})
                print("::error::OG template " + name + " " + str(exc), flush=True)

        for route in ("robots.txt", "sitemap-index.xml"):
            try:
                url = guard_draft(draft + "/" + route)
                status, data, final, headers = fetch(url)
                if status != 200 or len(data) < 30:
                    raise ValueError(f"SEO resource invalid: {status} {len(data)}")
                require_noindex(headers, url)
                print("V235_DRAFT_SEO_FILE_PASS", route, flush=True)
            except Exception as exc:
                report["errors"].append({"file": route, "reason": repr(exc)})

        if report["http_pages_passed"] != len(names):
            report["errors"].append({
                "reason": "sample_http_page_coverage_not_complete",
                "expected": len(names), "actual": report["http_pages_passed"]
            })
        if report["og_images_passed"] != 29:
            report["errors"].append({"reason": "OG_29_template_coverage_not_complete"})

    except Exception:
        report["errors"].append({"reason": "runner_exception",
                                 "trace": traceback.format_exc()[-2400:]})
    finally:
        report["errors_count"] = len(report["errors"])
        report["status"] = (
            "PASS_V235_EXISTING_DRAFT_HTTP_OG_STUDENT_QA"
            if not report["errors"] else "FAIL_V235_EXISTING_DRAFT_HTTP_OG_STUDENT_QA"
        )
        (OUT / "V235_EXISTING_DRAFT_HTTP_OG_RECHECK.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        with (OUT / "V235_EXISTING_DRAFT_SUMMARY.txt").open("w", encoding="utf-8") as f:
            f.write(
                f"{report['status']}\nOriginal live run: {RUN_ID}\n"
                f"Sample HTTP pages passed: {report['http_pages_passed']}\n"
                f"Approved OG templates passed: {report['og_images_passed']}/29\n"
                f"Student links passed: {len(report['student_links'])}/6\n"
                f"Chromium checks reused: {report['prior_chromium_checks']}/26 PASS\n"
                f"Errors: {report['errors_count']}\n"
                "No Netlify upload, no Production changes, no form submission.\n"
            )
        print(report["status"],
              "HTTP", report["http_pages_passed"],
              "OG", report["og_images_passed"],
              "STUDENT", len(report["student_links"]),
              "PRIOR_CHROMIUM", report["prior_chromium_checks"],
              "ERRORS", len(report["errors"]), flush=True)
        for row in report["errors"][:15]:
            print("::error::" + json.dumps(row, ensure_ascii=False), flush=True)
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
