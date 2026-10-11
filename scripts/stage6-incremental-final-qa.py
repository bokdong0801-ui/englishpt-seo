#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, HashingVectorizer
from sklearn.preprocessing import normalize

TOKEN_PATTERN = r"(?u)[가-힣A-Za-z0-9]+"
TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")
COSINE_THRESHOLD = 0.82
JACCARD5_THRESHOLD = 0.24

CHANGED = {
    "gyeongbuk-gimcheon-daesindong-opic.html": "opic",
    "busan-yeonje-yeonsanje1dong-toefl.html": "toefl",
}
EXPECTED_OLD_FAILURES = {
    ("opic", "gyeongbuk-gimcheon-daesindong-opic.html", "seoul-jongno-haengchondong-opic.html"),
    ("toefl", "busan-yeonje-yeonsanje1dong-toefl.html", "daegu-suseong-daeheungdong-toefl.html"),
}
AFFECTED_SHARDS = ["shard-002-of-026", "shard-009-of-026"]


def visible(raw: str) -> str:
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shard_id(path: Path) -> int:
    m = re.fullmatch(r"shard-(\d{3})-of-026", path.parents[1].name)
    if not m:
        raise RuntimeError(f"bad shard path {path}")
    return int(m.group(1)) - 1


def exact_shingles(text: str) -> frozenset[tuple[str, ...]]:
    ts = TOKEN_RE.findall(text.lower())
    return frozenset(tuple(ts[i:i+5]) for i in range(max(0, len(ts)-4)))


def compare_affected_shards(base_root: Path, final_root: Path) -> dict:
    changed = []
    compared = 0
    for shard in AFFECTED_SHARDS:
        bp = base_root / shard / "pages"
        fp = final_root / shard / "pages"
        bfiles = {p.name: p for p in bp.glob("*.html")}
        ffiles = {p.name: p for p in fp.glob("*.html")}
        if set(bfiles) != set(ffiles):
            raise RuntimeError(f"filename set changed in {shard}")
        for name in sorted(bfiles):
            compared += 1
            if sha(bfiles[name]) != sha(ffiles[name]):
                changed.append(name)
    if set(changed) != set(CHANGED):
        raise RuntimeError(f"unexpected changed HTML set: {changed}")
    return {"compared_html": compared, "changed_html": sorted(changed)}


def verify_previous_qa(path: Path) -> dict:
    q = json.loads(path.read_text(encoding="utf-8"))
    if q.get("page_count") != 66937:
        raise RuntimeError("previous QA page count mismatch")
    if q.get("cosine_failure_count") != 2 or q.get("jaccard5_failure_count") != 0:
        raise RuntimeError("previous QA is not the expected 2-failure baseline")
    got = set()
    for x in q.get("cosine_failures", []):
        a, b = sorted([x["a"], x["b"]])
        got.add((x["intent"], a, b))
    expected = set()
    for intent, a, b in EXPECTED_OLD_FAILURES:
        aa, bb = sorted([a, b])
        expected.add((intent, aa, bb))
    if got != expected:
        raise RuntimeError(f"previous failure set mismatch: {got}")
    return {
        "status": q.get("status"),
        "cosine_failures": q.get("cosine_failure_count"),
        "jaccard5_failures": q.get("jaccard5_failure_count"),
        "max_cosine": q.get("max_cosine"),
        "max_hashed_jaccard5_screen": q.get("max_hashed_jaccard5_screen"),
    }


def check_changed_page(final_root: Path, filename: str, intent: str) -> dict:
    paths = sorted(final_root.glob(f"shard-*/pages/*-{intent}.html"))
    if len(paths) != 5149:
        raise RuntimeError(f"{intent}: expected 5149 pages, got {len(paths)}")
    names = [p.name for p in paths]
    try:
        idx = names.index(filename)
    except ValueError:
        raise RuntimeError(f"missing changed page {filename}")
    shards = np.array([shard_id(p) for p in paths], dtype=np.int16)
    docs = [visible(p.read_text(encoding="utf-8")) for p in paths]

    cv = CountVectorizer(token_pattern=TOKEN_PATTERN, lowercase=True, dtype=np.float32)
    X = cv.fit_transform(docs).tocsr()
    normalize(X, norm="l2", copy=False)
    sims = (X[idx] @ X.T).toarray().ravel()
    mask = np.ones(len(paths), dtype=bool)
    mask[idx] = False
    mask[shards == shards[idx]] = False
    cross_scores = sims[mask]
    cos_max = float(cross_scores.max(initial=0.0))
    cos_fail = int(np.sum(cross_scores >= COSINE_THRESHOLD))

    hv = HashingVectorizer(
        token_pattern=TOKEN_PATTERN,
        lowercase=True,
        analyzer="word",
        ngram_range=(5,5),
        n_features=2**22,
        binary=True,
        alternate_sign=False,
        norm=None,
        dtype=np.float32,
    )
    B = hv.transform(docs).tocsr()
    B.sum_duplicates()
    B.data[:] = 1.0
    sizes = np.diff(B.indptr).astype(np.float32)
    inter = (B[idx] @ B.T).toarray().ravel()
    den = sizes[idx] + sizes - inter
    jac = np.divide(inter, den, out=np.zeros_like(inter), where=den > 0)
    hj_max = float(jac[mask].max(initial=0.0))
    hj_fail = int(np.sum(jac[mask] >= JACCARD5_THRESHOLD))

    target = exact_shingles(docs[idx])
    exact_max = 0.0
    exact_fail = 0
    exact_checks = 0
    for j, doc in enumerate(docs):
        if not mask[j]:
            continue
        other = exact_shingles(doc)
        union = len(target | other)
        score = len(target & other) / union if union else 0.0
        exact_checks += 1
        exact_max = max(exact_max, score)
        if score >= JACCARD5_THRESHOLD:
            exact_fail += 1

    return {
        "file": filename,
        "intent": intent,
        "cross_shard_pages_checked": int(np.sum(mask)),
        "max_cosine": round(cos_max, 6),
        "cosine_failures": cos_fail,
        "max_hashed_jaccard5": round(hj_max, 6),
        "hashed_jaccard5_failures": hj_fail,
        "max_exact_jaccard5": round(exact_max, 6),
        "exact_jaccard5_failures": exact_fail,
        "exact_jaccard_checks": exact_checks,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-root", required=True)
    ap.add_argument("--final-root", required=True)
    ap.add_argument("--previous-qa", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    base_root = Path(args.base_root)
    final_root = Path(args.final_root)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    final_count = len(list(final_root.glob("shard-*/pages/*.html")))
    if final_count != 66937:
        raise RuntimeError(f"final page count {final_count} != 66937")

    delta = compare_affected_shards(base_root, final_root)
    prev = verify_previous_qa(Path(args.previous_qa))
    checks = [check_changed_page(final_root, name, intent) for name, intent in CHANGED.items()]

    fail = any(
        x["cosine_failures"] or x["hashed_jaccard5_failures"] or x["exact_jaccard5_failures"]
        for x in checks
    )
    status = "PASS_STAGE6_INCREMENTAL_GLOBAL_PROOF_NOT_PRODUCTION" if not fail else "FAIL_STAGE6_INCREMENTAL_GLOBAL_PROOF_NOT_PRODUCTION"
    result = {
        "version": "1.0",
        "status": status,
        "stage": "STAGE6_INCREMENTAL_GLOBAL_PROOF",
        "page_count": final_count,
        "locality_count": 5149,
        "intent_count": 13,
        "proof": {
            "baseline": "Previous exact global Stage 6 checked all 165,685,000 cross-shard same-intent pairs and had exactly two cosine failures, zero Jaccard failures.",
            "delta": "SHA comparison proves only the two expected HTML pages changed in the refreshed shards.",
            "recheck": "Each changed page is rechecked against every cross-shard page of the same intent for exact cosine, hashed 5-shingle Jaccard, and exact 5-shingle Jaccard.",
            "conclusion": "All unchanged pairs retain the prior below-threshold result; every pair involving changed pages is rechecked here.",
        },
        "thresholds": {"cosine_lt": COSINE_THRESHOLD, "jaccard5_lt": JACCARD5_THRESHOLD},
        "previous_global_qa": prev,
        "delta_verification": delta,
        "changed_page_checks": checks,
        "changed_pair_cosine_failure_count": sum(x["cosine_failures"] for x in checks),
        "changed_pair_hashed_jaccard5_failure_count": sum(x["hashed_jaccard5_failures"] for x in checks),
        "changed_pair_exact_jaccard5_failure_count": sum(x["exact_jaccard5_failures"] for x in checks),
        "safety": {"production_deploy": False, "main_merge": False, "sitemap_live": False},
    }
    p = out / "STAGE6_INCREMENTAL_GLOBAL_PROOF_V1.json"
    p.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "pages": final_count,
        "delta": delta,
        "checks": checks,
        "production_deploy": False,
        "main_merge": False,
    }, ensure_ascii=False))
    if fail:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
