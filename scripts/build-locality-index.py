#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PARTS=ROOT/"stage5-input"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); args=ap.parse_args()
    rows=[]
    for p in sorted(PARTS.glob("production_locality_rows_5149_v1.part*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            r=json.loads(line)
            rows.append({
                "sido":r["sido"],
                "jurisdiction":r["jurisdiction_full"],
                "dong":r["dong_name"],
                "slug":r["region_slug"]
            })
    assert len(rows)==5149,len(rows)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(rows,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(json.dumps({"status":"PASS_LOCALITY_INDEX","rows":len(rows),"output":str(out)},ensure_ascii=False))
if __name__=="__main__": main()
