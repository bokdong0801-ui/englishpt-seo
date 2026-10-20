#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline checkpoint union proof; final Netlify state is GET-only. No deploy or upload."""
import csv,json,os,pathlib,urllib.request,datetime
ROOT=pathlib.Path.cwd()
OUT=ROOT/"final-20600-audit";OUT.mkdir(exist_ok=True)
def find(directory,filename):
 xs=list((ROOT/directory).rglob(filename))
 if len(xs)!=1:raise ValueError(directory+": expected one "+filename+" found "+str(len(xs)))
 return xs[0]
snapshot=list(csv.DictReader(find("required-snapshot","REQUIRED_SHA_TO_PATHS.csv").open(encoding="utf-8-sig",newline="")))
original={r["required_sha1"] for r in snapshot}
assert len(snapshot)==len(original)==20600
sources=[
 ("first200-snapshot","03_BATCH_SHA_PUT_CHECKPOINT.json",200,True),
 ("second1200-snapshot","03_RESUMABLE_PUT_PROGRESS.json",1194,False),
 ("prior6000-snapshot","03_RESUMABLE_PUT_PROGRESS.json",6000,False),
 ("prior4000a-snapshot","03_RESUMABLE_PUT_PROGRESS.json",4000,False),
 ("prior4000b-snapshot","03_RESUMABLE_PUT_PROGRESS.json",4000,False),
 ("prior4000c-snapshot","03_RESUMABLE_PUT_PROGRESS.json",4000,False),
 ("final1206-snapshot","03_RESUMABLE_PUT_PROGRESS.json",1206,False)
]
done=set();parts=[]
for folder,filename,num,first in sources:
 r=json.loads(find(folder,filename).read_text("utf8"))
 completed=r["completed_files"] if first else r["completed"]
 vals={x["sha"] for x in completed}
 if len(completed)!=num or len(vals)!=num:raise ValueError(folder+": wrong completed")
 if r.get("http_success",num)!=num and not first:raise ValueError(folder+": HTTP success mismatch")
 if first:
  assert r["status"]=="PASS_ALL_REQUESTED_FIRST_BATCH_UPLOAD_HTTP"
  assert r["verified_http_PUTs"]==200
 else:
  if folder!="second1200-snapshot":
   assert r["status"]=="PASS_NEXT_BATCH_ALL_REQUIRED_SHA_ACCEPTED"
   assert not r.get("ambiguous") and not r.get("failed")
  else:
   assert r["status"]=="HOLD_PARTIAL_OR_UNCERTAIN_UPLOAD_DO_NOT_REPEAT"
   assert len(r.get("ambiguous",[]))==6 and not r.get("failed")
 if vals&done:raise ValueError(folder+": completed SHA overlap")
 done.update(vals)
 parts.append({"source":folder,"verified_successful_sha":len(vals),"cumulative_verified_sha":len(done)})
assert done==original and len(done)==20600, "FULL INITIAL NETLIFY REQUIRED SHA LIST NOT COVERED"
siteid="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
did="6ad708da374d457504481d5c"
baseline="6ad5eb4918f9411c4d5e1ba4"
token=os.environ["NETLIFY_AUTH_TOKEN"]
def get(p):
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+p,method="GET",headers={"Authorization":"Bearer "+token})
 with urllib.request.urlopen(req,timeout=35) as resp:return json.load(resp)
site=get("sites/"+siteid);draft=get("sites/"+siteid+"/deploys/"+did)
assert site.get("id")==siteid and site.get("custom_domain")=="englishpt.kr"
published=(site.get("published_deploy") or {}).get("id")
assert published==baseline,"PRODUCTION DRIFT"
assert draft.get("id")==did and draft.get("site_id")==siteid
assert draft.get("title")=="ENPT-21964-OG-ASYNC-DIGEST-ONE-DRAFT-NOT-PRODUCTION-20261020"
assert draft.get("published_at") is None,"DRAFT PUBLISHED WITHOUT APPROVAL"
result={"status":"PASS_ALL_INITIAL_20600_REQUIRED_SHA_HTTP_SUCCESS_AND_PRODUCTION_UNCHANGED",
 "verified_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "original_netlify_required_sha_count":20600,
 "unique_confirmed_http_success_sha":len(done),"missing_sha_count":len(original-done),
 "checkpoint_parts":parts,"existing_async_draft_id":did,"draft_state":draft.get("state"),
 "still_required_static_count":len(draft.get("required") or []),
 "still_required_edge_count":len(draft.get("required_edge_functions") or []),
 "required_edge_sha":draft.get("required_edge_functions") or [],
 "production_id":published,"production_changed":False,
 "draft_ready":draft.get("state")=="ready","draft_published":False,"new_deploys":0,
 "additional_uploads":0,"GET_only":True,"preview_url":draft.get("deploy_ssl_url"),
 "QA_note":"All initially required 20600 SHA confirmed HTTP success. Netlify may remain uploading while Edge TAR is missing. This is not a site READY or HTTP visual QA result."}
(OUT/"FULL_ORIGINAL_20600_NETLIFY_REQUIRED_SHA_CHECKPOINT_UNION_QA.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("ENPT_FINAL_20600_ALL_REQUIRED_SHA_VERIFIED",json.dumps(result,ensure_ascii=False),flush=True)
