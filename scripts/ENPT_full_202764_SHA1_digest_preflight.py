#!/usr/bin/env python3
import hashlib,json,pathlib,gzip,datetime
root=pathlib.Path("thumb-21964-candidate")
assert root.is_dir()
paths={}
for i,p in enumerate(sorted(root.rglob("*"))):
 if not p.is_file(): continue
 rel="/"+p.relative_to(root).as_posix()
 h=hashlib.sha1()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 paths[rel]=h.hexdigest()
 if len(paths)%25000==0:print("HASHED",len(paths),flush=True)
assert len(paths)==202764,len(paths)
assert sum(x.startswith("/assets/images/seo-square/v1/") for x in paths)==21964
assert sum(x.startswith("/__pages/") for x in paths)==158571
assert "/index.html" in paths and "/netlify.toml" in paths
assert "X-Robots-Tag: noindex, nofollow" not in (root/"_headers").read_text()
out=pathlib.Path("async-digest-evidence");out.mkdir(exist_ok=True)
with gzip.open(out/"ALL_202764_PATH_SHA1.json.gz","wt",encoding="utf8") as f:json.dump(paths,f,separators=(",",":"),sort_keys=True)
info={"status":"PASS_202764_EXACT_FILES_SHA1_READY_FOR_ASYNC_DRAFT","files":len(paths),"square_jpegs":21964,"seo_pages":158571,"global_noindex":False,"draft_created":False,"production_changed":False,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
(out/"QA.json").write_text(json.dumps(info,indent=2))
print("ENPT_ASYNC_DIGEST_202764_READY",json.dumps(info),flush=True)
