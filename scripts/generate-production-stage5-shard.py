#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage 5 full generation shard.

Frozen contract:
- Stage 3 renderer
- Stage 4 variation/particle/row-signature extensions
- Stage 1 audited 5,149 locality rows
- 13 intents per locality

Safety:
- noindex,nofollow
- no live lead submission
- no main merge
- no production deploy
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import importlib.util
import json
import math
import re
import shutil
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "stage5_localities_5149_v1.jsonl"
OUTPUT_ROOT = ROOT / "stage5-full-generation"
EXPECTED_LOCALITIES = 5149
INTENTS_PER_LOCALITY = 13
DEFAULT_SHARD_SIZE = 200
DEFAULT_SHARD_COUNT = math.ceil(EXPECTED_LOCALITIES / DEFAULT_SHARD_SIZE)
SERVICE_ORDER = ["elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv"]
EXAM_ORDER = ["toeic","toeic-speaking","opic","ielts","duolingo","toefl"]

MALFORMED = [
    "영어회화을","영어과외을","비즈니스영어을","문항를","질의을","응시이","근거이","근거은",
    "제한 제한","페이지은","범위을","행동를","기능를","조건를","영역를","지점를","반응를",
    "시간를","항목를","'을 다음 확인 기준","'를 다음 확인 기준","합니다에서 무엇부터","습니다에서 무엇부터"
]
GENERIC = ["최고의 강사진","성적 향상을 책임","지금 바로 상담 신청"]
EXPECTED_KICKERS = [
    "자기상황 식별","선택 기준","우선순위","수업 흐름","중간 확인","판단 기준","피드백 예시",
    "자주 묻는 질문","더 깊게 보기","관련 과정","상담 전 체크"
]



STAGE5_LENSES = [
    {
        "terms": ["혼자 시작", "도움 감소", "자기 수정", "독립 완결", "재현 범위", "시작 단서"],
        "note": "혼자 시작하는 구간과 도움을 줄여도 이어지는 범위를 따로 봅니다.",
    },
    {
        "terms": ["마감일", "남은 횟수", "직전 점검", "우선 순서", "완충 시간", "후속 보완"],
        "note": "남은 일정과 실제 연습 횟수를 맞춰 직전 점검과 후속 보완을 분리합니다.",
    },
    {
        "terms": ["근거 누락", "질문 오해", "지식 공백", "처리 순서", "반복 실수", "수정 경로"],
        "note": "틀린 결과보다 오류가 시작된 원인과 수정 경로를 먼저 분리합니다.",
    },
    {
        "terms": ["첫 반응", "발화 완결", "질문 대응", "전달 의도", "즉시 사용", "장면 전환"],
        "note": "실제 사용 장면에서 첫 반응과 끝까지 전달하는 수행을 중심으로 봅니다.",
    },
    {
        "terms": ["새 자료", "질문 변형", "난도 변화", "조건 변경", "전이 확인", "재사용 범위"],
        "note": "익숙한 예시를 벗어나 자료와 질문이 달라져도 기준이 남는지 확인합니다.",
    },
    {
        "terms": ["기억 재생", "간격 복습", "재노출", "누적 유지", "망각 지점", "회수 속도"],
        "note": "바로 맞힌 결과보다 시간을 두고 다시 꺼냈을 때 유지되는 범위를 봅니다.",
    },
    {
        "terms": ["제한 시간", "처리 속도", "순서 배분", "종료 기준", "병목 구간", "시간 압박"],
        "note": "제한 시간 안에서 어디에 시간이 몰리는지와 끝까지 처리되는지를 나눠 봅니다.",
    },
    {
        "terms": ["대안 과정", "수업 방식", "비용 구성", "피드백 범위", "일정 유연성", "과정 적합"],
        "note": "한 가지 방식만 보지 않고 수업 운영과 피드백 범위를 같은 기준으로 비교합니다.",
    },
    {
        "terms": ["첨삭 반영", "재답변", "수정 이유", "후속 점검", "피드백 회수", "다음 행동"],
        "note": "피드백을 받은 뒤 실제 답변이나 수행이 어떻게 달라지는지를 다시 확인합니다.",
    },
    {
        "terms": ["우선 기능", "제외 범위", "단기 목표", "장기 보완", "목표 충돌", "범위 축소"],
        "note": "지금 필요한 기능과 뒤로 미뤄도 되는 범위를 나눠 목표가 섞이지 않게 합니다.",
    },
    {
        "terms": ["선택 근거", "핵심 정보", "이유 설명", "근거 연결", "판단 기준", "설명 완결"],
        "note": "답만 맞히는 것보다 어떤 근거로 판단했는지 설명할 수 있는지를 확인합니다.",
    },
    {
        "terms": ["첫 문장", "핵심 표현", "응답 구조", "문장 연결", "출력 지속", "마무리 표현"],
        "note": "알고 있는 내용을 실제 문장과 답변으로 끝까지 구성하는 과정을 봅니다.",
    },
    {
        "terms": ["최소 분량", "반복 단위", "시작 시간", "복습 시점", "주간 배치", "공백 복구"],
        "note": "바쁜 주에도 반복 가능한 최소 단위와 다시 시작할 수 있는 지점을 정합니다.",
    },
]

STAGE5_PROCESS_MODES = [
    "현재 상태를 관찰하고 달라진 지점을 짧게 기록합니다.",
    "전후 조건을 맞춰 대조한 뒤 새 자료에서 다시 검사합니다.",
    "설명보다 직접 수행을 먼저 두고 결과를 다음 행동으로 연결합니다.",
    "가까운 목표에 필요한 항목을 앞에 두고 나머지 범위를 조정합니다.",
]

STAGE5_METHOD_NOTES = [
    "현재 상태를 먼저 적고 다음 확인 항목을 남깁니다.",
    "가까운 일정에서 거꾸로 순서를 잡습니다.",
    "오류 원인과 수정 과정을 함께 봅니다.",
    "설명을 실제 수행으로 바로 바꿉니다.",
    "조건을 바꿔 재사용 범위를 살핍니다.",
    "시간을 두고 다시 되는지 확인합니다.",
    "처리 시간과 순서를 함께 기록합니다.",
    "되는 조건과 흔들리는 조건을 대조합니다.",
    "다음에 다시 볼 행동을 짧게 남깁니다.",
    "이번 목표에 필요한 범위만 유지합니다.",
]

STAGE5_TOPICS = [
    "최근 혼자 처리한 범위", "가장 자주 멈춘 행동", "다음 일정에 필요한 수행", "도움이 줄어도 남는 기능",
    "반복해서 흔들리는 조건", "이미 안정된 영역", "실전에서 필요한 첫 반응", "시간 압박에서 달라지는 부분",
    "질문이 바뀔 때 흔들리는 지점", "설명 없이 다시 가능한 범위", "이번에 제외해도 되는 목표", "다른 과정이 더 직접적인 조건",
    "피드백 뒤 다시 볼 행동", "자료가 달라도 유지되는 기준", "복습 가능한 실제 시간", "가장 가까운 결과에 영향을 주는 항목",
    "한 번 성공한 뒤 재현되는 범위", "힌트가 줄었을 때 수정되는 부분", "실제 제출이나 사용 조건", "다음 수업에서 확인할 기록",
    "새 자료에서 다시 막히는 부분", "수업 밖에서도 이어지는 행동", "현재 목표와 맞지 않는 범위", "다음 단계로 넘길 수 있는 기능",
]

STAGE5_VERIFY = [
    "새 조건에서 다시 점검합니다", "비슷한 난도의 자료로 재확인합니다", "질문을 바꿔 다시 봅니다", "도움을 줄인 뒤 재검사합니다",
    "실전과 가까운 조건에서 살핍니다", "시간 조건을 바꿔 비교합니다", "다른 예시에서 재현합니다", "독립 수행으로 이어지는지 봅니다",
    "다음 일정과 비슷한 상황에서 확인합니다", "처음과 다른 자료로 검증합니다", "후속 기록에서 다시 비교합니다", "조건을 하나 바꿔 점검합니다",
    "수업 밖의 수행으로 확인합니다", "피드백 없이 다시 시도합니다", "처리 순서를 바꿔 살핍니다", "새 질문에서 같은 기준을 적용합니다",
    "다음 복습 시점에 회수합니다", "필요한 힌트의 양을 비교합니다", "실제 사용 순서로 재검사합니다", "다른 선택과 나란히 검토합니다",
]


def _stage5_pick(row: dict, slot: int, values: list[str], salt: str) -> str:
    seed = f"{row['content_seed']}|{row.get('_intent_salt','')}|{slot}|{salt}"
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return values[int(h[:12], 16) % len(values)]


def _stage5_profile(row: dict) -> tuple[int, int, int, int]:
    rank = int(row.get("_stage5_global_rank", 0))
    base = rank % 100
    lane = rank // 100
    theme_idx = base % 10
    method_idx = ((base // 10) + 3 * (base % 10)) % 10
    return lane % len(STAGE5_LENSES), (lane // len(STAGE5_LENSES)) % len(STAGE5_PROCESS_MODES), theme_idx, method_idx


def install_stage5_scaled_guide(g, s4) -> None:
    """Use Stage 4's audited row-specific guide pool to break the 100-row cycle.

    Stage 4's visible guide repeats one profile sentence many times per page.
    At Stage 5 scale that creates rank+100 near-duplicates. Preserve the
    original lead, focus, method and signature sentences, and replace only the
    repeated theme sentence with one audited row/slot-specific pool sentence.
    """
    base_guide = g.guide
    pool_fn = g.guide_dimension_pool

    def guide(row: dict, slot: int) -> str:
        base_text = base_guide(row, slot)
        parts = re.split(r"(?<=\.)\s+", base_text)
        if len(parts) < 5:
            return base_text

        pool = pool_fn(row)
        if not pool:
            return base_text

        seed = (
            f"{row['content_seed']}|{row.get('_intent_salt','')}|"
            f"{row.get('_stage5_global_rank',0)}|{slot}|stage5-row-pool"
        )
        idx = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12], 16) % len(pool)
        parts[3] = pool[idx]
        return " ".join(parts)

    g.guide = guide


def stage5_row_signature_block(s4, row: dict, intent: str) -> str:
    """Keep the already human-reviewed Stage 4 row-signature contract unchanged."""
    return s4.row_signature_block(row, intent)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_rows() -> list[dict]:
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != EXPECTED_LOCALITIES:
        raise RuntimeError(f"Stage5 requires {EXPECTED_LOCALITIES} rows, got {len(rows)}")
    if len({r["region_slug"] for r in rows}) != EXPECTED_LOCALITIES:
        raise RuntimeError("region_slug uniqueness failure")
    if len({r["locality_key"] for r in rows}) != EXPECTED_LOCALITIES:
        raise RuntimeError("locality_key uniqueness failure")
    if len({r["variation_signature"] for r in rows}) != EXPECTED_LOCALITIES:
        raise RuntimeError("variation_signature uniqueness failure")
    if any(r.get("landing_eligibility") != "ELIGIBLE_AFTER_SLUG_QA" for r in rows):
        raise RuntimeError("ineligible row present")
    return sorted(rows, key=lambda r: r["region_slug"])


def reserved_urls() -> set[str]:
    out: set[str] = set()
    p = ROOT / "sitemap_95_urls.txt"
    if not p.exists():
        raise RuntimeError("sitemap_95_urls.txt missing")
    for line in p.read_text(encoding="utf-8").splitlines():
        x = line.strip()
        if not x or x.startswith("#"):
            continue
        out.add(x)
        out.add(x.rsplit("/", 1)[-1])
    return out


def push_top(heap: list, item: dict, serial: int, limit: int = 30) -> None:
    key = (item["jaccard5"], item["cosine"], serial, item)
    if len(heap) < limit:
        heapq.heappush(heap, key)
    elif key[:3] > heap[0][:3]:
        heapq.heapreplace(heap, key)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-index", type=int, required=True, help="zero-based shard index")
    ap.add_argument("--shard-count", type=int, default=DEFAULT_SHARD_COUNT)
    ap.add_argument("--shard-size", type=int, default=DEFAULT_SHARD_SIZE)
    args = ap.parse_args()

    if args.shard_size <= 0:
        raise RuntimeError("shard-size must be positive")
    required_count = math.ceil(EXPECTED_LOCALITIES / args.shard_size)
    if args.shard_count != required_count:
        raise RuntimeError(f"shard-count mismatch: {args.shard_count} != {required_count}")
    if not 0 <= args.shard_index < args.shard_count:
        raise RuntimeError(f"shard-index out of range: {args.shard_index}")

    all_rows = load_rows()
    name_counts = Counter(r["dong_name"] for r in all_rows)
    for rank, row in enumerate(all_rows):
        row["_stage4_rank"] = rank
        row["_stage5_global_rank"] = rank
        row["_same_name_count"] = name_counts[row["dong_name"]]

    start = args.shard_index * args.shard_size
    end = min(start + args.shard_size, len(all_rows))
    rows = all_rows[start:end]
    if not rows:
        raise RuntimeError("empty shard")

    shard_name = f"shard-{args.shard_index + 1:03d}-of-{args.shard_count:03d}"
    out = OUTPUT_ROOT / shard_name
    pages = out / "pages"
    if out.exists():
        shutil.rmtree(out)
    pages.mkdir(parents=True, exist_ok=True)

    s4 = load_module("stage4_engine", ROOT / "scripts/generate-production-stage4-100x13.py")
    g = load_module("stage3_renderer", ROOT / "scripts/generate-production-stage3-10x13.py")
    s4.patch_engine(g)
    s4.install_stage4_guide_pool(g)
    install_stage5_scaled_guide(g, s4)
    s4.install_stage4_unique_longform(g)
    svc = load_module("service_gold_stage5", ROOT / "scripts/generate-v45-full-depth-pilot.py")
    ex = load_module("exam_gold_stage5", ROOT / "scripts/generate-v45-exam-pilot.py")

    g.LOCALITY_LONGFORM = {}
    for row in rows:
        d = g.dims(row["variation_signature"])
        g.LOCALITY_LONGFORM[row["region_slug"]] = g.make_stage4_unique_longform(row, d)

    shutil.copy2(ROOT / "stage3-production-dryrun-10x13/pilot.css", pages / "pilot.css")
    shutil.copy2(ROOT / "stage3-production-dryrun-10x13/pilot.js", pages / "pilot.js")

    intents = SERVICE_ORDER + [ex.EXAMS[k]["intent"] for k in EXAM_ORDER]
    expected_by_locality = {
        row["region_slug"]: {f"{row['region_slug']}-{intent}.html" for intent in intents}
        for row in rows
    }
    reserved = reserved_urls()

    files: list[dict] = []
    checks: list[dict] = []
    failures: list[dict] = []
    groups: dict[str, list[tuple[str, str, object]]] = defaultdict(list)
    filenames: set[str] = set()
    canonicals: set[str] = set()
    html_set_digest = hashlib.sha256()
    reserved_conflicts = 0

    def process_page(row: dict, intent: str, family: str, h1: str, blueprint: str, raw: str, exam: str | None = None) -> None:
        nonlocal reserved_conflicts
        name = f"{row['region_slug']}-{intent}.html"
        canonical = f"https://englishpt.kr/{name}"
        txt = s4.visible(raw)
        page_bytes = raw.encode("utf-8")
        f: list[str] = []

        if len(re.findall(r"<h1\b", raw)) != 1 or f"<h1>{g.esc(h1)}</h1>" not in raw:
            f.append("h1")
        if f'rel="canonical" href="{canonical}"' not in raw:
            f.append("canonical")
        if 'name="robots" content="noindex,nofollow"' not in raw:
            f.append("noindex")
        if 'data-production-deploy="false"' not in raw:
            f.append("production_flag")
        required_blocks = ["decision-strip","decision-guide","mid-cta","variation-story","locality-longform","row-signature"]
        if raw.count("◆ ") < 5 or any(x not in raw for x in required_blocks):
            f.append("conversion_blocks")

        kickers = re.findall(r'<p class="kicker">(.*?)</p>', raw)
        try:
            positions = [kickers.index(x) for x in EXPECTED_KICKERS]
        except ValueError:
            positions = []
        if not positions or positions != sorted(positions):
            f.append("conversion_flow_order")

        try:
            block = re.search(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)
            if not block:
                raise ValueError("missing JSON-LD")
            json.loads(block.group(1))
        except Exception:
            f.append("schema")

        bad_malformed = [x for x in MALFORMED if x in txt]
        if bad_malformed:
            f.append("malformed_korean:" + ",".join(bad_malformed))
        bad_particles = s4.quoted_particle_errors(txt)
        if bad_particles:
            f.append("quoted_particle:" + ",".join(bad_particles[:8]))
        if any(x in txt for x in GENERIC):
            f.append("generic_marketing")

        internal_profile = re.search(
            r"(독립수행|일정역산|오류추적|실사용|조건전환|복습회수|시간처리|선택비교|피드백반영|목표경계)"
            r"(점검형|배치형|교정형|적용형|확장형|유지형|측정형|대조형|기록형|집중형)",
            txt,
        )
        if internal_profile or any(x in txt for x in ["후속 이름:","운영 프레임:","기록명:","기준 메모는"]):
            f.append("internal_variation_label")
        if any(x in txt for x in ["place_id","official_code","content_seed","variation_pack_id"]):
            f.append("db_internal")
        if "-tos.html" in raw.lower():
            f.append("standalone_tos")

        linked = set(re.findall(r'href="([^"]+\.html)"', raw))
        missing = expected_by_locality[row["region_slug"]] - {name} - linked
        if missing:
            f.append("cluster_links")

        if name in reserved or canonical in reserved:
            f.append("reserved_95_conflict")
            reserved_conflicts += 1

        if not 9000 <= len(txt) <= 20500:
            f.append(f"visible_chars:{len(txt)}")

        page_path = pages / name
        page_path.write_text(raw, encoding="utf-8")
        page_sha = hashlib.sha256(page_bytes).hexdigest()
        html_set_digest.update(name.encode("utf-8") + b"\0" + page_sha.encode("ascii") + b"\n")

        check = {
            "file": name,
            "family": family,
            "intent": intent,
            "visible_chars": len(txt),
            "bytes": len(page_bytes),
            "sha256": page_sha,
            "status": "PASS" if not f else "FAIL",
            "failures": f,
        }
        checks.append(check)
        if f:
            failures.append({"file": name, "failures": f})

        meta = {
            "path": f"{shard_name}/pages/{name}",
            "file": name,
            "family": family,
            "intent": intent,
            "h1": h1,
            "canonical": canonical,
            "locality": row["region_slug"],
            "locality_key": row["locality_key"],
            "dong_name": row["dong_name"],
            "full_name_ko": row["full_name_ko"],
            "sido": row["sido"],
            "blueprint": blueprint,
            "variation_signature": row["variation_signature"],
            "visible_chars": len(txt),
            "bytes": len(page_bytes),
            "sha256": page_sha,
        }
        if exam:
            meta["exam"] = exam
        files.append(meta)
        filenames.add(name)
        canonicals.add(canonical)
        groups[intent].append((row["region_slug"], name, s4.prep_similarity(txt)))

    for row in rows:
        d = g.dims(row["variation_signature"])
        for intent in SERVICE_ORDER:
            p = svc.PROFILES[intent]
            raw = g.render_page(row, d, intent, "service", p, svc, ex)
            raw = raw.replace(
                '<section class="section related">',
                stage5_row_signature_block(s4, row, intent) + '<section class="section related">',
                1,
            )
            raw = raw.replace("PRODUCTION DRY-RUN · noindex", "FULL GENERATION · noindex")
            raw = raw.replace("Stage 3 dry-run · production 미배포", "Stage 5 full generation · production 미배포")
            raw = s4.fix_quoted_particles(raw)
            process_page(row, intent, "service", f"{row['dong_name']} {p['service_h1']}", p["blueprint"], raw)

        for key in EXAM_ORDER:
            e = ex.EXAMS[key]
            intent = e["intent"]
            raw = g.render_page(row, d, intent, "exam", e, svc, ex)
            raw = raw.replace(
                '<section class="section related">',
                stage5_row_signature_block(s4, row, intent) + '<section class="section related">',
                1,
            )
            raw = raw.replace("PRODUCTION DRY-RUN · noindex", "FULL GENERATION · noindex")
            raw = raw.replace("Stage 3 dry-run · production 미배포", "Stage 5 full generation · production 미배포")
            raw = s4.fix_quoted_particles(raw)
            process_page(row, intent, "exam", f"{row['dong_name']} {e['service']}", e["blueprint"], raw, exam=key)

    expected_pages = len(rows) * INTENTS_PER_LOCALITY
    if len(files) != expected_pages:
        failures.append({"global": ["page_count", len(files), expected_pages]})
    if len(filenames) != expected_pages:
        failures.append({"global": ["filename_unique", len(filenames), expected_pages]})
    if len(canonicals) != expected_pages:
        failures.append({"global": ["canonical_unique", len(canonicals), expected_pages]})

    top_heap: list = []
    max_cosine = 0.0
    max_jaccard = 0.0
    pair_count = 0
    duplicate_fail_count = 0
    duplicate_failure_examples: list[dict] = []
    serial = 0

    for intent, docs in groups.items():
        for (loc_a, file_a, prep_a), (loc_b, file_b, prep_b) in combinations(docs, 2):
            co = s4.cosine_pre(prep_a, prep_b)
            ja = s4.jacc_pre(prep_a, prep_b)
            pair_count += 1
            max_cosine = max(max_cosine, co)
            max_jaccard = max(max_jaccard, ja)
            item = {
                "intent": intent,
                "a": loc_a,
                "b": loc_b,
                "file_a": file_a,
                "file_b": file_b,
                "cosine": round(co, 4),
                "jaccard5": round(ja, 4),
            }
            serial += 1
            push_top(top_heap, item, serial)
            if co >= 0.82 or ja >= 0.24:
                duplicate_fail_count += 1
                if len(duplicate_failure_examples) < 100:
                    duplicate_failure_examples.append(item)

    if duplicate_fail_count:
        failures.append({
            "global": ["duplicate_gate", duplicate_fail_count],
            "examples": duplicate_failure_examples,
        })

    top_pairs = [x[3] for x in sorted(top_heap, reverse=True)]
    shortest = min(files, key=lambda x: x["visible_chars"])
    longest = max(files, key=lambda x: x["visible_chars"])
    total_html_bytes = sum(x["bytes"] for x in files)

    qa = {
        "version": "1.0",
        "status": "PASS" if not failures else "FAIL",
        "stage": "STAGE5_FULL_GENERATION_SHARD",
        "shard": {
            "index_zero_based": args.shard_index,
            "name": shard_name,
            "count": args.shard_count,
            "size_target_localities": args.shard_size,
            "global_row_start_zero_based": start,
            "global_row_end_exclusive": end,
        },
        "page_count": len(files),
        "locality_count": len(rows),
        "intent_count": INTENTS_PER_LOCALITY,
        "file_integrity": {
            "filenames_unique": len(filenames),
            "canonicals_unique": len(canonicals),
            "reserved_95_conflicts": reserved_conflicts,
            "html_set_sha256": html_set_digest.hexdigest(),
        },
        "visible_chars": {
            "min": shortest["visible_chars"],
            "max": longest["visible_chars"],
            "avg": round(sum(x["visible_chars"] for x in files) / len(files), 1),
        },
        "package_sizing": {
            "html_bytes": total_html_bytes,
            "html_mib": round(total_html_bytes / 1024 / 1024, 2),
            "avg_html_bytes": round(total_html_bytes / len(files), 1),
        },
        "duplicate_gate": {
            "status": "PASS" if duplicate_fail_count == 0 and max_cosine < 0.82 and max_jaccard < 0.24 else "FAIL",
            "scope": "within-shard exact same-intent all-pairs",
            "pairs": pair_count,
            "max_cosine": round(max_cosine, 4),
            "max_5_shingle_jaccard": round(max_jaccard, 4),
            "thresholds": {"cosine_lt": 0.82, "jaccard5_lt": 0.24},
            "failure_count": duplicate_fail_count,
            "top_pairs": top_pairs,
        },
        "shortest_page": shortest,
        "longest_page": longest,
        "static_failure_count": sum(1 for x in checks if x["status"] == "FAIL"),
        "failures": failures,
        "safety": {
            "robots": "noindex,nofollow",
            "live_lead_submission": False,
            "sitemap_live": False,
            "main_merge": False,
            "production_deploy": False,
        },
    }
    (out / "STAGE5_SHARD_QA_V1.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "version": "1.0",
        "status": "STAGE5_SHARD_PASS_NOT_PRODUCTION" if not failures else "STAGE5_SHARD_FAIL_NOT_PRODUCTION",
        "stage": "STAGE5_FULL_GENERATION_SHARD",
        "shard": qa["shard"],
        "source_manifest": "stage5_localities_5149_v1.jsonl",
        "renderer": "stage3-frozen-page-contract-plus-stage4-full-variation",
        "page_count": len(files),
        "locality_count": len(rows),
        "intent_count": INTENTS_PER_LOCALITY,
        "localities": [
            {
                "locality_key": r["locality_key"],
                "region_slug": r["region_slug"],
                "dong_name": r["dong_name"],
                "full_name_ko": r["full_name_ko"],
                "sido": r["sido"],
                "global_rank": r["_stage5_global_rank"],
                "variation_signature": r["variation_signature"],
            }
            for r in rows
        ],
        "files": files,
        "safety": qa["safety"],
    }
    (out / "STAGE5_SHARD_MANIFEST_V1.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {
        "status": qa["status"],
        "shard": shard_name,
        "localities": len(rows),
        "pages": len(files),
        "html_mib": qa["package_sizing"]["html_mib"],
        "pairs": pair_count,
        "max_cosine": qa["duplicate_gate"]["max_cosine"],
        "max_jaccard5": qa["duplicate_gate"]["max_5_shingle_jaccard"],
        "static_failures": qa["static_failure_count"],
        "duplicate_failures": duplicate_fail_count,
    }
    print(json.dumps(summary, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
