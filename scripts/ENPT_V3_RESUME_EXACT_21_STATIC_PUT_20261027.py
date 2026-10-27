#!/usr/bin/env python3
"""Resume exact 6ae04e V3 nonpublished prepared draft; ONLY PUT its 21 required new static SHA.
No deploy creation, no Production publish, no Netlify site settings, and no form POST.
"""
import datetime,gzip,hashlib,json,os,pathlib,time,urllib.request,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"v3-resume-evidence"
DELTA=ROOT/"v3-delta-files"
MANIFEST=ROOT/"v3-digest-qa/V3_SHA_ONLY_SOURCE_GUARD.json"
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PUBLISHED="6adafef5f2c6d196833683db"
DRAFT="6ae04e7fd0a35eb412bbe704"
MARKER="ENPT-V3-20261027-202786-SHA-REUSE-NONPUBLISHED-ONCE"
TAR="1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b"
TOKEN=os.environ["NETLIFY_AUTH_TOKEN"]
API="https://api.netlify.com/api/v1/"
OUT.mkdir(exist_ok=True)
def log(file,payload):
 (OUT/file).write_text(json.dumps(payload,ensure_ascii=False,indent=2),"utf8")
 print("ENPT_V3_RESUME_STATIC",file,json.dumps(payload,ensure_ascii=False)[:1400],flush=True)
def get(uri):
 q=urllib.request.Request(API+uri,method="GET",headers={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"})
 with urllib.request.urlopen(q,timeout=45) as r:return json.load(r)
def identity():
 site=get("sites/"+SITE)
 assert site.get("custom_domain")=="englishpt.kr"
 assert (site.get("published_deploy") or {}).get("id")==PUBLISHED,"HOLD_PROD_CHANGED"
 d=get("sites/"+SITE+"/deploys/"+DRAFT)
 assert d.get("id")==DRAFT and d.get("site_id")==SITE and d.get("title")==MARKER
 assert d.get("published_at") is None and d.get("draft") is not False,"HOLD_NOT_NONPUB"
 assert d.get("state") in ("prepared","uploading","uploaded","ready"),"HOLD_DRAFT_STATE"
 return d
assert json.loads(MANIFEST.read_text("utf8"))["status"]=="PASS_V3_202786_SHA1_FILE_SOURCE_ONLY"
bysha={}
for p in DELTA.rglob("*"):
 if p.is_file():
  blob=p.read_bytes()
  bysha[hashlib.sha1(blob).hexdigest()]=(p.relative_to(DELTA).as_posix(),blob)
assert len(bysha)==21,"HOLD_WRONG_DELTA_COUNT"
d=identity()
needed=d.get("required") or []
assert len(needed)<=21 and set(needed).issubset(bysha),"HOLD_UNKNOWN_REQUIRED_STATIC"
assert d.get("required_edge_functions")==[TAR],"HOLD_UNEXPECTED_EDGE_REQUIREMENT"
pre={"status":"PASS_READY_TO_PUT_REQUIRED_STATIC","published_id":PUBLISHED,"draft_id":DRAFT,"required_static":len(needed),"edge_required":[TAR],"delta_sources":len(bysha),"production_writes":0}
log("01_EXACT_EXISTING_DRAFT_GUARD.json",pre)
attempt=[]
for sha in needed:
 identity()
 path,data=bysha[sha]
 entry={"sha":sha,"path":path,"bytes":len(data),"state":"ATTEMPTED_DO_NOT_DUPLICATE"}
 attempt.append(entry)
 log("02_STATIC_UPLOAD_LEDGER.json",{"draft":DRAFT,"uploads":attempt})
 url=API+"deploys/"+DRAFT+"/files/"+urllib.parse.quote(path,safe="/")
 q=urllib.request.Request(url,data=data,method="PUT",headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/octet-stream"})
 try:
  with urllib.request.urlopen(q,timeout=55) as r:
   assert r.status in (200,201,202,204),"HOLD_BAD_PUT_RESPONSE"
   entry["state"]="UPLOADED"
 except Exception as e:
  entry["state"]="HOLD_UPLOAD_AMBIGUOUS"
  entry["error"]=str(e)[:220]
  log("02_STATIC_UPLOAD_LEDGER.json",{"draft":DRAFT,"uploads":attempt})
  raise
 log("02_STATIC_UPLOAD_LEDGER.json",{"draft":DRAFT,"uploads":attempt})
for n in range(28):
 d=identity()
 if not (d.get("required") or []):break
 time.sleep(2)
else:raise RuntimeError("HOLD_UPLOAD_REMAINING")
out={"status":"PASS_ALL_21_STATIC_UPLOADS_RECONCILED","draft_id":DRAFT,"published_id_unchanged":PUBLISHED,
     "remaining_static_sha":d.get("required") or [],"edge_required":d.get("required_edge_functions") or [],
     "draft_state":d.get("state"),"uploaded_count":len(needed),"new_deploys":0,"production_changes":0}
log("03_STATIC_READY_EDGE_REQUIRED.json",out)
