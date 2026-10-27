#!/usr/bin/env python3
"""Patch ONLY seven corrupted 읍면동 course pages in a V3.1 nonpublished SHA manifest.
Never mutate Production; preserve all existing 202786 paths and other content byte-for-byte.
"""
from __future__ import annotations
import csv,gzip,hashlib,html.parser,json,pathlib,urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
OUT=R/"v3-1-patch-evidence";OUT.mkdir(exist_ok=True)
SRC=R/"v3-digest-qa/V3_202786_CANDIDATE_FILES_SHA1.json.gz"
DELTA=R/"v3-delta-files"
SIGN=R/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
REF=R/"published-manifest/PUBLISHED_202768_STATIC_SHA1_MANIFEST.json.gz"
HOST="https://6adafef5f2c6d196833683db--englishpt-seo.netlify.app/"
COURSES=("elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv","worker-english-conv-academy")
PREFIX="gyeonggi-anyang-manan-byeongmokandong-"
WRONG="가장 어려운 부분안동";CORRECT="병목안동"
def ssha(b):return hashlib.sha1(b).hexdigest()
with gzip.open(SRC,"rt",encoding="utf8") as f:manifest=json.load(f)
with gzip.open(SIGN,"rt",encoding="utf8") as f:mapdata=json.load(f)["original_public_html_to_data_payload"]
with gzip.open(REF,"rt",encoding="utf8") as f:ref=json.load(f)
assert len(manifest)==202786 and len(ref)==202768 and len(mapdata)==158571
before=dict(manifest);records=[]
for course in COURSES:
 route=PREFIX+course+".html"
 assert route in mapdata,("ROUTE_NOT_SIGNED",route)
 shard="/"+mapdata[route]["to"]
 assert shard in before and shard in ref
 assert manifest[shard]==ref[shard],("UNEXPECTED_V3_CHANGE",route)
 req=urllib.request.Request(HOST+shard.lstrip("/"),method="GET",headers={"User-Agent":"ENPT-Owner-Safe-7-HTML-Correction"})
 with urllib.request.urlopen(req,timeout=35) as resp:
  assert resp.status==200
  raw=resp.read(400000)
 assert ssha(raw)==ref[shard],("SOURCE_SHA_DRIFT",route)
 s=raw.decode("utf8","strict")
 occurrences=s.count(WRONG)
 assert occurrences>=1,("REPLACEMENT_NOT_FOUND",route)
 assert "<title>" in s and "<h1" in s
 amended=s.replace(WRONG,CORRECT)
 assert WRONG not in amended and CORRECT in amended
 assert amended!=s
 assert 'englishpt-consultation' in s and 'englishpt-consultation' in amended
 assert 'name="robots"' in s and 'name="robots"' in amended
 assert len(amended.encode("utf8"))<400000
 loc=DELTA/shard.lstrip("/");loc.parent.mkdir(parents=True,exist_ok=True)
 loc.write_text(amended,"utf8")
 newsha=ssha(loc.read_bytes())
 assert newsha!=ref[shard]
 manifest[shard]=newsha
 records.append({"course":course,"route":route,"shard":shard,"before_sha":ref[shard],"after_sha":newsha,"wrong_replacements":occurrences,"content_before_bytes":len(raw),"content_after_bytes":len(amended.encode())})
# 18 new + 10 changed = 28 exact source blobs; no extra or old file deletion.
files=[p for p in DELTA.rglob("*") if p.is_file()]
assert len(files)==28,("DELTA_FILES",len(files))
assert len(manifest)==202786 and set(manifest)==set(before)
changed=[k for k,v in manifest.items() if v!=before[k]]
assert len(changed)==7 and set(changed)=={r["shard"] for r in records}
with gzip.open(OUT/"V3_1_202786_CANDIDATE_FILES_SHA1.json.gz","wt",encoding="utf8") as f:json.dump(manifest,f,separators=(",",":"))
proof={"status":"PASS_V3_1_ONLY_7_LOCALITY_SHARDS_PATCHED","patched_html":7,"changed_from_immutable_published":10,
"original_sitemap_shards":44,"total_paths":202786,"new_regions":18,"source_existing_routes":158571,
"unchanged_old_paths":202758,"bad_phrase_remaining":0,"result_page_title_locality":"병목안동",
"all_36043_link_destinations_unmodified":True,"production_writes":0,"form_submissions":0,"changes":records}
(OUT/"V3_1_7_LOCALITY_CORRECTION_SOURCE_GUARD.json").write_text(json.dumps(proof,ensure_ascii=False,indent=2),"utf8")
print("ENPT_V3_1_LOCALITY_REPAIR_GUARD",json.dumps({k:v for k,v in proof.items() if k!="changes"},ensure_ascii=False),flush=True)
