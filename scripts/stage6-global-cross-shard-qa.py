#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import heapq
import html
import json
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, HashingVectorizer
from sklearn.preprocessing import normalize

INTENTS = [
    "elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv",
    "toeic","toeic-speaking","opic","ielts","duolingo","toefl",
]
TOKEN_PATTERN = r"(?u)[가-힣A-Za-z0-9]+"
TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")
COSINE_THRESHOLD = 0.82
JACCARD5_THRESHOLD = 0.24


def visible(raw: str) -> str:
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def shard_id(path: Path) -> int:
    name = path.parents[1].name
    m = re.fullmatch(r"shard-(\d{3})-of-026", name)
    if not m:
        raise RuntimeError(f"bad shard path: {path}")
    return int(m.group(1)) - 1


def push_top(heap: list, score: float, item: dict, limit: int = 50) -> None:
    entry = (score, json.dumps(item, ensure_ascii=False, sort_keys=True), item)
    if len(heap) < limit:
        heapq.heappush(heap, entry)
    elif entry[:2] > heap[0][:2]:
        heapq.heapreplace(heap, entry)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", default="stage5-work")
    ap.add_argument("--output", default="stage6-global")
    ap.add_argument("--expected-pages", type=int, default=66937)
    ap.add_argument("--block-size", type=int, default=96)
    ap.add_argument("--jaccard-screen", type=float, default=0.18)
    args = ap.parse_args()

    root = Path(args.work_root) / "stage5-full-generation"
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    all_html = list(root.glob("shard-*/pages/*.html"))
    if len(all_html) != args.expected_pages:
        raise RuntimeError(f"page count {len(all_html)} != {args.expected_pages}")

    global_cosine_max = 0.0
    global_jaccard_approx_max = 0.0
    global_jaccard_exact_max = 0.0
    cosine_failures = []
    jaccard_failures = []
    cosine_top = []
    jaccard_top = []
    intent_summaries = []
    total_cross_pairs = 0
    total_jaccard_exact_checks = 0

    for intent in INTENTS:
        paths = sorted(root.glob(f"shard-*/pages/*-{intent}.html"))
        if len(paths) != 5149:
            raise RuntimeError(f"{intent}: {len(paths)} pages != 5149")
        shards = np.array([shard_id(p) for p in paths], dtype=np.int16)
        names = [p.name for p in paths]

        def docs():
            for p in paths:
                yield visible(p.read_text(encoding="utf-8"))

        vectorizer = CountVectorizer(token_pattern=TOKEN_PATTERN, lowercase=True, dtype=np.float32)
        X = vectorizer.fit_transform(docs()).tocsr()
        normalize(X, norm="l2", copy=False)
        n = X.shape[0]
        same_shard_pairs = sum(int(np.sum(shards == s)) * (int(np.sum(shards == s)) - 1) // 2 for s in np.unique(shards))
        cross_pairs = n * (n - 1) // 2 - same_shard_pairs
        total_cross_pairs += cross_pairs

        intent_cos_max = 0.0
        intent_cos_fail = 0
        for start in range(0, n, args.block_size):
            end = min(n, start + args.block_size)
            sims = (X[start:end] @ X.T).toarray()
            for bi, i in enumerate(range(start, end)):
                row = sims[bi]
                row[: i + 1] = -1.0
                row[shards == shards[i]] = -1.0
                row_max = float(row.max(initial=-1.0))
                intent_cos_max = max(intent_cos_max, row_max)
                global_cosine_max = max(global_cosine_max, row_max)
                high = np.flatnonzero(row >= COSINE_THRESHOLD)
                intent_cos_fail += int(high.size)
                for j in high:
                    item = {"intent": intent, "a": names[i], "b": names[int(j)], "cosine": round(float(row[j]), 6)}
                    if len(cosine_failures) < 500:
                        cosine_failures.append(item)
                if row_max >= 0:
                    j = int(np.argmax(row))
                    push_top(cosine_top, row_max, {"intent": intent, "a": names[i], "b": names[j], "cosine": round(row_max, 6)})

        hv = HashingVectorizer(
            token_pattern=TOKEN_PATTERN,
            lowercase=True,
            analyzer="word",
            ngram_range=(5, 5),
            n_features=2**22,
            binary=True,
            alternate_sign=False,
            norm=None,
            dtype=np.float32,
        )
        B = hv.transform(docs()).tocsr()
        B.sum_duplicates()
        B.data[:] = 1.0
        sizes = np.diff(B.indptr).astype(np.float32)
        intent_j_approx_max = 0.0
        candidates: set[tuple[int, int]] = set()
        approx_heap = []
        for start in range(0, n, args.block_size):
            end = min(n, start + args.block_size)
            inter = (B[start:end] @ B.T).toarray()
            den = sizes[start:end, None] + sizes[None, :] - inter
            jac = np.divide(inter, den, out=np.zeros_like(inter), where=den > 0)
            for bi, i in enumerate(range(start, end)):
                row = jac[bi]
                row[: i + 1] = -1.0
                row[shards == shards[i]] = -1.0
                row_max = float(row.max(initial=-1.0))
                intent_j_approx_max = max(intent_j_approx_max, row_max)
                global_jaccard_approx_max = max(global_jaccard_approx_max, row_max)
                for j in np.flatnonzero(row >= args.jaccard_screen):
                    candidates.add((i, int(j)))
                if row_max >= 0:
                    j = int(np.argmax(row))
                    push_top(approx_heap, row_max, {"i": i, "j": j, "score": row_max}, limit=40)
        for _, _, item in approx_heap:
            candidates.add((int(item["i"]), int(item["j"])))

        @lru_cache(maxsize=256)
        def shingles(idx: int) -> frozenset[tuple[str, ...]]:
            ts = TOKEN_RE.findall(visible(paths[idx].read_text(encoding="utf-8")).lower())
            return frozenset(tuple(ts[k:k+5]) for k in range(max(0, len(ts) - 4)))

        intent_j_exact_max = 0.0
        intent_j_fail = 0
        for i, j in sorted(candidates):
            a, b = shingles(i), shingles(j)
            union = len(a | b)
            score = len(a & b) / union if union else 0.0
            total_jaccard_exact_checks += 1
            intent_j_exact_max = max(intent_j_exact_max, score)
            global_jaccard_exact_max = max(global_jaccard_exact_max, score)
            push_top(jaccard_top, score, {"intent": intent, "a": names[i], "b": names[j], "jaccard5": round(score, 6)})
            if score >= JACCARD5_THRESHOLD:
                intent_j_fail += 1
                if len(jaccard_failures) < 500:
                    jaccard_failures.append({"intent": intent, "a": names[i], "b": names[j], "jaccard5": round(score, 6)})

        intent_summaries.append({
            "intent": intent,
            "pages": n,
            "cross_shard_pairs": cross_pairs,
            "max_cosine": round(intent_cos_max, 6),
            "cosine_failures": intent_cos_fail,
            "max_hashed_jaccard5_screen": round(intent_j_approx_max, 6),
            "exact_jaccard5_checks": len(candidates),
            "max_exact_jaccard5_checked": round(intent_j_exact_max, 6),
            "jaccard5_failures": intent_j_fail,
        })

    status = "PASS_STAGE6_GLOBAL_CROSS_SHARD_QA_NOT_PRODUCTION" if not cosine_failures and not jaccard_failures and global_jaccard_approx_max < JACCARD5_THRESHOLD else "FAIL_STAGE6_GLOBAL_CROSS_SHARD_QA_NOT_PRODUCTION"
    result = {
        "version": "1.0",
        "status": status,
        "stage": "STAGE6_GLOBAL_CROSS_SHARD_QA",
        "page_count": len(all_html),
        "locality_count": 5149,
        "intent_count": 13,
        "scope": {
            "cosine": "exact same-intent all cross-shard pairs",
            "jaccard5": "all-pair 5-shingle hashed screen (2^22 buckets) plus exact verification of top/screen candidates",
            "cross_shard_cosine_pairs": total_cross_pairs,
            "exact_jaccard5_candidate_checks": total_jaccard_exact_checks,
        },
        "thresholds": {"cosine_lt": COSINE_THRESHOLD, "jaccard5_lt": JACCARD5_THRESHOLD, "jaccard5_screen": args.jaccard_screen},
        "max_cosine": round(global_cosine_max, 6),
        "max_hashed_jaccard5_screen": round(global_jaccard_approx_max, 6),
        "max_exact_jaccard5_checked": round(global_jaccard_exact_max, 6),
        "cosine_failure_count": len(cosine_failures),
        "jaccard5_failure_count": len(jaccard_failures),
        "cosine_failures": cosine_failures,
        "jaccard5_failures": jaccard_failures,
        "top_cosine_pairs": [x[2] for x in sorted(cosine_top, reverse=True)],
        "top_jaccard5_pairs": [x[2] for x in sorted(jaccard_top, reverse=True)],
        "intents": intent_summaries,
        "safety": {"production_deploy": False, "main_merge": False, "sitemap_live": False},
    }
    p = out / "STAGE6_GLOBAL_CROSS_SHARD_QA_V1.json"
    p.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "pages": len(all_html),
        "cross_shard_pairs": total_cross_pairs,
        "max_cosine": result["max_cosine"],
        "max_hashed_jaccard5_screen": result["max_hashed_jaccard5_screen"],
        "max_exact_jaccard5_checked": result["max_exact_jaccard5_checked"],
        "cosine_failures": len(cosine_failures),
        "jaccard5_failures": len(jaccard_failures),
        "exact_jaccard_checks": total_jaccard_exact_checks,
    }, ensure_ascii=False))
    if status.startswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
