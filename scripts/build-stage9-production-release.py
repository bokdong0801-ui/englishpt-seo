#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the explicitly approved Stage 9 production release."""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CLEAN_RENDERER = _load_module(
    "stage9_clean_mass_renderer", ROOT / "scripts" / "stage9-clean-mass-renderer.py"
)

STATION_RENDERER = _load_module(
    "stage9_station_renderer", ROOT / "scripts" / "stage9-station-renderer.py"
)

EXPECTED_SOURCE_NEW = 66937
EXPECTED_ACADEMY_NEW = 30894
EXPECTED_CONVERSATION_NEW = 20596
EXPECTED_NEW = EXPECTED_SOURCE_NEW + EXPECTED_ACADEMY_NEW + EXPECTED_CONVERSATION_NEW
EXPECTED_PRESERVED = 95
EXPECTED_HUBS = 4
EXPECTED_STATIONS = 911
EXPECTED_STATION_INTENTS = 23
EXPECTED_STATION_HTML = EXPECTED_STATIONS * (1 + EXPECTED_STATION_INTENTS) + 1
EXPECTED_TOTAL = EXPECTED_NEW + EXPECTED_PRESERVED + EXPECTED_HUBS + EXPECTED_STATION_HTML
EXPECTED_INDEXABLE = EXPECTED_PRESERVED + EXPECTED_HUBS + EXPECTED_STATION_HTML
EXPECTED_NOINDEX = EXPECTED_NEW
EXPECTED_SITEMAPS = 44
SITEMAP_CHUNK = 500
EXPECTED_REDIRECTS = 74
BASE_URL = "https://englishpt.kr"

OG_PAGE_IMAGES = {
    "englishpt.html": "/assets/images/og/englishpt-home-og.png",
    "courses.html": "/assets/images/og/englishpt-courses-og.png",
    "english-conversation.html": "/assets/images/og/englishpt-conversation-og.png",
    "exam-english.html": "/assets/images/og/englishpt-exam-og.png",
    "student-english.html": "/assets/images/og/englishpt-student-og.png",
    "stations.html": "/assets/images/og/englishpt-courses-og.png",
}

VISUAL_FAMILIES = ["school","school-talk","campus","interview","business","conversation","toeic","speaking","four-skills","digital-test"]

def write_visual_assets(out: Path) -> None:
    assets = out / "assets" / "images"
    assets.mkdir(parents=True, exist_ok=True)
    palettes = {
        "school":("#EAF4F1","#2F7E86","#173038"),
        "school-talk":("#EAF0F5","#536EA7","#192A39"),
        "campus":("#EEF2F5","#4C6987","#1A2937"),
        "interview":("#EDF2F1","#395D68","#17282C"),
        "business":("#F1EEE5","#315F4C","#121A17"),
        "conversation":("#F3EEE8","#B99479","#222920"),
        "toeic":("#EAF1F8","#2867A6","#172A3B"),
        "speaking":("#F1ECF4","#725184","#302438"),
        "four-skills":("#F5ECEE","#8A4653","#38252A"),
        "digital-test":("#EAF3ED","#2D7B5D","#1C3529"),
    }
    labels={
        "school":"BOOK","school-talk":"SPEAK","campus":"PRESENT","interview":"INTERVIEW",
        "business":"MEETING","conversation":"CONVERSATION","toeic":"LC · RC","speaking":"SPEAKING",
        "four-skills":"4 SKILLS","digital-test":"DIGITAL TEST",
    }
    for family in VISUAL_FAMILIES:
        bg,accent,ink=palettes[family]
        for variant in range(1,4):
            shift=variant*24
            svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
<rect width="1200" height="720" fill="{bg}"/>
<circle cx="{955-shift}" cy="{145+shift}" r="{112+variant*8}" fill="{accent}" opacity=".13"/>
<circle cx="{180+shift}" cy="{600-shift}" r="{145-variant*6}" fill="{accent}" opacity=".09"/>
<rect x="95" y="88" width="1010" height="544" rx="38" fill="#fff" stroke="{accent}" stroke-opacity=".20"/>
<rect x="150" y="146" width="360" height="26" rx="13" fill="{accent}" opacity=".16"/>
<rect x="150" y="198" width="245" height="18" rx="9" fill="{ink}" opacity=".10"/>
<rect x="150" y="235" width="300" height="18" rx="9" fill="{ink}" opacity=".08"/>
<rect x="150" y="325" width="395" height="192" rx="26" fill="{bg}" stroke="{accent}" stroke-opacity=".24"/>
<path d="M190 462 C260 {340+shift//3}, 330 {520-shift//4}, 500 370" fill="none" stroke="{accent}" stroke-width="16" stroke-linecap="round"/>
<circle cx="205" cy="430" r="22" fill="{accent}"/><circle cx="340" cy="405" r="22" fill="{accent}" opacity=".72"/><circle cx="490" cy="375" r="22" fill="{accent}" opacity=".46"/>
<rect x="625" y="175" width="365" height="315" rx="30" fill="{ink}"/>
<rect x="662" y="215" width="290" height="190" rx="18" fill="{bg}"/>
<circle cx="807" cy="310" r="58" fill="{accent}" opacity=".20"/>
<path d="M770 315 q37 -55 74 0 q-37 50 -74 0z" fill="{accent}" opacity=".86"/>
<rect x="725" y="440" width="165" height="14" rx="7" fill="#fff" opacity=".55"/>
<text x="150" y="585" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="{accent}" letter-spacing="3">{labels[family]}</text>
</svg>'''
            (assets / f"{family}-{variant}.svg").write_text(svg, encoding="utf-8")



REPRESENTATIVE_IMAGE_FAMILIES = {
    "toeic": {
        "label": "TOEIC · LC / RC",
        "palette": ("#EDF4FA","#2E6FA9","#18334A"),
        "accent2": "#8AB7D8",
    },
    "toeic-speaking": {
        "label": "TOEIC SPEAKING · MIC / TIME",
        "palette": ("#F2EEF7","#725184","#322640"),
        "accent2": "#BCA8CB",
    },
    "opic": {
        "label": "OPIc · STORY / ROLEPLAY",
        "palette": ("#FFF1EA","#C66F3D","#4E2A1E"),
        "accent2": "#E3A27D",
    },
    "ielts": {
        "label": "IELTS · 4 SKILLS / BAND",
        "palette": ("#EAF5F3","#258A83","#173D3A"),
        "accent2": "#8CC8C3",
    },
    "toefl": {
        "label": "TOEFL · R / L / S / W",
        "palette": ("#F1EEFB","#6957A5","#302851"),
        "accent2": "#B1A5D8",
    },
    "english-conv": {
        "label": "ENGLISH CONVERSATION · DAILY SPEAK",
        "palette": ("#FFF2F5","#C05678","#542638"),
        "accent2": "#E8A7BC",
    },
    "adult-conv": {
        "label": "ADULT CONVERSATION · LIFE / TRAVEL",
        "palette": ("#F6F0E9","#A8754E","#4A3525"),
        "accent2": "#D4B394",
    },
    "worker-conv": {
        "label": "BUSINESS SPEAK · MEETING / PRESENT",
        "palette": ("#EEF1EB","#496650","#1D3022"),
        "accent2": "#9EB2A1",
    },
    "beginner-conv": {
        "label": "BEGINNER · START SPEAK",
        "palette": ("#EDF5FB","#3E89B5","#17394F"),
        "accent2": "#9CC9E2",
    },
}


def write_search_image_assets(out: Path, failures: list) -> None:
    """Copy the five approved OG sources and rasterize all search-image candidates to PNG."""
    src_dir = ROOT / "assets" / "images" / "og"
    dst_dir = out / "assets" / "images" / "og"
    dst_dir.mkdir(parents=True, exist_ok=True)
    expected = (
        "englishpt-home-og.svg",
        "englishpt-courses-og.svg",
        "englishpt-conversation-og.svg",
        "englishpt-exam-og.svg",
        "englishpt-student-og.svg",
    )
    for name in expected:
        src = src_dir / name
        if not src.exists():
            failures.append(f"og_source_missing:{name}")
        else:
            shutil.copy2(src, dst_dir / name)

    converter = shutil.which("rsvg-convert")
    if not converter:
        failures.append("rsvg_convert_missing")
        return

    images_root = out / "assets" / "images"
    for svg in sorted(images_root.rglob("*.svg")):
        png = svg.with_suffix(".png")
        proc = subprocess.run(
            [converter, str(svg), "-o", str(png)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        if proc.returncode != 0 or not png.exists() or png.stat().st_size < 5000:
            failures.append({
                "rasterize_failed": str(svg.relative_to(out)),
                "stderr": proc.stderr[-500:],
            })


def _absolute_asset_url(src: str) -> str:
    if src.startswith("https://") or src.startswith("http://"):
        return src
    if not src.startswith("/"):
        src = "/" + src
    return BASE_URL + src


def _pick_search_image(page_name: str, raw: str) -> str:
    if page_name in OG_PAGE_IMAGES:
        return OG_PAGE_IMAGES[page_name]
    if page_name.startswith("station-") and page_name.count("-") == 1:
        return "/assets/images/og/englishpt-courses-og.png"

    m = re.search(
        r'<figure class="learning-visual">.*?<img[^>]+src=["\']([^"\']+)["\']',
        raw, re.I | re.S,
    )
    if not m:
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw, re.I)
    if m:
        src = m.group(1)
        if src.startswith("/assets/images/") or src.startswith("assets/images/"):
            path = "/" + src.lstrip("/")
            if path.lower().endswith(".svg"):
                path = path[:-4] + ".png"
            return path

    lower = page_name.lower()
    fallback_by_intent = (
        ("toeic-speaking", "/assets/images/representative/toeic-speaking-editorial.png"),
        ("toeic", "/assets/images/representative/toeic-editorial.png"),
        ("opic", "/assets/images/representative/opic-editorial.png"),
        ("ielts", "/assets/images/representative/ielts-editorial.png"),
        ("toefl", "/assets/images/representative/toefl-editorial.png"),
        ("duolingo", "/assets/images/representative/duolingo-editorial.png"),
        ("english-conv", "/assets/images/representative/english-conv-editorial.png"),
    )
    for token, path in fallback_by_intent:
        if token in lower:
            return path
    if page_name.startswith("station-"):
        return "/assets/images/og/englishpt-courses-og.png"
    return "/assets/images/og/englishpt-home-og.png"


def _add_schema_image(raw: str, image_url: str) -> tuple[str, bool]:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S | re.I)
    if not m:
        return raw, False
    try:
        data = json.loads(m.group(1))
        changed = False

        def walk(node):
            nonlocal changed
            if isinstance(node, dict):
                typ = node.get("@type")
                types = typ if isinstance(typ, list) else [typ]
                if any(x in ("WebPage", "CollectionPage", "Service", "EducationalOrganization") for x in types):
                    node["image"] = image_url
                    changed = True
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(data)
        if not changed and isinstance(data, dict):
            data["image"] = image_url
            changed = True
        rep = '<script type="application/ld+json">' + json.dumps(
            data, ensure_ascii=False, separators=(",", ":")
        ) + '</script>'
        return raw[:m.start()] + rep + raw[m.end():], changed
    except Exception:
        return raw, False


def apply_search_image_metadata(out: Path, failures: list) -> dict:
    pages = sorted(out.glob("*.html"))
    image_counts: dict[str, int] = {}
    schema_failures = []
    missing_assets = []

    for page in pages:
        raw = page.read_text(encoding="utf-8", errors="ignore")
        rel_image = _pick_search_image(page.name, raw)
        image_url = _absolute_asset_url(rel_image)
        asset = out / rel_image.lstrip("/")
        if not asset.exists():
            missing_assets.append({"file": page.name, "asset": rel_image})

        robots_m = re.search(r'<meta name="robots" content="([^"]+)">', raw, re.I)
        if robots_m:
            robots_tokens = {
                x.strip().lower()
                for x in robots_m.group(1).split(",")
                if x.strip()
            }
            robots_value = (
                "noindex,follow,max-image-preview:large"
                if "noindex" in robots_tokens
                else "index,follow,max-image-preview:large"
            )
            raw = raw[:robots_m.start()] + f'<meta name="robots" content="{robots_value}">' + raw[robots_m.end():]
        else:
            raw = raw.replace(
                "<head>",
                '<head><meta name="robots" content="index,follow,max-image-preview:large">',
                1,
            )

        # Remove any stale image hints before inserting one canonical set.
        raw = re.sub(r'<meta property="og:image(?::[^"]+)?" content="[^"]*">', '', raw, flags=re.I)
        raw = re.sub(r'<meta name="twitter:(?:card|image)" content="[^"]*">', '', raw, flags=re.I)
        raw = re.sub(r'<link rel="image_src" href="[^"]*">', '', raw, flags=re.I)

        title_m = re.search(r'<title>(.*?)</title>', raw, re.S | re.I)
        image_alt = html.unescape(re.sub(r'<[^>]+>', '', title_m.group(1))).strip() if title_m else "ENGLISH PT"
        if "/assets/images/og/" in rel_image:
            width, height = 1200, 630
        else:
            width, height = 1200, 720

        meta = (
            f'<meta property="og:image" content="{html.escape(image_url, quote=True)}">'
            f'<meta property="og:image:width" content="{width}">'
            f'<meta property="og:image:height" content="{height}">'
            '<meta property="og:image:type" content="image/png">'
            f'<meta property="og:image:alt" content="{html.escape(image_alt, quote=True)}">'
            '<meta name="twitter:card" content="summary_large_image">'
            f'<meta name="twitter:image" content="{html.escape(image_url, quote=True)}">'
            f'<link rel="image_src" href="{html.escape(image_url, quote=True)}">'
        )
        marker = re.search(r'<meta property="og:url" content="[^"]*">', raw, re.I)
        if marker:
            raw = raw[:marker.end()] + meta + raw[marker.end():]
        else:
            desc = re.search(r'<meta name="description" content="[^"]*">', raw, re.I)
            if desc:
                raw = raw[:desc.end()] + meta + raw[desc.end():]
            else:
                raw = raw.replace("<head>", "<head>" + meta, 1)

        raw, schema_ok = _add_schema_image(raw, image_url)
        if not schema_ok:
            schema_failures.append(page.name)
        page.write_text(raw, encoding="utf-8")
        image_counts[rel_image] = image_counts.get(rel_image, 0) + 1

    if missing_assets:
        failures.append({"search_image_assets_missing": missing_assets[:50], "count": len(missing_assets)})
    if schema_failures:
        failures.append({"search_image_schema_failed": schema_failures[:50], "count": len(schema_failures)})

    return {
        "html_pages": len(pages),
        "unique_search_images": len(image_counts),
        "image_usage": dict(sorted(image_counts.items(), key=lambda x: (-x[1], x[0]))),
        "missing_assets": len(missing_assets),
        "schema_failures": len(schema_failures),
    }


def write_representative_candidate_assets(out: Path) -> None:
    assets = out / "assets" / "images" / "representative"
    assets.mkdir(parents=True, exist_ok=True)
    for family, spec in REPRESENTATIVE_IMAGE_FAMILIES.items():
        bg, accent, ink = spec["palette"]
        accent2 = spec["accent2"]
        label = spec["label"]
        for variant in range(1,4):
            dx=(variant-2)*28
            dy=(variant-2)*18
            # A people-first abstract tutoring scene: learner + tutor + learning object.
            # It stays intentionally text-light so it works across local pages.
            svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
<rect width="1200" height="720" fill="{bg}"/>
<circle cx="{1020+dx}" cy="{120+dy}" r="150" fill="{accent}" opacity=".10"/>
<circle cx="{155-dx}" cy="{625-dy}" r="175" fill="{accent2}" opacity=".14"/>
<rect x="74" y="64" width="1052" height="592" rx="42" fill="#fff" stroke="{accent}" stroke-opacity=".18"/>
<rect x="120" y="112" width="960" height="64" rx="22" fill="{bg}"/>
<text x="158" y="154" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="{accent}" letter-spacing="1.5">{label}</text>

<!-- tutor -->
<circle cx="{420+dx}" cy="{300+dy}" r="72" fill="{accent2}" opacity=".92"/>
<path d="M{310+dx} {515+dy} q110 -165 220 0 v55 h-220z" fill="{accent2}" opacity=".85"/>
<!-- learner -->
<circle cx="{755-dx}" cy="{290-dy}" r="68" fill="{accent}" opacity=".88"/>
<path d="M{650-dx} {520-dy} q105 -160 210 0 v50 h-210z" fill="{accent}" opacity=".76"/>

<!-- desk / learning object -->
<rect x="265" y="545" width="670" height="34" rx="17" fill="{ink}" opacity=".16"/>
<rect x="{535+dx}" y="{400+dy}" width="190" height="118" rx="12" fill="{ink}" opacity=".90"/>
<rect x="{555+dx}" y="{418+dy}" width="150" height="80" rx="8" fill="{bg}"/>
<path d="M{585+dx} {463+dy} h92" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
<path d="M{600+dx} {488+dy} h62" stroke="{accent2}" stroke-width="8" stroke-linecap="round"/>

<!-- activity accents -->
<circle cx="{355+dx}" cy="{250+dy}" r="10" fill="{accent}"/>
<circle cx="{830-dx}" cy="{232-dy}" r="10" fill="{accent2}"/>
<path d="M{495+dx} {338+dy} C560 290, 650 288, {700-dx} {335-dy}" fill="none" stroke="{accent}" stroke-width="7" stroke-linecap="round" stroke-dasharray="10 14" opacity=".55"/>

<rect x="152" y="606" width="{220+variant*26}" height="14" rx="7" fill="{accent}" opacity=".20"/>
<rect x="152" y="632" width="{330-variant*22}" height="12" rx="6" fill="{ink}" opacity=".10"/>
</svg>'''
            (assets / f"{family}-{variant}.svg").write_text(svg, encoding="utf-8")

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

LIVE_FORM = '''<form id="pilotForm" class="lead-form" name="englishpt-consultation" method="POST" data-netlify="true" data-netlify-honeypot="bot-field"><input type="hidden" name="form-name" value="englishpt-consultation"><input type="hidden" name="subject" data-remove-prefix value="ENGLISH PT 새 상담 신청"><p hidden><label>비워두세요 <input name="bot-field"></label></p>
<label>이름 <span>*</span><input name="name" autocomplete="name" required></label>
<label>연락처 <span>*</span><input name="phone" inputmode="tel" autocomplete="tel" placeholder="010-0000-0000" required></label>
<label class="full">가장 가까운 일정<input name="deadline" placeholder="시험·발표·면접·사용 일정"></label>
<label class="full">가장 막히는 장면<textarea name="difficulty" rows="3" placeholder="최근 어려웠던 문제·응답·상황"></textarea></label>
<label class="privacy-check"><input name="consent" type="checkbox" required><span>상담을 위한 개인정보 수집·이용에 동의합니다. <a href="/privacy/">개인정보처리방침</a></span></label>
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


def simplify_preserved_consultation(raw: str) -> tuple[str, bool]:
    """Keep preserved pages intact except for the shared consultation form contract."""
    if '<form id="leadForm"' not in raw:
        return raw, False
    area_m = re.search(r'id="leadArea"[^>]*value="([^"]*)"', raw, re.I)
    area = html.unescape(area_m.group(1)).strip() if area_m else "송현동"
    h1 = _plain_h1(raw) or "잉글리시PT"
    new_form = CLEAN_RENDERER.consultation_form({"dong": area}, h1)
    updated, n = re.subn(
        r'<form id="leadForm"[^>]*>.*?</form>',
        new_form,
        raw,
        count=1,
        flags=re.S | re.I,
    )
    updated = updated.replace(
        "과정을 먼저 고르지 않아도 됩니다. 현재 목표와 가장 어려운 지점을 남겨주시면 상담에 필요한 내용을 정리해 연락드립니다.",
        "과정을 먼저 고르지 않아도 됩니다. 궁금한 점이나 상담받고 싶은 내용을 자유롭게 남겨주세요.",
    )
    return updated, n == 1


PRESERVED_EASY_REPLACEMENTS = {
    "장면": "상황",
    "판단라는 기준": "판단 기준",
    "답변 시작로": "답변 시작으로",
    "이유 확장로": "이유 확장으로",
    "academic performance": "수업과 평가 방식",
    "adaptive format": "난이도가 달라지는 시험 방식",
    "productive response": "직접 말하기·쓰기 응답",
    "open response": "직접 답하는 문제",
    "발화 명료성": "말이 또렷하게 들리는지",
    "문항 요구": "문제가 무엇을 묻는지",
    "입력정보": "읽거나 들은 정보",
    "스크립트": "외운 답변",
    "병목": "가장 어려운 부분",
    "태깅": "원인별로 구분",
    "재검증": "다시 확인",
    "재평가": "다시 확인",
    "재작성": "다시 쓰기",
    "재답변": "다시 답하기",
}

PRESERVED_EXAM_SUFFIXES = [
    ("toeic-speaking", "toeic-speaking"),
    ("duolingo", "duolingo"),
    ("ielts", "ielts"),
    ("toefl", "toefl"),
    ("opic", "opic"),
    ("toeic", "toeic"),
]


def preserved_exam_base(name: str) -> str | None:
    stem = name[:-5] if name.endswith(".html") else name
    for token, base in PRESERVED_EXAM_SUFFIXES:
        if (
            stem.endswith("-" + token)
            or stem.endswith("-academy-" + token)
            or stem.endswith("-1to1-" + token)
        ):
            return base
    return None


def humanize_preserved_page(raw: str, name: str) -> str:
    for old, new in PRESERVED_EASY_REPLACEMENTS.items():
        raw = raw.replace(old, new)

    base = preserved_exam_base(name)
    if not base or 'data-beginner-guide="true"' in raw:
        return raw

    h1 = _plain_h1(raw) or "영어 시험 준비"
    parts = h1.split(maxsplit=1)
    dong = parts[0] if parts else "해당 지역"
    service = parts[1] if len(parts) > 1 else {
        "toeic":"토익과외",
        "toeic-speaking":"토익스피킹과외",
        "opic":"오픽과외",
        "ielts":"아이엘츠과외",
        "duolingo":"듀오링고영어테스트",
        "toefl":"토플과외",
    }[base]
    loc = {"slug": Path(name).stem, "dong": dong, "service": service}
    guide = CLEAN_RENDERER.beginner_exam_guide(base, loc)

    detail_marker = '<section id="detail"'
    if detail_marker in raw:
        return raw.replace(detail_marker, guide + detail_marker, 1)

    hero = re.search(r'<section class="hero[^"]*">.*?</section>', raw, flags=re.S | re.I)
    if hero:
        return raw[:hero.end()] + guide + raw[hero.end():]
    return guide + raw


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
        'name="englishpt-consultation"',
        'data-netlify="true"',
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
    if q8.get("counts", {}).get("new_pages") != EXPECTED_SOURCE_NEW:
        failures.append("stage8_source_new_page_count")
    if q8.get("counts", {}).get("preserved_pages") != EXPECTED_PRESERVED:
        failures.append("stage8_preserved_page_count")
    if q8.get("counts", {}).get("deploy_html_total") != EXPECTED_SOURCE_NEW + EXPECTED_PRESERVED:
        failures.append("stage8_source_total_page_count")

    rollback = stage7 / "rollback-root"
    if not rollback.exists():
        failures.append("rollback_root_missing")
    else:
        shutil.copytree(rollback, out, dirs_exist_ok=True)
        for preserved_page in sorted(out.glob("*.html")):
            preserved_raw = preserved_page.read_text(encoding="utf-8")
            preserved_raw, changed = simplify_preserved_consultation(preserved_raw)
            preserved_raw = humanize_preserved_page(preserved_raw, preserved_page.name)
            if preserved_page.name == "englishpt.html":
                preserved_raw = preserved_raw.replace(
                    "잉글리시PT / 1:1 맞춤 영어관리 | ENGLISH PT",
                    "1:1 영어과외·영어회화·시험영어 | 잉글리시PT",
                )
                preserved_raw = preserved_raw.replace(
                    "영어를 PT처럼 진단하고 훈련하고 기록하고 다시 조정하는 ENGLISH PT. 회화·시험·학교 영어를 현재 상태와 목표에 맞춰 1:1로 관리합니다.",
                    "영어회화부터 토익·토익스피킹·오픽·아이엘츠·토플까지, 현재 수준과 목표에 맞춰 필요한 영역을 1:1로 진단하고 훈련하는 잉글리시PT입니다.",
                )
            preserved_page.write_text(preserved_raw, encoding="utf-8")

    current_home = ROOT / "englishpt.html"
    if not current_home.exists():
        failures.append("current_homepage_missing")
    else:
        shutil.copy2(current_home, out / "englishpt.html")

    national_hubs = (
        "courses.html",
        "english-conversation.html",
        "exam-english.html",
        "student-english.html",
    )
    for hub_name in national_hubs:
        hub_src = ROOT / hub_name
        if not hub_src.exists():
            failures.append(f"national_hub_missing:{hub_name}")
        else:
            shutil.copy2(hub_src, out / hub_name)

    new_pages = sorted((work / "stage5-full-generation").glob("shard-*/pages/*.html"))
    if len(new_pages) != EXPECTED_SOURCE_NEW:
        failures.append({"source_new_pages": [len(new_pages), EXPECTED_SOURCE_NEW]})

    transformed_source = 0
    transformed_academy = 0
    transformed_conversation = 0
    bad_robot_pages: list[str] = []
    bad_domain_pages: list[str] = []
    bad_ui_pages: list[dict] = []

    def write_checked(name: str, raw: str, ui_problems: list[str]) -> None:
        if ui_problems:
            bad_ui_pages.append({"file": name, "problems": ui_problems})
        robots_m = re.search(r'<meta name="robots" content="([^"]+)">', raw, re.I)
        robots_tokens = {
            x.strip().lower()
            for x in (robots_m.group(1).split(",") if robots_m else [])
            if x.strip()
        }
        if not robots_m or "follow" not in robots_tokens or not ({"index","noindex"} & robots_tokens):
            bad_robot_pages.append(name)
        canonical = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', raw, re.I)
        if not canonical or not canonical.group(1).startswith(BASE_URL + "/"):
            bad_domain_pages.append(name)
        (out / name).write_text(raw, encoding="utf-8")

    derived_by_base: dict[str, list[tuple[str, str]]] = {}
    for academy, base in CLEAN_RENDERER.ACADEMY_BASE.items():
        derived_by_base.setdefault(base, []).append(("academy", academy))
    for derived, base in CLEAN_RENDERER.CONV_DERIVED_BASE.items():
        derived_by_base.setdefault(base, []).append(("conversation", derived))

    for src in new_pages:
        source_raw = src.read_text(encoding="utf-8")
        raw, ui_problems = CLEAN_RENDERER.render_production_page(source_raw, src.name)
        write_checked(src.name, raw, ui_problems)
        transformed_source += 1

        _, source_intent = CLEAN_RENDERER.intent_from_name(src.name)
        for derived_kind, derived_intent in derived_by_base.get(source_intent, []):
            derived_name = src.name[:-len(source_intent + ".html")] + derived_intent + ".html"
            if derived_kind == "academy":
                derived_raw, derived_problems = CLEAN_RENDERER.render_academy_page(
                    source_raw, src.name, derived_intent
                )
                transformed_academy += 1
            else:
                derived_raw, derived_problems = CLEAN_RENDERER.render_conversation_derived_page(
                    source_raw, src.name, derived_intent
                )
                transformed_conversation += 1
            write_checked(derived_name, derived_raw, derived_problems)

    station_report = STATION_RENDERER.render_all(out)
    if station_report.get("status") != "PASS_STATION_RENDER":
        failures.append({"station_render": station_report})
    if station_report.get("total_station_html") != EXPECTED_STATION_HTML:
        failures.append({"station_html": [station_report.get("total_station_html"), EXPECTED_STATION_HTML]})

    first_pages_dir = next(iter((work / "stage5-full-generation").glob("shard-*/pages")), None)
    if first_pages_dir:
        for asset in ("pilot.css", "pilot.js"):
            src = first_pages_dir / asset
            if src.exists():
                shutil.copy2(src, out / asset)
    write_visual_assets(out)
    write_representative_candidate_assets(out)

    # Keep user-approved editorial thumbnails as fixed branch assets.
    custom_rep_src = ROOT / "assets" / "images" / "representative"
    custom_rep_dst = out / "assets" / "images" / "representative"
    custom_rep_dst.mkdir(parents=True, exist_ok=True)
    for name in (
        "toeic-editorial.svg",
        "toeic-speaking-editorial.svg",
        "opic-editorial.svg",
        "ielts-editorial.svg",
        "duolingo-editorial.svg",
        "toefl-editorial.svg",
        "english-conv-editorial.svg",
    ):
        src = custom_rep_src / name
        if not src.exists():
            failures.append(f"custom_representative_missing:{name}")
        else:
            shutil.copy2(src, custom_rep_dst / name)

    # Rasterize only after every generated and editorial SVG candidate is present.
    write_search_image_assets(out, failures)

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

    # Preserved pages use the shared branch-side consultation JavaScript.
    preserved_assets = out / "assets"
    preserved_assets.mkdir(parents=True, exist_ok=True)
    current_site_js = ROOT / "assets" / "site.js"
    current_site_css = ROOT / "assets" / "styles.css"
    if not current_site_js.exists():
        failures.append("preserved_site_js_missing")
    else:
        shutil.copy2(current_site_js, preserved_assets / "site.js")
    if not current_site_css.exists():
        failures.append("preserved_styles_css_missing")
    else:
        shutil.copy2(current_site_css, preserved_assets / "styles.css")

    # Shared nationwide locality selector data: 5,149 verified localities.
    locality_index = preserved_assets / "locality-index.json"
    proc = subprocess.run(
        ["python3", str(ROOT / "scripts" / "build-locality-index.py"), "--output", str(locality_index)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    if proc.returncode != 0 or not locality_index.exists():
        failures.append({"locality_index_build_failed": proc.stderr[-800:]})
    else:
        try:
            locality_rows = json.loads(locality_index.read_text(encoding="utf-8"))
            if len(locality_rows) != 5149:
                failures.append({"locality_index_rows": [len(locality_rows), 5149]})
        except Exception as exc:
            failures.append({"locality_index_invalid": str(exc)})

    # Build the nationwide 5,149-locality selector used by the home and hub navigation.
    locality_index = preserved_assets / "locality-index.json"
    proc = subprocess.run(
        [
            "python3", str(ROOT / "scripts" / "build-locality-index.py"),
            "--output", str(locality_index),
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    if proc.returncode != 0 or not locality_index.exists():
        failures.append({
            "locality_index_build_failed": proc.returncode,
            "stderr": proc.stderr[-1000:],
        })
    else:
        try:
            locality_rows = json.loads(locality_index.read_text(encoding="utf-8"))
            if len(locality_rows) != 5149:
                failures.append({"locality_index_rows": [len(locality_rows), 5149]})
        except Exception as exc:
            failures.append({"locality_index_parse": str(exc)})

    locality_builder = ROOT / "scripts" / "build-locality-index.py"
    locality_index = preserved_assets / "locality-index.json"
    if not locality_builder.exists():
        failures.append("locality_index_builder_missing")
    else:
        proc = subprocess.run(
            ["python3", str(locality_builder), "--output", str(locality_index)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        if proc.returncode != 0 or not locality_index.exists():
            failures.append({"locality_index_build_failed": proc.stderr[-1000:]})

    # Stage 9 AI/search discovery files are controlled by the current branch,
    # not by the older Stage 8 approval packet.
    discovery_files = {
        "robots.txt": ROOT / "robots.txt",
        "llms.txt": ROOT / "llms.txt",
    }
    for name, src in discovery_files.items():
        if not src.exists():
            failures.append(f"discovery_file_missing:{name}")
        else:
            shutil.copy2(src, out / name)

    # Current-branch operational assets must override the older Stage 8 packet.
    for name in ("_headers",):
        src = ROOT / name
        if not src.exists():
            failures.append(f"operational_file_missing:{name}")
        else:
            shutil.copy2(src, out / name)

    favicon_src = ROOT / "assets" / "favicon.svg"
    if not favicon_src.exists():
        failures.append("favicon_missing")
    else:
        shutil.copy2(favicon_src, preserved_assets / "favicon.svg")

    privacy_src = ROOT / "privacy"
    if not privacy_src.exists():
        failures.append("privacy_page_missing")
    else:
        shutil.copytree(privacy_src, out / "privacy", dirs_exist_ok=True)

    def apply_sitewide_operational_markup(raw: str) -> str:
        raw = raw.replace(
            '<script defer src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4/dist/email.min.js"></script>',
            '',
        ).replace(
            '<script defer src="https://cdn.jsdelivr.net/npm/@emailjs/browser@4.4.1/dist/email.min.js"></script>',
            '',
        )
        if 'rel="icon"' not in raw and "</head>" in raw:
            raw = raw.replace(
                "</head>",
                '<link rel="icon" href="https://englishpt.kr/assets/favicon.svg" type="image/svg+xml"></head>',
                1,
            )
        if "<footer" in raw and 'href="/privacy/"' not in raw.split("</footer>",1)[0].split("<footer",1)[-1]:
            raw = raw.replace(
                "</footer>",
                '<div class="wrap"><p class="foot-note"><a href="/privacy/">개인정보처리방침</a></p></div></footer>',
                1,
            )
        if 'class="privacy-detail"' in raw:
            raw = raw.replace(
                "관계 법령상 보존 의무가 없는 한 지체 없이 파기합니다.</p>",
                '관계 법령상 보존 의무가 없는 한 지체 없이 파기합니다. 자세한 내용은 <a href="/privacy/">개인정보처리방침</a>에서 확인할 수 있습니다.</p>',
            )
        robots_m = re.search(r'<meta name="robots" content="([^"]+)">', raw, re.I)
        robots_tokens = {
            x.strip().lower()
            for x in (robots_m.group(1).split(",") if robots_m else [])
            if x.strip()
        }
        if "noindex" not in robots_tokens:
            desc_m = re.search(r'<meta name="description" content="([^"]*)">', raw, re.I)
            if desc_m:
                current_desc = html.unescape(desc_m.group(1)).strip()
                if len(current_desc) > 80:
                    h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', raw, re.S | re.I)
                    subject = (
                        html.unescape(re.sub(r'<[^>]+>', ' ', h1_m.group(1))).strip()
                        if h1_m else ""
                    )
                    subject = re.sub(r'\s+', ' ', subject)
                    new_desc = f"{subject} 안내. 현재 수준과 목표에 맞춰 필요한 학습 방향과 상담 기준을 확인하세요."
                    if len(new_desc) > 80:
                        new_desc = f"{subject} 안내. 현재 수준과 목표에 맞는 학습 방향을 확인하세요."
                    raw = raw[:desc_m.start()] + f'<meta name="description" content="{html.escape(new_desc, quote=True)}">' + raw[desc_m.end():]
                    raw = re.sub(
                        r'<meta property="og:description" content="[^"]*">',
                        f'<meta property="og:description" content="{html.escape(new_desc, quote=True)}">',
                        raw,
                        count=1,
                        flags=re.I,
                    )
                    schema_m = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
                    if schema_m:
                        try:
                            data = json.loads(schema_m.group(1))
                            graph = data.get("@graph") if isinstance(data, dict) else None
                            if isinstance(graph, list):
                                for node in graph:
                                    if isinstance(node, dict) and node.get("@type") in ("WebPage","CollectionPage"):
                                        node["description"] = new_desc
                                rep = '<script type="application/ld+json">' + json.dumps(data,ensure_ascii=False,separators=(",",":")) + '</script>'
                                raw = raw[:schema_m.start()] + rep + raw[schema_m.end():]
                        except Exception:
                            pass
        return raw

    for page in sorted(out.glob("*.html")):
        page.write_text(
            apply_sitewide_operational_markup(page.read_text(encoding="utf-8", errors="ignore")),
            encoding="utf-8",
        )

    search_image_report = apply_search_image_metadata(out, failures)

    # Rebuild sitemaps from the exact final HTML set because Stage 9 adds
    # five exam-academy intents plus four conversation-search intents per locality.
    old_sitemap = out / "sitemap.xml"
    if old_sitemap.exists():
        old_sitemap.unlink()
    sitemap_dir = out / "sitemaps"
    if sitemap_dir.exists():
        shutil.rmtree(sitemap_dir)
    sitemap_dir.mkdir(parents=True)

    html_files = sorted(out.glob("*.html"))
    if len(html_files) != EXPECTED_TOTAL:
        failures.append({"deploy_html_total": [len(html_files), EXPECTED_TOTAL]})

    all_canonical_urls: list[str] = []
    canonical_urls: list[str] = []
    noindex_pages: list[str] = []
    for page in html_files:
        raw = page.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', raw, re.I)
        if not m:
            failures.append({"canonical_missing": page.name})
            continue
        url = m.group(1)
        all_canonical_urls.append(url)
        robots_m = re.search(r'<meta name="robots" content="([^"]+)">', raw, re.I)
        robots_tokens = {
            x.strip().lower()
            for x in (robots_m.group(1).split(",") if robots_m else [])
            if x.strip()
        }
        if "noindex" in robots_tokens:
            noindex_pages.append(page.name)
        elif "index" in robots_tokens:
            canonical_urls.append(url)
        else:
            failures.append({"robots_indexing_state_missing": page.name})

    all_canonical_urls = sorted(set(all_canonical_urls))
    canonical_urls = sorted(set(canonical_urls))
    if len(all_canonical_urls) != EXPECTED_TOTAL:
        failures.append({"unique_canonical_urls": [len(all_canonical_urls), EXPECTED_TOTAL]})
    if len(canonical_urls) != EXPECTED_INDEXABLE:
        failures.append({"indexable_canonical_urls": [len(canonical_urls), EXPECTED_INDEXABLE]})
    if len(noindex_pages) != EXPECTED_NOINDEX:
        failures.append({"noindex_pages": [len(noindex_pages), EXPECTED_NOINDEX]})

    for shard_no, offset in enumerate(range(0, len(canonical_urls), SITEMAP_CHUNK), 1):
        urls = canonical_urls[offset:offset + SITEMAP_CHUNK]
        body = ''.join(f'<url><loc>{html.escape(url)}</loc></url>' for url in urls)
        (sitemap_dir / f'sitemap-{shard_no:03d}.xml').write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + body + '</urlset>\n',
            encoding="utf-8",
        )

    sitemap_files = sorted(sitemap_dir.glob("sitemap-*.xml"))
    if len(sitemap_files) != EXPECTED_SITEMAPS:
        failures.append({"sitemap_shards": [len(sitemap_files), EXPECTED_SITEMAPS]})

    sitemap_index_body = ''.join(
        f'<sitemap><loc>{BASE_URL}/sitemaps/{p.name}</loc></sitemap>'
        for p in sitemap_files
    )
    (out / "sitemap-index.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + sitemap_index_body + '</sitemapindex>\n',
        encoding="utf-8",
    )

    sitemap_urls = len(canonical_urls)
    if sitemap_urls != EXPECTED_INDEXABLE:
        failures.append({"sitemap_urls": [sitemap_urls, EXPECTED_INDEXABLE]})
    index = (out / "sitemap-index.xml").read_text(encoding="utf-8")
    if index.count("<sitemap><loc>") != EXPECTED_SITEMAPS:
        failures.append("sitemap_index_count")
    if f"{BASE_URL}/sitemaps/" not in index:
        failures.append("sitemap_index_domain")

    robots = (out / "robots.txt").read_text(encoding="utf-8")
    if "Disallow: /" in robots:
        failures.append("robots_blocks_all")
    if f"Sitemap: {BASE_URL}/sitemap-index.xml" not in robots:
        failures.append("robots_sitemap_mismatch")
    for agent in ("OAI-SearchBot","Googlebot","Google-Extended","Yeti"):
        if f"User-agent: {agent}" not in robots:
            failures.append(f"robots_missing_agent:{agent}")

    llms_path = out / "llms.txt"
    if not llms_path.exists():
        failures.append("llms_missing")
        llms = ""
    else:
        llms = llms_path.read_text(encoding="utf-8")
        for required in (
            "https://englishpt.kr/englishpt.html",
            "https://englishpt.kr/sitemap-index.xml",
            "physical branch or office",
            "Academy-keyword pages",
        ):
            if required not in llms:
                failures.append(f"llms_contract_missing:{required}")

    # Naver's nosourceinfo opts pages out of AI-generated source descriptions.
    if any("nosourceinfo" in p.read_text(encoding="utf-8", errors="ignore").lower() for p in html_files):
        failures.append("nosourceinfo_present")

    current_404 = ROOT / "404.html"
    if not current_404.exists():
        failures.append("custom_404_missing")
    else:
        shutil.copy2(current_404, out / "404.html")

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
            "source_pages": transformed_source,
            "academy_pages": transformed_academy,
            "conversation_pages": transformed_conversation,
            "new_pages": transformed_source + transformed_academy + transformed_conversation,
            "station_hubs": station_report.get("station_hubs"),
            "station_course_pages": station_report.get("station_course_pages"),
            "station_index_pages": station_report.get("station_index"),
            "station_html_total": station_report.get("total_station_html"),
            "search_image_metadata": search_image_report,
            "html_total": len(html_files),
            "sitemap_shards": len(sitemap_files),
            "sitemap_urls": sitemap_urls,
            "redirect_rules": len(rules),
        },
        "indexing": {
            "mass_page_robots": "noindex,follow,max-image-preview:large",
            "station_and_core_robots": "index,follow,max-image-preview:large",
            "indexable_pages": len(canonical_urls),
            "noindex_pages": len(noindex_pages),
            "robots_contract_failures": len(set(bad_robot_pages)),
            "robots_txt_allows_crawl": "Disallow: /" not in robots,
            "production_ui_failures": len(bad_ui_pages),
        },
        "ai_discovery": {
            "oai_searchbot_allowed": "User-agent: OAI-SearchBot" in robots,
            "googlebot_allowed": "User-agent: Googlebot" in robots,
            "google_extended_allowed": "User-agent: Google-Extended" in robots,
            "yeti_allowed": "User-agent: Yeti" in robots,
            "llms_txt_present": bool(llms),
            "nosourceinfo_present": False,
            "entity_graph": "EducationalOrganization + WebSite + WebPage + Service + BreadcrumbList",
        },
        "source": {
            "stage7_status": q7.get("status"),
            "stage8_status": q8.get("status"),
            "mass_renderer": "stage9-clean-gold-v1",
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
