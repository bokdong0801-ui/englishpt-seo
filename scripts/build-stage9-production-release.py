#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the explicitly approved Stage 9 production release."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_NEW = 66937
EXPECTED_PRESERVED = 95
EXPECTED_TOTAL = 67032
EXPECTED_SITEMAPS = 135
EXPECTED_REDIRECTS = 74
BASE_URL = "https://englishpt.kr"

ROBOTS_RE = re.compile(
    r'<meta\s+name=["\']robots["\']\s+content=["\']noindex\s*,\s*nofollow["\']\s*/?>',
    re.I,
)

SERVICE_THEME_SUFFIXES = {
    "elem-tutor": "theme-elem intent-audience",
    "mid-conv": "theme-mid intent-audience",
    "high-conv": "theme-high intent-audience",
    "univ-conv": "theme-univ intent-audience",
    "jobseeker-conv": "theme-job intent-audience",
    "biz-business-conv": "theme-worker intent-audience",
    "housewife-conv": "theme-housewife intent-audience",
}
EXAM_SUFFIXES = ("toeic", "toeic-speaking", "opic", "ielts", "duolingo", "toefl")

EMAILJS_TAG = '<script defer src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>'
LIVE_FORM = '''<form id="pilotForm" class="lead-form">
<label>이름 <span>*</span><input name="name" autocomplete="name" required></label>
<label>연락처 <span>*</span><input name="phone" inputmode="tel" autocomplete="tel" placeholder="010-0000-0000" required></label>
<label class="full">가장 가까운 일정<input name="deadline" placeholder="시험·발표·면접·사용 일정"></label>
<label class="full">가장 막히는 장면<textarea name="difficulty" rows="3" placeholder="최근 어려웠던 문제·응답·상황"></textarea></label>
<label class="privacy-check"><input name="consent" type="checkbox" required><span>상담을 위한 개인정보 수집·이용에 동의합니다.</span></label>
<div class="submit-row"><button class="btn primary" type="submit">무료 PT 진단 신청 →</button><a class="btn phone" href="tel:+821050068027">전화 010-5006-8027</a></div>
<p class="pilot-status" aria-live="polite"></p>
</form>'''

PRODUCTION_TEXT_FIXES = {
    "복습회수": "복습 횟수",
    "현재범위": "현재 범위",
    "차수 차수": "반복 횟수",
    "상기 차수": "복습 횟수",
    "회상 차수": "복습 횟수",
    "기억 회수": "복습 횟수",
    "암기 차수": "복습 횟수",
    "후속 기점": "다음 기준",
    "재검토 동작": "다음 점검",
    "재확인 동작": "다음 점검",
    "재확인 행동": "다음 점검",
    "재검토 행동": "다음 점검",
}


def theme_class_for(name: str) -> str:
    for suffix, body_class in SERVICE_THEME_SUFFIXES.items():
        if name.endswith(f"-{suffix}.html"):
            return body_class
    if any(name.endswith(f"-{suffix}.html") for suffix in EXAM_SUFFIXES):
        return "theme-test intent-test"
    raise ValueError(f"unknown Stage 9 mass-page intent: {name}")


def _plain_h1(raw: str) -> str:
    m = re.search(r"<h1>(.*?)</h1>", raw, re.S | re.I)
    if not m:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()


def _replace_kicker_h2(raw: str, kicker: str, heading: str) -> str:
    pattern = re.compile(
        r'(<p class="kicker">' + re.escape(kicker) + r'</p><h2>).*?(</h2>)',
        re.S,
    )
    return pattern.sub(lambda m: m.group(1) + html.escape(heading) + m.group(2), raw, count=1)


def normalize_production_page(raw: str, name: str) -> tuple[str, list[str]]:
    problems: list[str] = []
    body_class = theme_class_for(name)
    raw, body_n = re.subn(
        r'<body class="[^"]*" data-production-deploy="false">',
        f'<body class="{body_class}" data-production-deploy="true">',
        raw,
        count=1,
    )
    if body_n != 1:
        problems.append("production_body")

    raw = raw.replace("FULL GENERATION · noindex", "ENGLISH PT · 지역별 맞춤 안내")
    raw = raw.replace("Stage 5 full generation · production 미배포", "ENGLISH PT · 지역별 맞춤 영어 안내")
    raw = raw.replace("Stage 3 dry-run · production 미배포", "ENGLISH PT · 지역별 맞춤 영어 안내")
    raw = raw.replace('href="../englishpt.html"', 'href="/englishpt.html"')

    if '<script defer src="pilot.js"></script>' in raw and EMAILJS_TAG not in raw:
        raw = raw.replace(
            '<script defer src="pilot.js"></script>',
            EMAILJS_TAG + '<script defer src="pilot.js"></script>',
            1,
        )

    raw, form_n = re.subn(
        r'<form id="pilotForm">.*?</form>',
        LIVE_FORM,
        raw,
        count=1,
        flags=re.S,
    )
    if form_n != 1:
        problems.append("live_form")

    h1 = _plain_h1(raw)
    if not h1:
        problems.append("h1_missing_for_ui")
        h1 = "ENGLISH PT"
    service = h1.split(maxsplit=1)[1] if len(h1.split(maxsplit=1)) == 2 else h1

    heading_map = {
        "자기상황 식별": "내 상황과 가까운 장면부터 확인합니다",
        "선택 기준": "지금 이 과정이 맞는지 다섯 가지 기준으로 확인합니다",
        "판단 가이드": f"{service}를 실제 목표와 일정에 연결하는 방법",
        "지역별 판단 방식": f"{service} 선택 전에 확인할 기준",
        "우선순위": "현재 결과를 가장 크게 막는 지점부터 우선합니다",
        "수업 흐름": "설명에서 끝내지 않고 실제 행동으로 다시 확인합니다",
        "중간 확인": "지금 필요한 첫 순서를 상담 전에 정리해보세요",
        "판단 기준": "변화를 추상적인 표현 대신 실제 행동으로 확인합니다",
        "피드백 예시": "성과를 약속하지 않고 다음 확인 행동을 남깁니다",
        "자주 묻는 질문": "상담 전에 자주 확인하는 질문",
        "더 깊게 보기": f"{service} 선택 전에 확인할 기준을 더 구체적으로 정리했습니다",
        "판단 루트": "이 페이지에서 확인하는 순서를 정리했습니다",
        "관련 과정": "같은 지역의 다른 영어 목표도 비교해보세요",
        "상담 전 체크": "최근 자료와 가장 막힌 장면, 다음 일정을 준비해 주세요",
    }
    for kicker, heading in heading_map.items():
        raw = _replace_kicker_h2(raw, kicker, heading)

    raw = re.sub(
        r'(<section class="final"><div class="wrap"><h2>).*?(</h2>)',
        lambda m: m.group(1) + html.escape(f"{h1}, 등록보다 먼저 현재 상태와 목표부터 확인하세요.") + m.group(2),
        raw,
        count=1,
        flags=re.S,
    )

    for old, new in PRODUCTION_TEXT_FIXES.items():
        raw = raw.replace(old, new)

    if "<main>" in raw and 'class="breadcrumb wrap"' not in raw:
        crumb = (
            '<div class="breadcrumb wrap" aria-label="현재 위치">'
            '<a href="/englishpt.html">잉글리시PT</a><span aria-hidden="true">/</span>'
            f'<strong>{html.escape(h1)}</strong></div>'
        )
        raw = raw.replace("<main>", "<main>" + crumb, 1)

    schema_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
    canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', raw, re.I)
    if schema_match and canonical_match:
        try:
            data = json.loads(schema_match.group(1))
            graph = data.get("@graph")
            if isinstance(graph, list) and not any(x.get("@type") == "BreadcrumbList" for x in graph if isinstance(x, dict)):
                graph.append({
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": 1, "name": "잉글리시PT", "item": f"{BASE_URL}/englishpt.html"},
                        {"@type": "ListItem", "position": 2, "name": h1, "item": canonical_match.group(1)},
                    ],
                })
                replacement = '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + '</script>'
                raw = raw[:schema_match.start()] + replacement + raw[schema_match.end():]
        except Exception:
            problems.append("breadcrumb_schema")

    if 'class="mobile-sticky"' not in raw:
        raw = raw.replace(
            "</body>",
            '<div class="mobile-sticky"><a href="#consultation-preview">무료 PT 진단 신청</a></div></body>',
            1,
        )

    required = [
        f'<body class="{body_class}" data-production-deploy="true">',
        'name="name"',
        'name="phone"',
        'name="consent"',
        EMAILJS_TAG,
        'class="breadcrumb wrap"',
        'class="mobile-sticky"',
    ]
    if any(x not in raw for x in required):
        problems.append("production_ui_contract")
    if any(x in raw for x in ("production 미배포", "검수용 페이지", 'data-production-deploy="false"')):
        problems.append("stale_preview_copy")
    return raw, problems


def count_redirect_rules(path: Path) -> list[str]:
    return [
        line.strip() for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage7-root", required=True)
    ap.add_argument("--stage8-root", required=True)
    ap.add_argument("--work-root", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    stage7 = Path(args.stage7_root).resolve()
    stage8 = Path(args.stage8_root).resolve()
    work = Path(args.work_root).resolve()
    out = Path(args.output).resolve()

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    failures: list[object] = []

    q7 = json.loads((stage7 / "STAGE7_DEPLOY_PREVIEW_QA_V1.json").read_text(encoding="utf-8"))
    q8 = json.loads((stage8 / "STAGE8_PRODUCTION_APPROVAL_PACKET_V1.json").read_text(encoding="utf-8"))

    if q7.get("status") != "PASS_STAGE7_DEPLOY_PREVIEW_ROLLBACK_READY_NOT_PRODUCTION":
        failures.append("stage7_not_pass")
    if q8.get("status") != "PASS_STAGE8_PRODUCTION_APPROVAL_PACKET_READY_NOT_DEPLOYED":
        failures.append("stage8_not_pass")
    if q8.get("final_domain") != BASE_URL or q8.get("final_domain_confirmed") is not True:
        failures.append("final_domain_not_confirmed")
    if q8.get("approval", {}).get("next_stage") != "STAGE9_PRODUCTION_DEPLOY":
        failures.append("stage8_next_stage_not_stage9")
    if q8.get("counts", {}).get("new_pages") != EXPECTED_NEW:
        failures.append("stage8_new_page_count")
    if q8.get("counts", {}).get("preserved_pages") != EXPECTED_PRESERVED:
        failures.append("stage8_preserved_page_count")
    if q8.get("counts", {}).get("deploy_html_total") != EXPECTED_TOTAL:
        failures.append("stage8_total_page_count")

    rollback = stage7 / "rollback-root"
    if not rollback.exists():
        failures.append("rollback_root_missing")
    else:
        shutil.copytree(rollback, out, dirs_exist_ok=True)

    new_pages = sorted((work / "stage5-full-generation").glob("shard-*/pages/*.html"))
    if len(new_pages) != EXPECTED_NEW:
        failures.append({"new_pages": [len(new_pages), EXPECTED_NEW]})

    transformed = 0
    bad_robot_pages: list[str] = []
    bad_domain_pages: list[str] = []
    bad_ui_pages: list[dict] = []
    for src in new_pages:
        raw = src.read_text(encoding="utf-8")
        raw, n = ROBOTS_RE.subn('<meta name="robots" content="index,follow">', raw, count=1)
        raw, ui_problems = normalize_production_page(raw, src.name)
        if ui_problems:
            bad_ui_pages.append({"file": src.name, "problems": ui_problems})
        if n != 1:
            bad_robot_pages.append(src.name)
        if "noindex" in raw.lower() or "nofollow" in raw.lower():
            bad_robot_pages.append(src.name)
        canonical = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', raw, re.I)
        if not canonical or not canonical.group(1).startswith(BASE_URL + "/"):
            bad_domain_pages.append(src.name)
        (out / src.name).write_text(raw, encoding="utf-8")
        transformed += 1

    first_pages_dir = next(iter((work / "stage5-full-generation").glob("shard-*/pages")), None)
    if first_pages_dir:
        for asset in ("pilot.css", "pilot.js"):
            src = first_pages_dir / asset
            if src.exists():
                shutil.copy2(src, out / asset)
    production_assets = {
        "pilot.css": ROOT / "assets" / "stage9-mass-production.css",
        "pilot.js": ROOT / "assets" / "stage9-mass-production.js",
    }
    for asset, src in production_assets.items():
        if not src.exists():
            failures.append(f"production_asset_missing:{asset}")
        else:
            shutil.copy2(src, out / asset)
    for asset in ("pilot.css", "pilot.js"):
        if not (out / asset).exists():
            failures.append(f"{asset}_missing")

    release_config = stage8 / "release-config"
    if not release_config.exists():
        failures.append("release_config_missing")
    else:
        for p in release_config.iterdir():
            dst = out / p.name
            if p.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(p, dst)
            else:
                shutil.copy2(p, dst)

    # The pre-release baseline sitemap contains only the historical 95 URLs.
    # Stage 9 publishes the final sitemap-index.xml instead.
    old_sitemap = out / "sitemap.xml"
    if old_sitemap.exists():
        old_sitemap.unlink()

    html_files = sorted(out.glob("*.html"))
    sitemap_files = sorted((out / "sitemaps").glob("sitemap-*.xml")) if (out / "sitemaps").exists() else []
    if len(html_files) != EXPECTED_TOTAL:
        failures.append({"deploy_html_total": [len(html_files), EXPECTED_TOTAL]})
    if transformed != EXPECTED_NEW:
        failures.append({"transformed_new": [transformed, EXPECTED_NEW]})
    if len(sitemap_files) != EXPECTED_SITEMAPS:
        failures.append({"sitemap_shards": [len(sitemap_files), EXPECTED_SITEMAPS]})
    if bad_robot_pages:
        failures.append({"robots_transform_failures": sorted(set(bad_robot_pages))[:20]})
    if bad_domain_pages:
        failures.append({"canonical_domain_failures": sorted(set(bad_domain_pages))[:20]})
    if bad_ui_pages:
        failures.append({"production_ui_failures": bad_ui_pages[:20]})

    index = (out / "sitemap-index.xml").read_text(encoding="utf-8")
    if index.count("<sitemap><loc>") != EXPECTED_SITEMAPS:
        failures.append("sitemap_index_count")
    if f"{BASE_URL}/sitemaps/" not in index:
        failures.append("sitemap_index_domain")

    sitemap_urls = 0
    for p in sitemap_files:
        text = p.read_text(encoding="utf-8")
        sitemap_urls += text.count("<url><loc>")
        if "englishup.kr" in text or "example.com" in text:
            failures.append({"stale_sitemap_host": p.name})
            break
    if sitemap_urls != EXPECTED_TOTAL:
        failures.append({"sitemap_urls": [sitemap_urls, EXPECTED_TOTAL]})

    robots = (out / "robots.txt").read_text(encoding="utf-8")
    if "Disallow: /" in robots:
        failures.append("robots_blocks_all")
    if f"Sitemap: {BASE_URL}/sitemap-index.xml" not in robots:
        failures.append("robots_sitemap_mismatch")

    rules = count_redirect_rules(out / "_redirects")
    if len(rules) < EXPECTED_REDIRECTS + 1:
        failures.append({"redirect_rule_count": len(rules)})
    if not any(x.startswith("/ /englishpt.html 301") for x in rules):
        failures.append("root_redirect_missing")

    report = {
        "version": "1.0",
        "status": "PASS_STAGE9_RELEASE_ASSEMBLED_READY_TO_DEPLOY" if not failures else "FAIL_STAGE9_RELEASE_ASSEMBLY",
        "stage": "STAGE9_PRODUCTION_DEPLOY",
        "final_domain": BASE_URL,
        "counts": {
            "new_pages": transformed,
            "html_total": len(html_files),
            "sitemap_shards": len(sitemap_files),
            "sitemap_urls": sitemap_urls,
            "redirect_rules": len(rules),
        },
        "indexing": {
            "new_page_robots": "index,follow",
            "noindex_pages": len(set(bad_robot_pages)),
            "robots_txt_allows_crawl": "Disallow: /" not in robots,
            "production_ui_failures": len(bad_ui_pages),
        },
        "source": {
            "stage7_status": q7.get("status"),
            "stage8_status": q8.get("status"),
        },
        "failures": failures,
    }
    (out / "STAGE9_PRODUCTION_RELEASE_QA_V1.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
