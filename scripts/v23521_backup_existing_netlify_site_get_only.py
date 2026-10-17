#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only complete old Production deployed-file backup if small enough.
GET from Netlify API only. Verifies CURRENT published deploy exactly equals protected ID,
checks file listing, and may export an independent archive with verified file SHA1.
NO Production deployment, no UI settings change, no form data, no POST.
"""
import datetime, hashlib, json, os, pathlib, re, sys, time, urllib.parse, urllib.request, urllib.error, zipfile
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
OLD="6ac4bd517c30220008bb9661"
API="https://api.netlify.com/api/v1"
OUT=pathlib.Path("production-original-backup")
OUT.mkdir(exist_ok=True)
STATE={"status":"STARTED","timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "site_id":SITE,"expected_old_deploy":OLD,"production_deployed":False,
  "netlify_changes":False,"forms_submitted":False,"credit_purchased":False,
  "original_backup_complete":False,"file_manifest_count":None,"errors":[],"warnings":[]}
TOKEN=os.environ.get("NETLIFY_AUTH_TOKEN","")
MAX_FILES=2500
MAX_BYTES=120*1024*1024

def get(path, raw=False, max_len=None):
  hdr={"Authorization":"Bearer "+TOKEN,"Accept":"application/json"}
  if raw:
    hdr["Content-Type"]="application/vnd.bitballoon.v1.raw"
    hdr["Accept"]="application/vnd.bitballoon.v1.raw"
  req=urllib.request.Request(API+path,headers=hdr,method="GET")
  with urllib.request.urlopen(req,timeout=55) as resp:
    data=resp.read() if max_len is None else resp.read(max_len)
    return data,dict(resp.headers)

def stamp():
  (OUT/"BACKUP_STATUS.json").write_text(json.dumps(STATE,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def safe_path(x):
  if not isinstance(x,str) or not x.startswith("/"):
    raise ValueError("Invalid file path")
  a=x.lstrip("/")
  if not a or "//" in a or any(p in ("",".","..") for p in a.split("/")) or "\\" in a:
    raise ValueError("Path traversal or ambiguity")
  return a
def main():
  try:
    if not TOKEN: raise RuntimeError("Netlify token missing")
    site=json.loads(get("/sites/"+SITE)[0])
    if site.get("id")!=SITE or site.get("custom_domain") not in ("englishpt.kr","www.englishpt.kr"):
      raise ValueError("Site identity check failed")
    published=(site.get("published_deploy") or {}).get("id")
    STATE["published_deploy_id"]=published
    if published!=OLD: raise ValueError("Current Production deploy differs from protected OLD snapshot; STOP")
    dep=json.loads(get("/sites/"+SITE+"/deploys/"+OLD)[0])
    if dep.get("id")!=OLD or dep.get("state")!="ready" or dep.get("context")!="production":
      raise ValueError("Old deploy no longer a ready Production deploy")
    STATE["rollback_deploy_status"]="READY"
    STATE["rollback_deploy_url"]="https://app.netlify.com/sites/"+site["name"]+"/deploys/"+OLD
    # API returns original uploaded files, not HTML rewritten by Netlify.
    content,headers=get("/sites/"+SITE+"/files")
    listing=json.loads(content)
    if not isinstance(listing,list):
      raise ValueError("GET site files did not return list")
    paths=set();size_sum=0
    for f in listing:
      a=safe_path(f.get("path"))
      if a in paths:raise ValueError("Duplicate file path: "+a)
      paths.add(a)
      size=f.get("size")
      if not isinstance(size,int) or size<0:raise ValueError("Missing file size")
      size_sum+=size
      if not re.fullmatch(r"[a-f0-9]{40}",str(f.get("sha",""))):
        raise ValueError("Missing SHA1 in Netlify file manifest")
    STATE["file_manifest_count"]=len(listing)
    STATE["file_manifest_bytes"]=size_sum
    STATE["file_manifest_complete"]=True
    STATE["manifest_has_index"]="index.html" in paths
    STATE["list_response_has_link_header"]=bool(headers.get("Link"))
    STATE["list_response_x_total_count"]=headers.get("X-Total-Count")
    manifest={"site_id":SITE,"deploy_id":OLD,"generated_at_utc":STATE["timestamp_utc"],
       "files":[{"path":f["path"],"sha":f["sha"],"size":f["size"]} for f in listing]}
    (OUT/"NETLIFY_ORIGINAL_DEPLOY_FILE_MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if len(paths)>MAX_FILES or size_sum>MAX_BYTES:
      STATE["status"]="MANUAL_FULL_ZIP_BACKUP_REQUIRED_TOO_LARGE_FOR_SAFE_API_LOOP"
      STATE["warnings"].append(f"GET-only manifest captured; {len(paths)} original files / {size_sum} bytes. Do not issue large unbounded per-file API requests. Use Netlify deploy Download ZIP.")
      return 0
    STATE["backup_attempted"]=True
    zipfile_path=OUT/("ENGLISHPT_ORIGINAL_PRODUCTION_"+OLD+".zip")
    count=0
    with zipfile.ZipFile(zipfile_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
      for row in listing:
        p=safe_path(row["path"])
        raw,meta=get("/sites/"+SITE+"/files/"+urllib.parse.quote(p,safe="/"),raw=True)
        if len(raw)!=row["size"]:
          raise ValueError(f"Raw asset size mismatch {p} {len(raw)} != {row['size']}")
        if hashlib.sha1(raw).hexdigest()!=row["sha"]:
          raise ValueError("Netlify asset SHA1 mismatched: "+p)
        z.writestr(p,raw)
        count+=1
        if count%250==0:print("BACKUP_READONLY_FILE_PROGRESS",count,len(listing),flush=True)
    with zipfile.ZipFile(zipfile_path) as z:
      names=z.namelist()
      assert len(names)==len(listing) and set(names)==paths, "ZIP integrity/manifest mismatch"
      assert z.testzip() is None, "ZIP CRC failed"
    digest=hashlib.sha256(zipfile_path.read_bytes()).hexdigest()
    STATE.update({"status":"PASS_FULL_INDEPENDENT_PRODUCTION_ORIGINAL_BACKUP","original_backup_complete":True,
      "archive_sha256":digest,"archive_name":zipfile_path.name,"archive_bytes":zipfile_path.stat().st_size,
      "api_raw_sha1_verified_count":count,"zip_integrity_checked":True})
    (OUT/"ORIGINAL_DEPLOY_BACKUP_SHA256.txt").write_text(digest+"  "+zipfile_path.name+"\n",encoding="utf8")
    return 0
  except Exception as e:
    STATE["errors"].append(type(e).__name__+": "+str(e)[:220])
    STATE["status"]="HOLD_ORIGINAL_BACKUP_FAILED"
    return 1
  finally:
    stamp()
    print("BACKUP_FINAL_STATUS",json.dumps({k:v for k,v in STATE.items() if k not in ("warnings",)},ensure_ascii=False),flush=True)
if __name__=="__main__":sys.exit(main())
