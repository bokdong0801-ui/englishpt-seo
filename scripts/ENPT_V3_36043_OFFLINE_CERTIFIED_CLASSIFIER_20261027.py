#!/usr/bin/env python3
"""Correct final offline classification of the actual 36,043 GET-only V3 destination results.
Original CSV full_region ends in '지역 영어 안내'; trim this suffix before checking title/h1.
Do not infer success from generic text '안내'. Never submit a form or mutate Production.
"""
from __future__ import annotations
import collections,csv,datetime,json,pathlib,re,unicodedata
ROOT=pathlib.Path("v3-36043-shards")
OUT=pathlib.Path("v3-36043-certified");OUT.mkdir(exist_ok=True)
COURSES=("elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv","worker-english-conv-academy")
paths=sorted(ROOT.glob("*/RESULTS_5149.csv"))
if len(paths)!=7:raise RuntimeError("HOLD_EXPECTED_7_RESULT_CSV_FOUND_"+str(len(paths)))
allrows=[]
for path in paths:allrows.extend(csv.DictReader(path.open(encoding="utf-8-sig")))
if len(allrows)!=36043 or len({r["preview_url"] for r in allrows})!=36043:raise RuntimeError("HOLD_36043_COVERAGE_UNMET")
def norm(s):return re.sub(r"\s+","",unicodedata.normalize("NFKC",s or "")).lower()
classes=collections.Counter()
for r in allrows:
 display=r["region_full"]
 if not display.endswith(" 지역 영어 안내"):raise RuntimeError("HOLD_UNEXPECTED_DISPLAY_LABEL_"+display[:100])
 place=display.removesuffix(" 지역 영어 안내").strip()
 if len(place.split())<2:raise RuntimeError("HOLD_NO_KOREAN_DISTRICT_"+place)
 dong=place.split()[-1]
 assert dong not in ("안내","영어","지역")
 header=norm(r.get("title","")+" "+r.get("h1",""))
 r["expected_dong"]=dong
 r["locality_in_title_or_h1"]=str(norm(dong) in header)
 if r["http"]!="200":
  cls="HTTP_404" if r["http"]=="404" else "NETWORK_UNKNOWN" if not r["http"] else "HTTP_OTHER"
 elif r["final_url"].rstrip("/")!=r["preview_url"].rstrip("/"):cls="REDIRECT_MISMATCH"
 elif r["canonical"]!=r["production_url"]:cls="CANONICAL_MISMATCH"
 elif not header:cls="MISSING_TITLE_AND_H1"
 elif not norm(dong) in header:cls="LOCALITY_TITLE_REVIEW"
 elif re.search(r"찾을\s*수\s*없|not found|404",r["title"]+" "+r["h1"],re.I):cls="SOFT404"
 else:cls="PASS"
 r["certified_class"]=cls
 classes[cls]+=1
# Every grouped course must cover 5149 unique localities.
bytype=collections.defaultdict(set)
for r in allrows:bytype[r["course"]].add(r["region_slug"])
if set(bytype)!=set(COURSES) or any(len(x)!=5149 for x in bytype.values()):raise RuntimeError("HOLD_COURSE_5149_COVERAGE")
allrows.sort(key=lambda r:r["preview_url"])
with (OUT/"ENPT_V3_36043_CERTIFIED_LIVE_URLS.csv").open("w",newline="",encoding="utf-8-sig") as f:
 w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
errors=[r for r in allrows if r["certified_class"]!="PASS"]
with (OUT/"ENPT_V3_36043_ISSUES_TO_REVIEW.csv").open("w",newline="",encoding="utf-8-sig") as f:
 w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(errors)
summary={"status":"PASS_ALL_36043_REAL_URLS" if not errors else "HOLD_REVIEW_FOLLOWUP_ISSUES",
"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"full_verified_urls":len(allrows),"seven_groups":len(bytype),"unique_5149_each":True,
"http_200":sum(r["http"]=="200" for r in allrows),
"http_404":sum(r["http"]=="404" for r in allrows),
"no_http_response":sum(not r["http"] for r in allrows),
"canonical_self":sum(r["http"]=="200" and r["canonical"]==r["production_url"] for r in allrows),
"title_and_h1_region_pass":sum(r["locality_in_title_or_h1"]=="True" for r in allrows),
"class_counts":dict(sorted(classes.items())),"issue_count":len(errors),
"issues_preview":[{k:r[k] for k in ("preview_url","expected_dong","title","h1","canonical","certified_class")} for r in errors[:40]],
"production_writes":0,"forms_submitted":0}
(OUT/"ENPT_V3_36043_CERTIFIED_SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),"utf8")
print("ENPT_V3_36043_CERTIFIED_STATUS",json.dumps({k:v for k,v in summary.items() if k!="issues_preview"},ensure_ascii=False),flush=True)
