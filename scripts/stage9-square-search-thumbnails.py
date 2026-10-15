#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate 1200x630 crop-safe Korean Open Graph social previews for ENGLISH PT.

Stage contract
- 29 master designs: 1 main + 5 hubs + 23 course intents.
- Korean-first copy; no teacher/person/emoji artwork.
- Indexable pages receive page-specific images with the page H1 automatically inserted.
- noindex pages use the matching master image until they become indexable.
- Output is deterministic PNG so the same page always receives the same visual.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from functools import lru_cache
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - CI installs Pillow before use.
    raise SystemExit("Pillow is required: python -m pip install pillow") from exc

BASE_URL = "https://englishpt.kr"
SIZE = 1200
BRAND = "잉글리시PT"

# key -> title, subtitle, chips, palette(bg, ink, accent, soft)
MASTER = {
    "main": ("1:1 맞춤 영어 수업", "왕초보부터 시험영어까지", ["영어회화","시험영어","학생영어","무료 PT 진단"], ("#F4FAF5","#123D32","#2E7D5A","#DDF1E4")),
    "hub-courses": ("나에게 맞는 영어 과정 찾기", "목적에 맞는 수업 안내", ["회화","시험","학생영어","맞춤추천"], ("#F3F8FC","#173B6D","#3D74A8","#DDEAF5")),
    "hub-conversation": ("영어회화 과정 한눈에 보기", "회화 목적별 수업 안내", ["왕초보","성인회화","직장인","비즈니스"], ("#F3FAF5","#174B3A","#2E8A63","#DCF2E5")),
    "hub-exam": ("시험영어 과정 한눈에 보기", "목표 점수별 준비 안내", ["토익","오픽","아이엘츠","토플"], ("#FFF4F4","#721B25","#A83243","#F6DDE0")),
    "hub-student": ("학생영어 과정 한눈에 보기", "학년별 맞춤 영어 안내", ["초등","중학생","고등학생","대학생"], ("#FFF8EA","#7A3A10","#C56A21","#F7E6C9")),
    "hub-stations": ("가까운 역에서 영어 수업 찾기", "역 기준으로 편하게 탐색", ["역으로 찾기","지역탐색","가까운수업"], ("#F1F8F6","#183F50","#2E7A70","#DCEFEB")),

    "beginner-english-conv": ("왕초보영어회화", "기초부터 시작하는 회화", ["인사","자기소개","쉬운표현"], ("#F3FAF5","#174B3A","#2E8A63","#DCF2E5")),
    "english-conv-academy": ("영어회화학원", "회화 방향 먼저 정리", ["회화수업","레벨진단","맞춤안내"], ("#F3FAF5","#174B3A","#2E8A63","#DCF2E5")),
    "adult-english-conv-academy": ("성인영어회화", "생활영어부터 차근차근", ["성인회화","실용영어","여행영어"], ("#FFF8EC","#70451D","#B37A42","#F3E5CF")),
    "worker-english-conv-academy": ("직장인영어회화", "바쁜 일정에 맞춘 수업", ["직장인","실전회화","일정조율"], ("#F2F7FC","#183B6C","#386FA4","#DDEAF6")),
    "biz-business-conv": ("비즈니스영어", "업무 상황 중심 영어", ["회의","이메일","발표"], ("#F2F7FC","#183B6C","#386FA4","#DDEAF6")),
    "housewife-conv": ("주부영어회화", "부담 없이 시작하는 회화", ["생활영어","기초회화","편한수업"], ("#FFF8EC","#7C4B24","#C17E45","#F2E3CD")),
    "univ-conv": ("대학생영어회화", "발표·교환학생 준비 회화", ["대학생","발표","회화연습"], ("#F8F3FF","#54327C","#7E59A6","#E9DDF7")),
    "jobseeker-conv": ("취준생영어회화", "면접 대비 영어회화", ["취준생","면접영어","자기소개"], ("#F2F8F7","#194F4A","#2B7B70","#DCEFEB")),
    "elem-tutor": ("초등영어과외", "흥미와 기초를 함께", ["초등영어","읽기","말하기"], ("#FFF8E9","#83411A","#D2752B","#F7E6C6")),
    "mid-conv": ("중학생영어회화", "학교영어와 말하기 연결", ["중학생","학교영어","회화"], ("#F3FAF5","#174B3A","#2E8A63","#DCF2E5")),
    "high-conv": ("고등학생영어회화", "필요한 표현부터 정리", ["고등학생","말하기","실전표현"], ("#F8F3FF","#54327C","#7E59A6","#E9DDF7")),

    "toeic": ("토익과외", "1:1 맞춤 토익 준비", ["LC","RC","오답관리"], ("#FFF4F4","#741C24","#B43642","#F5DDE0")),
    "toeic-academy": ("토익학원", "점수 목표 중심 준비", ["점수목표","전략","파트분석"], ("#F2F7FC","#163C6C","#3B73AA","#DCE9F5")),
    "toeic-speaking": ("토익스피킹과외", "실전 말하기 중심 준비", ["발화연습","답변구성","파트대응"], ("#FFF4F6","#7C1F36","#BD405A","#F6DDE4")),
    "toeic-speaking-academy": ("토익스피킹학원", "목표 등급 중심 준비", ["등급목표","파트연습","말하기"], ("#F8F3FF","#503078","#7B58A3","#E9DDF7")),
    "opic": ("오픽과외", "IH·AL 목표 중심 준비", ["IH","AL","돌발주제"], ("#F8F3FF","#4A2D79","#7754A9","#E8DCF7")),
    "opic-academy": ("오픽학원", "목표 등급별 준비 안내", ["등급목표","질문대응","실전훈련"], ("#F2F7FC","#173B6C","#3B72A5","#DDEAF6")),
    "ielts": ("아이엘츠과외", "1:1 맞춤 아이엘츠", ["듣기","읽기","쓰기","말하기"], ("#FFF4F4","#761D27","#B43A49","#F5DDE0")),
    "ielts-academy": ("아이엘츠학원", "목표 Band 중심 준비", ["Band 목표","유학준비","영역별보완"], ("#F8F3FF","#51327B","#7D5AA7","#E9DDF7")),
    "toefl": ("토플과외", "목표 점수 맞춤 준비", ["읽기","듣기","말하기","쓰기"], ("#F2F7FC","#173C6C","#3D74A8","#DCEAF6")),
    "toefl-academy": ("토플학원", "유학 목표 중심 준비", ["점수목표","유학준비","전략설계"], ("#F8F3FF","#51327B","#7D5AA7","#E9DDF7")),
    "duolingo": ("듀오링고과외", "빠르게 준비하는 시험 대비", ["실전대비","유형적응","목표점수"], ("#F3FAF5","#174B3A","#2E8A63","#DCF2E5")),
    "duolingo-academy": ("듀오링고학원", "준비 흐름 정리", ["유형이해","적응훈련","실전연습"], ("#FFF8E9","#803B17","#C96A24","#F7E5C4")),
}

CORE_PAGE_KEYS = {
    "englishpt.html": "main",
    "courses.html": "hub-courses",
    "english-conversation.html": "hub-conversation",
    "exam-english.html": "hub-exam",
    "student-english.html": "hub-student",
    "stations.html": "hub-stations",
}
COURSE_KEYS = [k for k in MASTER if k not in {"main","hub-courses","hub-conversation","hub-exam","hub-student","hub-stations"}]
COURSE_KEYS.sort(key=len, reverse=True)

def strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def get_h1(raw: str) -> str:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S | re.I)
    return strip_tags(m.group(1)) if m else ""

def is_indexable(raw: str) -> bool:
    m = re.search(r'<meta\s+name=["\']robots["\']\s+content=["\']([^"\']+)["\']', raw, re.I)
    if not m:
        return True
    return "noindex" not in {x.strip().lower() for x in m.group(1).split(",")}

def page_key(name: str) -> str:
    if name in CORE_PAGE_KEYS:
        return CORE_PAGE_KEYS[name]
    if name.startswith("station-"):
        for intent in COURSE_KEYS:
            if name.endswith("-" + intent + ".html"):
                return intent
        return "hub-stations"
    for intent in COURSE_KEYS:
        if name.endswith("-" + intent + ".html"):
            return intent
    return "main"

def page_title(raw: str, key: str, specific: bool) -> str:
    if specific:
        h1 = get_h1(raw)
        if h1:
            return h1
    return MASTER[key][0]

@lru_cache(maxsize=4)
def font_path(weight: str) -> str:
    candidates = {
        "bold": [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Bold.otf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "C:/Windows/Fonts/malgunbd.ttf",
        ],
        "regular": [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "C:/Windows/Fonts/malgun.ttf",
        ],
    }
    for p in candidates[weight]:
        if Path(p).exists():
            return p
    raise RuntimeError("Korean font not found. CI must install fonts-noto-cjk.")

@lru_cache(maxsize=512)
def _font(weight: str, size: int):
    return ImageFont.truetype(font_path(weight), size)


def fit_font(text: str, max_width: int, start: int, minimum: int = 44):
    p = font_path("bold")
    for size in range(start, minimum - 1, -2):
        f = _font("bold", size)
        if ImageDraw.Draw(Image.new("RGB",(10,10))).textbbox((0,0), text, font=f)[2] <= max_width:
            return f
    return _font("bold", minimum)

def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int = 2) -> list[str]:
    words = text.split()
    if not words:
        return [text]
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textbbox((0,0), test, font=font)[2] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) <= max_lines:
        return lines
    # Korean H1 often has no spaces around the keyword; character fallback.
    chars = text.replace(" ", "")
    lines, cur = [], ""
    for ch in chars:
        test = cur + ch
        if draw.textbbox((0,0), test, font=font)[2] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = ch
            if len(lines) == max_lines - 1:
                break
    rest_start = sum(len(x) for x in lines)
    remain = chars[rest_start:]
    if remain:
        cur = remain
        while draw.textbbox((0,0), cur, font=font)[2] > max_width and len(cur) > 1:
            cur = cur[:-1]
    lines.append(cur)
    return lines[:max_lines]

def icon(draw: ImageDraw.ImageDraw, key: str, accent: str, soft: str) -> None:
    # Object-only motif; intentionally no people, faces, teacher characters, or emoji.
    x0,y0,x1,y1 = 805,355,1090,650
    draw.rounded_rectangle((x0,y0,x1,y1), 42, fill=soft)
    if key == "hub-stations":
        draw.line((855,565,1035,430), fill=accent, width=22)
        draw.ellipse((975,365,1055,445), outline=accent, width=18)
        draw.ellipse((998,388,1032,422), fill=accent)
    elif key in {"hub-exam","toeic","toeic-academy","ielts","ielts-academy","toefl","toefl-academy","duolingo","duolingo-academy"} or "speaking" in key or key.startswith("opic"):
        draw.ellipse((880,410,1015,545), outline=accent, width=22)
        draw.ellipse((920,450,975,505), outline=accent, width=16)
        draw.line((947,477,1050,390), fill=accent, width=16)
    elif key in {"hub-student","elem-tutor","mid-conv","high-conv","univ-conv"}:
        draw.rectangle((860,430,1035,565), outline=accent, width=18)
        draw.line((880,470,1010,470), fill=accent, width=12)
        draw.line((880,515,980,515), fill=accent, width=12)
    else:
        draw.rounded_rectangle((860,425,1038,540), 34, outline=accent, width=18)
        draw.ellipse((900,475,920,495), fill=accent)
        draw.ellipse((940,475,960,495), fill=accent)
        draw.ellipse((980,475,1000,495), fill=accent)

def draw_thumb(path: Path, key: str, title: str, subtitle: str, chips: list[str]) -> None:
    """Render a genuine 1200x630 landscape OG image, with a center-square safe area.

    Some social platforms crop landscape cards into a centered square. Every
    semantic element stays inside x=300..900; side artwork is decorative only.
    No resize/crop of a square poster and no cut-off of the page H1.
    """
    width, height = 1200, 630
    safe_left, safe_right = 306, 894
    bg, ink, accent, soft = MASTER[key][3]
    im = Image.new("RGB", (width, height), bg)
    d = ImageDraw.Draw(im)

    # Balanced side decoration: none of it contains important text.
    d.ellipse((-165, -145, 295, 315), fill=soft)
    d.ellipse((950, 310, 1360, 720), fill=soft)
    d.rounded_rectangle((100, 240, 220, 378), radius=22, outline=accent, width=9)
    d.line((132, 288, 188, 288), fill=accent, width=8)
    d.line((132, 320, 178, 320), fill=accent, width=8)
    d.ellipse((978, 178, 1080, 280), outline=accent, width=12)
    d.ellipse((1014, 214, 1044, 244), fill=accent)
    d.rounded_rectangle((970, 335, 1100, 354), radius=8, fill=accent)
    d.rounded_rectangle((970, 372, 1062, 391), radius=8, fill=accent)

    def centered(text: str, y: int, font, color: str) -> None:
        box = d.textbbox((0, 0), text, font=font)
        text_width = box[2] - box[0]
        d.text(((width - text_width) // 2, y), text, font=font, fill=color)

    def split_to_width(text: str, font, max_width: int) -> list[str]:
        lines = []
        current = ""
        # Character-level fallback means long Korean place names never spill
        # beyond the safe width, even when they contain no spaces.
        for character in text:
            candidate = (current + character).lstrip()
            if d.textbbox((0, 0), candidate, font=font)[2] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current.rstrip())
                current = character.strip()
        if current:
            lines.append(current.rstrip())
        return lines or [""]

    brand_font = _font("bold", 30)
    centered("ENGLISH PT  |  잉글리시PT", 78, brand_font, accent)
    d.line((safe_left + 50, 132, safe_right - 50, 132), fill=accent, width=3)

    max_title_width = 530
    title_font = _font("bold", 26)
    title_lines = split_to_width(title, title_font, max_title_width)
    for font_size in range(70, 23, -2):
        possible_font = _font("bold", font_size)
        possible_lines = split_to_width(title, possible_font, max_title_width)
        if len(possible_lines) <= 4 and len(possible_lines) * int(font_size * 1.20) <= 236:
            title_font, title_lines = possible_font, possible_lines
            break
    if len(title_lines) > 4:
        raise ValueError(f"OG H1 too long for safe design: {title[:120]!r}")
    line_step = int(title_font.size * 1.20)
    text_top = 172 + max(0, (220 - len(title_lines) * line_step) // 2)
    for i, line in enumerate(title_lines):
        centered(line, text_top + i * line_step, title_font, ink)

    subtitle_font = _font("regular", 28)
    for font_size in range(28, 17, -2):
        candidate = _font("regular", font_size)
        if d.textbbox((0, 0), subtitle, font=candidate)[2] <= max_title_width:
            subtitle_font = candidate
            break
    centered(subtitle, 434, subtitle_font, ink)

    # Chips fit in the same central 630px square without relying on edge text.
    chip_font = _font("bold", 21)
    visible = []
    total = 0
    for label in chips:
        text_width = d.textbbox((0, 0), label, font=chip_font)[2]
        chip_width = text_width + 26
        if total + chip_width + (12 if visible else 0) > 550:
            break
        visible.append((label, chip_width))
        total += chip_width + (12 if len(visible) > 1 else 0)
    x = (width - total) // 2
    for label, chip_width in visible:
        d.rounded_rectangle((x, 516, x + chip_width, 557), radius=20, fill="#FFFFFF")
        d.text((x + 13, 522), label, font=chip_font, fill=accent)
        x += chip_width + 12

    # Central crop-safe elements occupy x=306..894, all within [285..915].
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG", optimize=False, compress_level=4)

def build(root: Path, force_specific: bool = False) -> dict:
    master_dir = root / "assets" / "images" / "og-master"
    page_dir = root / "assets" / "images" / "og-pages"

    # Exactly 29 master designs.
    for key, spec in MASTER.items():
        draw_thumb(master_dir / f"{key}.png", key, spec[0], spec[1], spec[2])

    manifest = {}
    counts = {"masters": len(MASTER), "indexable_unique": 0, "noindex_master": 0}

    for page in sorted(root.glob("*.html")):
        if page.name == "404.html":
            continue
        raw = page.read_text(encoding="utf-8", errors="ignore")
        key = page_key(page.name)
        specific = force_specific or is_indexable(raw)

        if specific:
            # Core/hub pages keep the approved 29-master copy. Only local/station
            # pages substitute the real page H1 (region/station + keyword).
            title = MASTER[key][0] if page.name in CORE_PAGE_KEYS else page_title(raw, key, True)
            out = page_dir / f"{page.stem}.png"
            subtitle, chips = MASTER[key][1], MASTER[key][2]
            draw_thumb(out, key, title, subtitle, chips)
            rel = "/" + str(out.relative_to(root)).replace("\\","/")
            counts["indexable_unique"] += 1
        else:
            rel = f"/assets/images/og-master/{key}.png"
            counts["noindex_master"] += 1

        manifest[page.name] = {
            "key": key,
            "indexable": specific,
            "image": rel,
            "absolute_image": BASE_URL + rel,
            "width": 1200,
            "height": 630,
            "safe_crop": "center-square",
        }

    (root / "assets" / "search-thumbnail-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if counts["masters"] != 29:
        raise RuntimeError(f"master count mismatch: {counts['masters']}")
    return counts

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="Built Stage 9 release directory")
    ap.add_argument(
        "--force-specific",
        action="store_true",
        help="Generate a page-specific landscape image for every HTML page (Preview QA only).",
    )
    args = ap.parse_args()
    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"missing root: {root}")
    counts = build(root, force_specific=args.force_specific)
    print("PASS_STAGE9_LANDSCAPE_CROP_SAFE_OG", json.dumps(counts, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
