#!/usr/bin/env python3
"""Patch v23.4 immutable staged HTML student course cards; offline only, no publishing.

Six cards in each student group:
Tutor: elem / middle / high; Conversation grade guide: elem / middle / high.
No false mid/high-tutor locality pages are invented.
"""
import argparse
import html as htmlmod
import json
import re
import sys
import traceback
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, unquote

GROUP = re.compile(
    r'(<article class="related-group"><h3>학생 영어</h3><div class="related-course-links">)'
    r'(.*?)'
    r'(</div></article>)', re.S)
LOCAL_PATH = re.compile(r'href="/([^"]+)-(?:elem-tutor|mid-conv|high-conv)\.html"')
LABEL = re.compile(r'(.+?)\s+(?:초등학생영어과외|중학생영어회화|고등학생영어회화|'
                   r'초등학생영어회화|중학생영어과외|고등학생영어과외)')
LINK = re.compile(r'<a\b[^>]*>.*?</a>', re.S)
ATTR_HREF = re.compile(r'\bhref="([^"]+)"')
SPANS = re.compile(r'<span>(.*?)</span>', re.S)
GRADES = ("초등학생", "중학생", "고등학생")
GRADE_IDS = ("elementary", "middle", "high")
HUB_SECTION = re.compile(
    r'(<section class="section" aria-label="학년별 영어과외 안내">.*?</section>)'
    r'(?=<section class="section soft region-navigation" id="region">)', re.S)

def find_location(fragment, page):
    hit = LOCAL_PATH.search(fragment)
    if not hit:
        raise ValueError("cannot determine locality slug from existing real detail links")
    slug = htmlmod.unescape(hit.group(1))
    dong = None
    for link in LINK.findall(fragment):
        span = SPANS.search(link)
        if not span:
            continue
        label = htmlmod.unescape(re.sub(r'<[^>]*>', '', span.group(1))).strip()
        found = LABEL.match(label)
        if found:
            dong = found.group(1).strip()
            break
    if not dong:
        raise ValueError("cannot determine dong display name from student link labels")
    return slug, dong

def target_file(root, url, current_page, hub_anchors):
    route = urlsplit(url)
    if route.scheme or route.netloc or not route.path.startswith("/"):
        return "not_local_absolute_path"
    target = (root / unquote(route.path).lstrip("/")).resolve()
    if not target.is_relative_to(root.resolve()):
        return "path_traversal"
    if not target.is_file():
        return "missing_destination"
    if route.fragment and target.name == "student-english.html" and route.fragment not in hub_anchors:
        return "missing_hub_anchor"
    return None

def cards(slug, dong, page):
    # A locality has only the elementary tutoring page in this 23-intent
    # release. Other tutoring options lead to honest, distinct study/consultation
    # sections of the student hub instead of non-existent regional URLs.
    urls = [
        "/student-english.html#elementary-tutor" if page.name.endswith("-elem-tutor.html")
        else "/" + htmlmod.escape(slug, quote=True) + "-elem-tutor.html",
        "/student-english.html#middle-tutor",
        "/student-english.html#high-tutor",
        "/student-english.html#elementary",
        "/student-english.html#middle",
        "/student-english.html#high",
    ]
    output = []
    for i, (grade, url) in enumerate(zip(GRADES + GRADES, urls)):
        label = htmlmod.escape(dong + " " + grade + ("영어과외" if i < 3 else "영어회화"))
        if i < 3:
            output.append(
                '<a class="related-course-tutor" href="' + url + '">'
                '<span>' + label + '</span><b>→</b></a>')
        else:
            output.append(
                '<a class="related-course-fallback" href="' + url + '" '
                'title="지역별 회화 상세페이지와 별도로 학년별 학생영어 안내로 이동">'
                '<span>' + label + ' '
                '<small>학년별 수업 안내 · 지역 상세페이지 준비 전</small></span>'
                '<b>안내 →</b></a>')
    return ''.join(output), urls

def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--root", type=Path, required=True)
    arg.add_argument("--source-hub", type=Path, required=True)
    arg.add_argument("--report", type=Path, required=True)
    arg.add_argument("--expected", type=int, default=140391)
    args = arg.parse_args()
    root = args.root.resolve()
    pages = sorted(root.glob("*.html"))
    generated = [p for p in pages if p.name not in ("index.html", "404.html")]
    report = {
        "status": "RUNNING", "release": "v23.4-corrected-student-navigation",
        "source_run": "38689660290",
        "source_sha": "a18b8901ecda7d37f65e35b15f03d579ec63c70f",
        "og_full_site_run": "38766832143",
        "generated_expected": args.expected, "generated_found": len(generated),
        "html_total": len(pages), "student_groups_found": 0,
        "student_groups_modified": 0, "student_links_verified": 0,
        "files_untouched": 0, "errors_count": 0, "errors": [],
        "production_deployed": False, "netlify_deployed": False,
        "form_submissions": False
    }
    args.report.parent.mkdir(exist_ok=True, parents=True)
    bad = []
    try:
        if len(generated) != args.expected or len(pages) != args.expected + 2:
            raise ValueError(f"unexpected release HTML count: {len(generated)} + hubs")
        source = args.source_hub.read_text(encoding="utf-8")
        section = HUB_SECTION.search(source)
        if not section:
            raise ValueError("new approved student tutoring hub section absent from repository source")
        hub_path = root / "student-english.html"
        hub = hub_path.read_text(encoding="utf-8")
        needle = '<section class="section soft region-navigation" id="region">'
        if 'id="elementary-tutor"' not in hub:
            if needle not in hub:
                raise ValueError("student hub insertion point missing")
            hub = hub.replace(needle, section.group(1) + needle, 1)
            hub_path.write_text(hub, encoding="utf-8")
        hub_anchors = set(re.findall(r'\bid="([^"]+)"', hub))
        required = set(GRADE_IDS) | set(x + "-tutor" for x in GRADE_IDS)
        if not required.issubset(hub_anchors):
            raise ValueError("student hub lacks needed grade tutoring/conversation anchors")

        # Prevent "안내 →" wrapping across two lines at mobile width.
        # The immutable OG package has its own root pilot.css; update the
        # staged copy without touching the live Draft or Production site.
        css_rule = (
            "\n/* v23.4 student-navigation CTA mobile no-wrap */\n"
            ".related-course-links a span{flex:1 1 auto;min-width:0}\n"
            ".related-course-links a b{flex:0 0 auto;white-space:nowrap;"
            "word-break:keep-all;overflow-wrap:normal}\n"
        )
        pilot_css = root / "pilot.css"
        if not pilot_css.is_file():
            raise ValueError("staged release lacks pilot.css required by locality pages")
        css_updated = 0
        for css_path in (pilot_css, root / "assets/stage9-mass-production.css"):
            if css_path.is_file():
                contents = css_path.read_text(encoding="utf-8")
                if "v23.4 student-navigation CTA mobile no-wrap" not in contents:
                    css_path.write_text(contents + css_rule, encoding="utf-8")
                    css_updated += 1
        report["css_files_updated"] = css_updated

        for index,p in enumerate(pages):
            try:
                original = p.read_text(encoding="utf-8")
                matches = list(GROUP.finditer(original))
                if not matches:
                    report["files_untouched"] += 1
                    continue
                if len(matches) != 1:
                    raise ValueError("duplicate student English group")
                match = matches[0]
                slug, dong = find_location(match.group(2), p)
                interior, urls = cards(slug, dong, p)
                for link in urls:
                    error = target_file(root, link, p, hub_anchors)
                    if error:
                        raise ValueError(f"{error}: {link}")
                # Exact six-link ordering and labels.
                links = LINK.findall(interior)
                if len(links) != 6:
                    raise ValueError("six cards not created")
                for i, link in enumerate(links):
                    label = htmlmod.escape(dong + " " + GRADES[i%3] + ("영어과외" if i<3 else "영어회화"))
                    if f"<span>{label}" not in link or f'href="{urls[i]}"' not in link:
                        raise ValueError(f"wrong link label / order at index {i}")
                report["student_groups_found"] += 1
                updated = original[:match.start(2)] + interior + original[match.end(2):]
                if updated != original:
                    p.write_text(updated, encoding="utf-8")
                    report["student_groups_modified"] += 1
                report["student_links_verified"] += 6
                if (index+1) % 25000 == 0:
                    print("STUDENT_NAV_PROGRESS",index+1,len(pages),
                          report["student_groups_modified"],flush=True)
            except Exception as exc:
                if len(bad) < 200:
                    bad.append({"file": p.name, "reason": str(exc)})
                report["errors_count"] += 1
        if report["student_groups_found"] < 1000:
            bad.append({"file": "(all)", "reason": "student group coverage unexpectedly low"})
            report["errors_count"] += 1
    except Exception as exc:
        bad.append({"file": "(runner)", "reason": repr(exc), "trace": traceback.format_exc()[-1600:]})
        report["errors_count"] += 1
    finally:
        report["errors"] = bad
        report["status"] = ("PASS_V23_4_ALL_STUDENT_NAV_CORRECTED" if
                            report["errors_count"] == 0 and
                            report["student_groups_found"] >= 1000
                            else "FAIL_V23_4_ALL_STUDENT_NAV_CORRECTED")
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n", encoding="utf-8")
        print(report["status"],"pages",report["html_total"],
              "groups",report["student_groups_found"],"changed",report["student_groups_modified"],
              "links",report["student_links_verified"],"errors",report["errors_count"],flush=True)
        for row in bad[:20]:
            print("::error::"+json.dumps(row,ensure_ascii=False),flush=True)
    return 0 if report["status"].startswith("PASS") else 1

if __name__ == "__main__":
    sys.exit(main())
