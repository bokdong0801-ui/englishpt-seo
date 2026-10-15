#!/usr/bin/env python3
"""v23.4 immutable Netlify Draft read-only HTTP and Chromium review. No form submissions."""
import argparse
import json
import os
import re
import sys
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

BASE = "https://6ad07fd3b9f7987dddeb8b3f--englishpt-final-ia-review-bokdong.netlify.app"
DEPLOY_ID = "6ad07fd3b9f7987dddeb8b3f"
SOURCE_RUN = "38689660290"
SOURCE_SHA = "a18b8901ecda7d37f65e35b15f03d579ec63c70f"
WORKER = "seoul-jongno-sajikdong-worker-english-conv-academy.html"
SAMPLES = [
    "englishpt.html",
    "seoul-jongno-sajikdong-beginner-english-conv.html",
    "seoul-jongno-sajikdong-toeic.html",
    "seoul-jongno-sajikdong-ielts.html",
    "dalseo-songhyeondong.html",
    "station-gangnam.html",
    "station-amsayeoksagongwon.html",
    WORKER,
]
HUBS = ["index.html", "courses.html", "english-conversation.html",
        "exam-english.html", "student-english.html", "stations.html"]
CHOICES = (
    "사직동 초등학생영어과외", "사직동 초등학생영어회화",
    "사직동 중학생영어회화", "사직동 중학생영어과외",
    "사직동 고등학생영어회화", "사직동 고등학생영어과외",
)
PREFIX = "ENGLISHPT_V23_4_EXISTING_DRAFT_"
UA = {"User-Agent": "ENGLISH-PT-v23.4-draft-verify-no-submissions"}

class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.active = None
        self.has_h1 = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "h1":
            self.has_h1 = True
        if tag == "a":
            self.active = {"href": d.get("href", ""), "text": []}
            self.links.append(self.active)

    def handle_data(self, data):
        if self.active is not None:
            self.active["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            self.active = None

def report_path(phase):
    return Path("draft-review-report") / (PREFIX + phase.upper() + ".json")

def save(phase, data):
    p = report_path(phase)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WRITTEN_REPORT", str(p), flush=True)

def blank(phase):
    return dict(version="v23.4", status="RUNNING", phase=phase,
                draft_url=BASE, netlify_deploy_id=DEPLOY_ID,
                source_run=SOURCE_RUN, source_sha=SOURCE_SHA,
                checked_at=datetime.now(timezone.utc).isoformat(),
                production_deployed=False, draft_deployed=False,
                form_submissions="NOT_PERFORMED", checks=[], failures=[],
                confirmed_scope="live 14 HTTP pages; 8 sample pages x two viewports")

def record_error(report, page, code, detail="", width=None):
    row = {"page": page, "reason": code, "detail": str(detail)[:500]}
    if width is not None:
        row["width"] = width
    report["failures"].append(row)
    print("::error::" + json.dumps(row, ensure_ascii=False), flush=True)

def http_fetch(url, attempts=2):
    last = None
    for n in range(attempts):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=35) as response:
                return response.status, response.read().decode("utf-8", "replace"), response.url
        except Exception as exc:
            last = exc
            if n + 1 < attempts:
                time.sleep(2)
    raise last

def validate_same_draft(url):
    u = urlsplit(url)
    if u.scheme != "https" or u.netloc != urlsplit(BASE).netloc:
        raise ValueError("Not the approved immutable v23.4 Draft host: " + url)
    return url

def run_http():
    report = blank("http")
    targets = list(dict.fromkeys(HUBS + SAMPLES))
    cache = {}
    try:
        for name in targets:
            url = validate_same_draft(urljoin(BASE + "/", name))
            try:
                status, html, final_url = http_fetch(url)
                if status != 200:
                    raise ValueError("HTTP " + str(status))
                if urlsplit(final_url).netloc != urlsplit(BASE).netloc:
                    raise ValueError("Unexpected redirect: " + final_url)
                if len(html) < 900:
                    raise ValueError("Unusually short response: " + str(len(html)))
                parser = Extract()
                parser.feed(html)
                if not parser.has_h1:
                    raise ValueError("H1 missing")
                if name.startswith("seoul-jongno-sajikdong-"):
                    if 'data-hero-copy="audience-v2"' not in html:
                        raise ValueError("v23 Hero V2 marker missing")
                    if "consultation-preview" not in parser.ids:
                        raise ValueError("consultation target missing")
                    if not any(a["href"] == "#consultation-preview" for a in parser.links):
                        raise ValueError("consultation CTA link missing")
                if name == WORKER:
                    for choice in CHOICES:
                        normalized = "".join(choice.split())
                        matching = [a for a in parser.links if normalized in "".join("".join(a["text"]).split())]
                        if not matching:
                            record_error(report, name, "student_choice_anchor_missing", choice)
                            continue
                        href = next((a["href"].strip() for a in matching if a["href"].strip() and not a["href"].startswith(("javascript:", "#"))), "")
                        if not href:
                            record_error(report, name, "student_choice_non_navigable", choice)
                            continue
                        dest_url = validate_same_draft(urljoin(url, href))
                        route = urlsplit(dest_url)
                        if not route.path or route.path == "/":
                            record_error(report, name, "empty_student_choice_route", href)
                            continue
                        if dest_url not in cache:
                            try:
                                target_status, target_html, actual_url = http_fetch(dest_url)
                                if target_status != 200 or urlsplit(actual_url).netloc != urlsplit(BASE).netloc:
                                    raise ValueError("Bad destination response")
                                target_parser = Extract()
                                target_parser.feed(target_html)
                                if not target_parser.has_h1:
                                    raise ValueError("destination H1 missing")
                                if route.fragment and route.path.rstrip("/").rsplit("/", 1)[-1] in ("student-english", "student-english.html"):
                                    if unquote(route.fragment) not in target_parser.ids:
                                        raise ValueError("destination anchor missing: " + route.fragment)
                                cache[dest_url] = True
                            except Exception as exc:
                                cache[dest_url] = False
                                record_error(report, name, "student_choice_destination_invalid", f"{choice}: {href}: {exc}")
                        if cache.get(dest_url):
                            report["checks"].append({"name": name, "choice": choice, "href": href, "destination": dest_url, "status": "PASS"})
                    for phrase in ("수업 하루 전까지", "수업 외 시간에도", "레벨테스트", "주 2~5회"):
                        if phrase not in html:
                            record_error(report, name, "v23_4_copy_missing", phrase)
                    if "연습 방법도" in html.split("</head>", 1)[-1]:
                        record_error(report, name, "obsolete_wording", "연습 방법도")
                report["checks"].append({"name": name, "url": url, "http": status, "html_chars": len(html), "status": "PASS"})
                print("HTTP_OK", name, status, len(html), flush=True)
            except Exception as exc:
                record_error(report, name, "http_or_content_failed", repr(exc))
        report["status"] = "PASS_V23_DRAFT_HTTP_REVIEW" if not report["failures"] else "FAIL_V23_DRAFT_HTTP_REVIEW"
    except Exception:
        record_error(report, "(runner)", "unexpected_http_runner_exception", traceback.format_exc())
        report["status"] = "FAIL_V23_DRAFT_HTTP_REVIEW"
    finally:
        report["pages_expected"] = len(targets)
        report["pages_passed"] = sum(1 for x in report["checks"] if x.get("http") == 200 and x.get("status") == "PASS")
        report["student_choices_checked"] = sum(1 for x in report["checks"] if "choice" in x)
        report["representative_urls"] = {x: BASE + "/" + x for x in SAMPLES}
        save("http", report)
        print(report["status"], "pages", report["pages_passed"], "/", len(targets),
              "student_choices", report["student_choices_checked"],
              "failures", len(report["failures"]), flush=True)
    return not report["failures"]

JS_PROBE = r"""() => {
  const bodyText = document.body?.innerText || '';
  const h1 = document.querySelector('h1');
  const styles = [...document.styleSheets].some(s => !!s.href);
  const anchor = document.querySelector('a[href="#consultation-preview"]');
  const target = document.getElementById('consultation-preview');
  const btn = document.querySelector('[data-open-form]');
  const modal = document.getElementById('applyModal');
  const modalBefore = modal?.classList.contains('open') || false;
  return {
    url: location.href, width: innerWidth,
    documentWidth: document.documentElement.scrollWidth,
    h1: h1?.innerText || '',
    bodyChars: bodyText.length, styles: styles,
    consultationAnchor: !!anchor, consultationTarget: !!target,
    modalButton: !!btn, modalExists: !!modal, modalOpenInitially: modalBefore,
    timeline: document.querySelectorAll('.change-section .change-card').length,
    aftercare: !!document.querySelector('.manage-aftercare,.aftercare-summary'),
    docReady: document.readyState, fonts: document.fonts?.status || 'unknown'
  }
}"""

def run_chromium():
    report = blank("chromium")
    output = Path("draft-review-report/screenshots")
    output.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            executable = next((x for x in (
                "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium"
            ) if Path(x).exists()), None)
            launch = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
            if executable:
                launch["executable_path"] = executable
            browser = playwright.chromium.launch(**launch)
            try:
                for width, is_mobile in ((390, True), (1440, False)):
                    context = browser.new_context(
                        viewport={"width": width, "height": 900}, device_scale_factor=1,
                        is_mobile=is_mobile, has_touch=is_mobile)
                    # Never submit forms: reject form-submit POSTs even if a page script fires.
                    context.route("**/*", lambda route: route.abort() if route.request.method not in ("GET", "HEAD") else route.continue_())
                    page = context.new_page()
                    try:
                        for name in SAMPLES:
                            url = validate_same_draft(BASE + "/" + name)
                            try:
                                resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                                if not resp or resp.status != 200:
                                    raise ValueError("Browser page HTTP: " + str(resp.status if resp else "None"))
                                page.wait_for_timeout(800)
                                page.evaluate("() => document.fonts?.ready")
                                values = page.evaluate(JS_PROBE)
                                issues = []
                                if values["width"] != width or values["documentWidth"] > width + 3:
                                    issues.append("viewport_overflow")
                                if not values["styles"]:
                                    issues.append("stylesheet_unavailable")
                                if not values["h1"] or values["bodyChars"] < 300:
                                    issues.append("visible_page_content_missing")
                                if values["docReady"] == "loading":
                                    issues.append("document_not_ready")
                                # Navigate to the intended consultation section or open its modal; never press submit.
                                visible_cta = page.locator("[data-open-form]:visible")
                                if values["modalExists"] and visible_cta.count() > 0:
                                    visible_cta.first.click(timeout=6000)
                                    opened = page.locator("#applyModal").evaluate(
                                        "(e) => e.classList.contains('open') && e.getAttribute('aria-hidden') !== 'true'")
                                    if not opened:
                                        issues.append("consultation_modal_did_not_open")
                                    # Reload for clean screenshot; never touch a submit control.
                                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                                    page.wait_for_timeout(350)
                                elif values["consultationAnchor"] and values["consultationTarget"]:
                                    pass
                                else:
                                    issues.append("visible_consultation_navigation_missing")
                                if name == "englishpt.html" and values["timeline"] != 4:
                                    issues.append("four_timeline_cards_missing")
                                if name == "seoul-jongno-sajikdong-beginner-english-conv.html" and not values["aftercare"]:
                                    issues.append("beginner_aftercare_missing")
                                path = output / (name[:-5] + "-" + str(width) + ".png")
                                page.screenshot(path=str(path), full_page=False, timeout=15000)
                                report["checks"].append({"name": name, "width": width, "status": "PASS" if not issues else "FAIL",
                                                         "checks": values, "issues": issues, "screenshot": path.name})
                                for issue in issues:
                                    record_error(report, name, issue, width=width)
                                print("CHROMIUM_PAGE", width, name, "PASS" if not issues else ",".join(issues), flush=True)
                            except Exception as exc:
                                record_error(report, name, "browser_probe_exception", repr(exc), width=width)
                    finally:
                        context.close()
            finally:
                browser.close()
        report["status"] = "PASS_V23_LIVE_DRAFT_CHROMIUM" if not report["failures"] else "FAIL_V23_LIVE_DRAFT_CHROMIUM"
    except Exception:
        record_error(report, "(browser)", "browser_launch_or_runner_exception", traceback.format_exc())
        report["status"] = "FAIL_V23_LIVE_DRAFT_CHROMIUM"
    finally:
        report["viewport_widths"] = [390, 1440]
        report["screenshots_saved"] = len(list(output.glob("*.png")))
        save("chromium", report)
        print(report["status"], "checks", len(report["checks"]), "screenshots", report["screenshots_saved"],
              "failures", len(report["failures"]), flush=True)
    return not report["failures"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=["http", "chromium"])
    options = parser.parse_args()
    sys.exit(0 if (run_http() if options.phase == "http" else run_chromium()) else 1)
