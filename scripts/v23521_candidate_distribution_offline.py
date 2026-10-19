#!/usr/bin/env python3
"""Profile the exact frozen Production .tar.zst streamed: no deploy and no extracted files."""
import argparse,collections,datetime,hashlib,json,os,pathlib,subprocess,sys,tarfile
def bucket(path):
 h=2166136261
 for b in path.encode("utf8"):
  h=((h^b)*16777619)&0xFFFFFFFF
 return f"{(h>>24)&255:02x}"
def main():
 p=argparse.ArgumentParser();p.add_argument("archive");p.add_argument("--out",required=True);a=p.parse_args()
 report={"status":"RUNNING","source":str(pathlib.Path(a.archive).name),"generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
   "sensitive_data":False,"netlify_uploads":0,"production_deployed":False,"method":"offline_stream_archive",
   "files":0,"directories":0,"regular_bytes":0,"root_files":0,"html_files":0,
   "files_over_10MB":0,"files_over_5MB":0,"no_sharded_root_html":0}
 byext=collections.Counter();bytop=collections.Counter();buckets=collections.Counter()
 known=set();uniquehashes=set();duplicatecontent=0;totalhash=0
 maxes=[];html_root=0
 proc=subprocess.Popen(["zstd","-dc",a.archive],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  with tarfile.open(fileobj=proc.stdout,mode="r|") as archive:
   for m in archive:
    n=m.name.removeprefix("./").strip("/")
    if not n:continue
    if m.isdir():report["directories"]+=1;continue
    if not m.isfile():continue
    report["files"]+=1;report["regular_bytes"]+=m.size
    top=n.split("/",1)[0];bytop[top if "/" in n else "(root)"]+=1
    if "/" not in n:report["root_files"]+=1
    if n.endswith(".html"):
     report["html_files"]+=1
     if "/" not in n:html_root+=1
     if "/" not in n and n not in ("index.html","404.html"):
      buckets[bucket(n)]+=1
    if m.size>10000000:report["files_over_10MB"]+=1
    if m.size>5000000:report["files_over_5MB"]+=1
    ext=n.rsplit(".",1)[-1].lower() if "." in n else "(noext)"
    byext[ext]+=1
    if len(maxes)<12:
      maxes.append((m.size,n));maxes.sort(reverse=True)
    elif m.size>maxes[-1][0]:
      maxes.append((m.size,n));maxes.sort(reverse=True);maxes.pop()
    if n in ("index.html","404.html","pilot.js","_headers","_redirects","sitemap-index.xml","robots.txt"):
      known.add(n)
    blob=archive.extractfile(m)
    if blob is None:raise ValueError("missing tar member "+n)
    h=hashlib.sha1()
    while True:
      block=blob.read(512*1024)
      if not block:break
      h.update(block)
    d=h.hexdigest()
    if d in uniquehashes:duplicatecontent+=1
    else:uniquehashes.add(d)
    if report["files"]%25000==0:print("PROFILE_PROGRESS",report["files"],report["regular_bytes"],flush=True)
  if proc.wait(timeout=90)!=0:raise RuntimeError("zstd decompression failed")
 except Exception:
  proc.kill();raise
 finally:
  try:proc.stderr.close()
  except:pass
 report.update({
  "source_html_in_root":html_root,
  "unique_sha1_content":len(uniquehashes),
  "duplicate_content_instances":duplicatecontent,
  "all_html_shard_bucket_count":len(buckets),
  "hash_scheme":"FNV1a32 high byte into /__pages/00..ff/<root-file>.html, original route internal rewrite",
  "hash_shards_max_files":max(buckets.values()) if buckets else 0,
  "hash_shards_min_files":min(buckets.values()) if buckets else 0,
  "hash_shard_file_counts":dict(sorted(buckets.items())),
  "other_non_html_root_files":report["root_files"]-html_root,
  "projected_root_files_after_html_shard":report["root_files"]-html_root+int("index.html" in known)+int("404.html" in known),
  "prefix_top_folders":dict(bytop),
  "extension_counts":dict(byext),
  "largest_files":[{"path":n,"bytes":s} for s,n in maxes],
  "presence":sorted(known),
  "max_docs_per_directory":54000,
  "source_root_exceeds_limit":report["root_files"]>54000,
  "all_shards_safely_below_limit":max(buckets.values())<54000 if buckets else False,
  "index_html_kept_at_root":("index.html" in known),
  "file_content_processed_SHA1":report["files"],
  "status":"PASS_OFFLINE_FILES_AND_CONTENT_DISTRIBUTION" if report["files"]>=158573 and report["html_files"]>=158573 else "HOLD_UNEXPECTED_SITE_SIZE"})
 pathlib.Path(a.out).parent.mkdir(parents=True,exist_ok=True)
 pathlib.Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("OFFLINE_SITE_DISTRIBUTION_SUMMARY",json.dumps({k:v for k,v in report.items() if k not in ("hash_shard_file_counts","prefix_top_folders","extension_counts","largest_files")},ensure_ascii=False),flush=True)
 return 0 if report["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
