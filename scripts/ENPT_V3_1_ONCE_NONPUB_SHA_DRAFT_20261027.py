#!/usr/bin/env python3
"""EXACTLY ONE full V3.1 nonpublished Netlify draft; 202786 files via SHA reuse.
Uploads only 28 delta HTML files. No Production publish/restore. No automatic retry of POST.
"""
import gzip,hashlib,json,os,pathlib,re,time,urllib.error,urllib.parse,urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
OUT=R/"v3-1-draft-ledger";OUT.mkdir(exist_ok=True)
SOURCE=R/"v3-1-patch-evidence/V3_1_202786_CANDIDATE_FILES_SHA1.json.gz"
DELTA=R/"v3-delta-files"
PUBLISHED="6adafef5f2c6d196833683db"
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
MARKER="ENPT-V3-1-20261027-BYEONGMOKANDONG-7-CORRECTED-NONPUB"
EDGE="1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b"
TOKEN=os.environ["NETLIFY_AUTH_TOKEN"]
BASE="https://api.netlify.com/api/v1/"
def save(n,v):
 (OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),"utf8")
 print("ENPT_V3_1_DRAFT_LEDGER",n,json.dumps(v,ensure_ascii=False)[:1800],flush=True)
def get(path):
 q=urllib.request.Request(BASE+path,method="GET",headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
 with urllib.request.urlopen(q,timeout=45) as r:return json.load(r)
def hold(reason):raise RuntimeError("HOLD_V3_1_"+reason)
def identity():
 s=get("sites/"+SITE)
 if (s.get("published_deploy") or {}).get("id")!=PUBLISHED or s.get("custom_domain")!="englishpt.kr":hold("PRODUCTION_DRIFT")
 return s
assert len(TOKEN)>20
guard=json.loads((R/"v3-1-patch-evidence/V3_1_7_LOCALITY_CORRECTION_SOURCE_GUARD.json").read_text())
assert guard["status"]=="PASS_V3_1_ONLY_7_LOCALITY_SHARDS_PATCHED" and guard["patched_html"]==7
with gzip.open(SOURCE,"rt",encoding="utf8") as f:files=json.load(f)
assert len(files)==202786
bysha={}
for p in DELTA.rglob("*"):
 if p.is_file():
  b=p.read_bytes();sha=hashlib.sha1(b).hexdigest()
  assert files["/"+p.relative_to(DELTA).as_posix()]==sha
  bysha[sha]=(p.relative_to(DELTA).as_posix(),b)
assert len(bysha)==28
site=identity()
account=get("accounts/"+site["account_id"])
if account.get("usages_exceeded") or account.get("configurable_limits_exceeded"):hold("ACCOUNT_CREDIT_EXCEEDED")
history=get("sites/"+SITE+"/deploys?per_page=100")
if any(x.get("title")==MARKER for x in history):hold("EXISTING_MARKER_DO_NOT_DUPLICATE")
payload=json.dumps({"files":files,"edge_functions":{"tar":EDGE},"draft":True,"async":True,"branch":"review-enpt-v3-1-20261027"},separators=(",",":")).encode()
assert len(payload)<24000000
save("01_PREPOST_PRODUCTION_GUARD.json",{"source_production":PUBLISHED,"files":len(files),"delta_files":len(bysha),"no_production_publish":True})
save("02_ONE_NONPUB_POST_ATTEMPT.json",{"status":"ATTEMPTED_DO_NOT_RETRY","marker":MARKER,"count":1})
req=urllib.request.Request(BASE+"sites/"+SITE+"/deploys?"+urllib.parse.urlencode({"title":MARKER}),
 data=payload,method="POST",headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"})
with urllib.request.urlopen(req,timeout=110) as r:d=json.load(r)
did=d.get("id")
if not did or not re.fullmatch(r"[a-f0-9]{24}",did):hold("DRAFT_ID_INVALID")
save("02_ONE_NONPUB_POST_ATTEMPT.json",{"status":"CREATED_NONPUB","draft_id":did,"marker":MARKER,"state":d.get("state"),"published_at":d.get("published_at"),"production_published":0})
for i in range(50):
 identity();d=get("sites/"+SITE+"/deploys/"+did)
 if d.get("state") in ("prepared","uploading","ready"):break
 if d.get("state") in ("failed","error"):hold("DRAFT_PREPARATION_FAILED")
 time.sleep(3)
else:hold("DRAFT_PREPARATION_TIMEOUT")
assert d.get("published_at") is None and d.get("draft") is not False
needed=d.get("required") or []
edge=d.get("required_edge_functions") or []
if set(needed)-set(bysha):hold("NETLIFY_WANTS_UNEXPECTED_EXISTING_ASSETS")
if edge!=[EDGE]:hold("EDGE_TAR_NOT_EXPECTED")
save("03_REQUIRED_FILES.json",{"draft_id":did,"static_required":len(needed),"edge_required":edge,"ready_delta_blobs":len(bysha)})
ledger=[]
for sha in needed:
 identity()
 name,blob=bysha[sha]
 entry={"path":name,"sha1":sha,"state":"ATTEMPTED_NO_RETRY"};ledger.append(entry)
 save("04_STATIC_PUT_LEDGER.json",{"draft_id":did,"files":ledger})
 url=BASE+"deploys/"+did+"/files/"+urllib.parse.quote(name,safe="/")
 rq=urllib.request.Request(url,data=blob,method="PUT",headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/octet-stream"})
 try:
  with urllib.request.urlopen(rq,timeout=60) as result:
   if result.status not in (200,201,202,204):hold("FILE_PUT_HTTP_BAD")
   entry["state"]="UPLOADED"
 except Exception as e:
  entry["state"]="HOLD_AMBIGUOUS_NOT_RETRIED";entry["error"]=str(e)[:160]
  save("04_STATIC_PUT_LEDGER.json",{"draft_id":did,"files":ledger});raise
 save("04_STATIC_PUT_LEDGER.json",{"draft_id":did,"files":ledger})
for i in range(40):
 identity();d=get("sites/"+SITE+"/deploys/"+did)
 if not(d.get("required") or []):break
 time.sleep(2)
else:hold("MISSING_STATIC_UPLOADS")
save("05_ALL_STATICS_VERIFIED_EDGE_PENDING.json",{"status":"PASS_V3_1_ALL_STATICS_UPLOADED","draft_id":did,
"missing_static_count":len(d.get("required") or []),"required_edge":d.get("required_edge_functions"),"production_unchanged":PUBLISHED,"new_production_publishes":0})
print("ENPT_V3_1_CREATED_NONPUB_AND_STATICS_DONE",did,flush=True)
