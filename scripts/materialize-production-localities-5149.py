#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstruct and validate the frozen Stage 1 5,149-row locality manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PART_DIR = ROOT / "stage5-input"
OUTPUT = ROOT / "stage5_localities_5149_v1.jsonl"
EXPECTED_PARTS = 6
EXPECTED_ROWS = 5149
EXPECTED_SHA256 = "3fe392df02bf76e0a6f84ef220433f0b901f97ae09a0a091269deeb2eaf8e9f0"


def main() -> None:
    parts = [
        PART_DIR / f"production_locality_rows_5149_v1.part{i:03d}.jsonl"
        for i in range(1, EXPECTED_PARTS + 1)
    ]
    missing = [str(p.relative_to(ROOT)) for p in parts if not p.exists()]
    if missing:
        raise RuntimeError(f"missing Stage 5 input parts: {missing}")

    raw = b"".join(p.read_bytes() for p in parts)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"locality manifest checksum mismatch: {digest} != {EXPECTED_SHA256}")

    text = raw.decode("utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) != EXPECTED_ROWS:
        raise RuntimeError(f"locality row count mismatch: {len(lines)} != {EXPECTED_ROWS}")

    rows = [json.loads(line) for line in lines]
    if len({r["region_slug"] for r in rows}) != EXPECTED_ROWS:
        raise RuntimeError("region_slug uniqueness failure")
    if len({r["locality_key"] for r in rows}) != EXPECTED_ROWS:
        raise RuntimeError("locality_key uniqueness failure")
    if len({r["variation_signature"] for r in rows}) != EXPECTED_ROWS:
        raise RuntimeError("variation_signature uniqueness failure")
    if any(r.get("landing_eligibility") != "ELIGIBLE_AFTER_SLUG_QA" for r in rows):
        raise RuntimeError("ineligible row present in Stage 5 input")

    OUTPUT.write_bytes(raw)
    print(json.dumps({
        "status": "PASS",
        "rows": len(rows),
        "region_slug_unique": len({r["region_slug"] for r in rows}),
        "locality_key_unique": len({r["locality_key"] for r in rows}),
        "variation_signature_unique": len({r["variation_signature"] for r in rows}),
        "sha256": digest,
        "output": str(OUTPUT.relative_to(ROOT)),
        "production_deploy": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
