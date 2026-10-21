#!/usr/bin/env python3
"""Read-only six local student route completeness from signed authoritative SEO route map."""
import collections,csv,gzip,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
source=root/"signed-qa-map"/"NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
with gzip.open(source,"rt",encoding="utf8") as f: m=json.load(f)["original_public_html_to_data_payload"]
assert len(m)==158571
suffix="-worker-english-conv-academy.html"
slugs=sorted(r[:-len(suffix)] for r in m if r.endswith(suffix) and not r.startswith("station-"))
assert len(slugs)==6060 and len(set(slugs))==6060,("locality_count",len(slugs))
courses=("elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv")
rows=[];missing=[]
for slug in slugs:
 for typ in courses:
  route=slug+"-"+typ+".html"
  exists=route in m
  rows.append({"slug":slug,"course":typ,"route":route,"exists":exists,"noindex":m[route]["noindex"] if exists else ""})
  if not exists:missing.append(route)
out=pathlib.Path("four-route-qa");out.mkdir(exist_ok=True)
with (out/"ALL_36360_STUDENT_DESTINATIONS.csv").open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
res={"status":"PASS_6060_LOCALITIES_36360_STUDENT_LINK_TARGETS_EXISTS" if not missing else "HOLD_MISSING_STUDENT_ROUTES","localities":len(slugs),"courses_per_locality":len(courses),"checked_destinations":len(rows),"missing_count":len(missing),"missing_examples":missing[:30],"signed_generated_pages":len(m),"noindex_policies_modified":0,"production_published":False}
(out/"ALL_36360_QA_SUMMARY.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),"utf8")
print("ENPT_SIX_COURSES_ALL_LOCALITIES_QA",json.dumps(res,ensure_ascii=False),flush=True)
if missing:raise SystemExit(1)
