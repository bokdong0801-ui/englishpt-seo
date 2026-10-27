#!/usr/bin/env python3
"""Compare legacy 36043 V3 route audit + 57 exception fixes with NEW 36043 rerun.
Two independent data sets, exact URL keys, no HTTP, production writes or form posts.
"""
import csv,collections,json,pathlib,datetime,sys
A=pathlib.Path("comparison-old");B=pathlib.Path("comparison-new");C=pathlib.Path("comparison-retry57")
OUT=pathlib.Path("v3-36043-comparison-evidence");OUT.mkdir(exist_ok=True)
def pick(root,required,count):
 options=[]
 for p in root.rglob("*.csv"):
  try:
   with p.open(encoding="utf-8-sig",newline="") as f:
    reader=csv.DictReader(f)
    if not required.issubset(reader.fieldnames or []):continue
    entries=list(reader)
    if len(entries)==count:options.append((p,entries))
  except Exception:continue
 assert len(options)==1,(root,[(str(a),len(b)) for a,b in options])
 return options[0]
oldfile,old=pick(A,{"preview_url","http","canonical"},36043)
newfile,new=pick(B,{"route","http","canonical","town_text_present"},36043)
rfile,retry=pick(C,{"preview_url","result"},57)
base="https://review-enpt-v3-fullsite-20261027--englishpt-seo.netlify.app/"
def path(r):
 return r["preview_url"].removeprefix(base)
pold={path(r):r for r in old}
pnew={r["route"]:r for r in new}
pr={path(r):r for r in retry}
assert len(pold)==len(pnew)==36043 and set(pold)==set(pnew),("MISSING_OR_EXTRA_ROUTES",len(set(pold)-set(pnew)),len(set(pnew)-set(pold)))
assert len(pr)==57 and set(pr)<=set(pold)
assert all(r["result"]=="PASS" for r in retry)
changes=[];classification=collections.Counter();regressions=[];newly_unverified=[];improved=[]
for route in sorted(pold):
 o=pold[route];n=pnew[route]
 original_good=o["http"]=="200" and o["final_url"]==o["preview_url"] and o["canonical"]==o["production_url"]
 if route in pr:original_good=pr[route]["result"]=="PASS"
 latest_good=str(n["http"])=="200" and n["final_url"]==base+route and n["canonical"]=="https://englishpt.kr/"+route and str(n["town_text_present"]).lower()=="true"
 if latest_good and original_good:cls="BOTH_PASSED"
 elif latest_good:cls="NEW_PASSED_PREVIOUS_UNCONFIRMED"
 elif original_good:cls="NEW_UNCONFIRMED_OR_REGRESSED"
 else:cls="BOTH_NEED_REVIEW"
 classification[cls]+=1
 if cls in ("NEW_UNCONFIRMED_OR_REGRESSED","BOTH_NEED_REVIEW"):
  r={"route":route,"previous_http":o["http"],"previous_canonical":o["canonical"],"previous_retry":pr.get(route,{}).get("result",""),
  "latest_http":n["http"],"latest_result":n["result"],"latest_canonical":n["canonical"],"latest_town_match":n["town_text_present"],"error":n["error"]}
  regressions.append(r)
 if cls=="NEW_PASSED_PREVIOUS_UNCONFIRMED":improved.append(route)
summary={"status":"PASS_NEW_AND_OLD_CONSISTENT" if not regressions else "HOLD_REVIEW_NEW_EXCEPTIONS",
 "old_source_csv":str(oldfile),"new_source_csv":str(newfile),"retry_source_csv":str(rfile),
 "expected_routes":36043,"previous_total":len(old),"new_total":len(new),"previous_exceptions_rechecked":len(pr),
 "class_counts":dict(classification),"new_http_404":sum(str(x["http"])=="404" for x in new),
 "new_network_or_unconfirmed":sum(str(x["http"]) in ("","None") for x in new),
 "new_canonical_correct":sum(x["canonical"]=="https://englishpt.kr/"+x["route"] for x in new),
 "new_town_text_present":sum(str(x["town_text_present"]).lower()=="true" for x in new),
 "regressions_or_unverified":len(regressions),"recovered_vs_prior":len(improved),
 "regression_examples":regressions[:25],"previous_57_all_pass":True,
 "production_posts":0,"form_submits":0,"timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/"V3_36043_OLD_VS_NEW_RECONCILIATION.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),"utf8")
with (OUT/"V3_OLD_VS_NEW_ISSUES.csv").open("w",newline="",encoding="utf-8-sig") as f:
 fields=["route","previous_http","previous_canonical","previous_retry","latest_http","latest_result","latest_canonical","latest_town_match","error"]
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(regressions)
print("ENPT_V3_36043_RECONCILIATION",json.dumps({k:v for k,v in summary.items() if k!="regression_examples"},ensure_ascii=False),flush=True)
