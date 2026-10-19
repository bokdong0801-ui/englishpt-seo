#!/usr/bin/env python3
"""Build a complete Netlify async+draft file digest payload OFFLINE only.
Nothing is uploaded to Netlify. No credential is read. No API call occurs.
Purpose: measure JSON size, filename collisions, file sizes and directory limits.
"""
import argparse,collections,datetime,hashlib,json,pathlib,subprocess,tarfile,sys
EXPECTED_SHA="e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba"
def shard(name):
 h=2166136261
 for b in name.encode("utf8"):h=((h^b)*16777619)&0xffffffff
 return f"{h>>24:02x}"
def main():
 p=argparse.ArgumentParser();p.add_argument("tar_zst");p.add_argument("--output-dir",required=True);args=p.parse_args()
 out=pathlib.Path(args.output_dir);out.mkdir(exist_ok=True,parents=True)
 files={};sizes=collections.Counter();total_bytes=0;root_html=0;src_names=set();sources_with_different_paths=0;maxima=[]
 csum=hashlib.sha256()
 with open(args.tar_zst,"rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):csum.update(block)
 actual_sha=csum.hexdigest()
 if actual_sha!=EXPECTED_SHA:raise ValueError("Wrong original frozen file SHA")
 process=subprocess.Popen(["zstd","-dc",args.tar_zst],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  with tarfile.open(fileobj=process.stdout,mode="r|") as stream:
   for member in stream:
    orig=member.name.removeprefix("./")
    if not orig or member.isdir():continue
    if not member.isfile():raise ValueError("Non-regular source artifact member")
    if orig in src_names:raise ValueError("Duplicate original member "+orig)
    src_names.add(orig)
    dest=orig
    if "/" not in orig and orig.endswith(".html") and orig not in ("index.html","404.html"):
     root_html+=1
     dest="__pages/"+shard(orig)+"/"+orig
    if dest!=orig:sources_with_different_paths+=1
    if "/"+dest in files:raise ValueError("Collision between staged target paths")
    b=stream.extractfile(member)
    if b is None:raise ValueError("Could not read source archive file")
    digest=hashlib.sha1()
    while 1:
     chunk=b.read(512*1024)
     if not chunk:break
     digest.update(chunk)
    files["/"+dest]=digest.hexdigest()
    folder=dest.rsplit("/",1)[0] if "/" in dest else "(root)"
    sizes[folder]+=1
    total_bytes+=member.size
    maxima.append(member.size)
    if len(files)%25000==0:print("ASYNCDIGEST_PROGRESS",len(files),flush=True)
  if process.wait(timeout=90)!=0:raise ValueError("ZSTD read failure")
 finally:
  process.stderr.close()
 # "draft": true means do not change live published version, "async" handles large manifest preparation.
 #  Must not POST it without NEW user authorization.
 payload={"async":True,"draft":True,"files":files}
 blob=json.dumps(payload,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode("utf8")
 manifest_sha=hashlib.sha256(blob).hexdigest()
 (out/"ASYNC_DRAFT_SHARDED_NETLIFY_SHA1_DIGEST_OFFLINE_NOT_SENT.json").write_bytes(blob)
 dirworst=sorted(sizes.items(),key=lambda x:x[1],reverse=True)[:12]
 report={
  "status":"PASS_OFFLINE_SHA1_ASYNC_DRAFT_SHARD_PAYLOAD_FEASIBILITY",
  "source_archive_sha256":actual_sha,
  "analysis_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "site_ever_contacted":False,"netlify_api_writes":0,"production_deployed":False,
  "source_regular_file_count":len(src_names),"manifest_file_count":len(files),
  "root_html_relocated":root_html,"raw_source_bytes":total_bytes,
  "unique_file_sha1":len(set(files.values())),"duplicate_SHA1_instances":len(files)-len(set(files.values())),
  "all_files_referenced_once":len(src_names)==len(files),
  "manifest_json_bytes":len(blob),"manifest_json_sha256":manifest_sha,
  "manifest_async":True,"manifest_draft":True,
  "max_files_in_any_output_directory":max(sizes.values()),
  "max_files_in_root_output":sizes["(root)"],
  "output_directory_count":len(sizes),"largest_directories":dirworst,
  "root_html_removed":sources_with_different_paths,
  "files_over_10MB":sum(n>10000000 for n in maxima),
  "largest_source_file_bytes":max(maxima),
  "Netlify_published_per_directory_limit":54000,
  "dir_limit_pass_offline":max(sizes.values())<54000,
  "caveats":[
   "This is a structural OFFLINE simulation, not an actual Netlify preview or production deploy.",
   "Netlify may impose additional request payload, API rate, and processing limits. No guarantee of acceptance.",
   "Draft upload of all files and Edge rewrite runtime verification require separate user authorization.",
   "Payload includes no Edge Function artifact because Netlify deployment integration must be validated separately.",
   "Netlify file content is not contained in JSON; future PUT uploads would need the immutable source archive."
  ]}
 if (len(files)!=180798 or root_html!=158571 or total_bytes!=6814005542 or
     len(set(files.values()))!=180794 or max(sizes.values())>=54000):
  report["status"]="HOLD_OFFLINE_INTEGRITY_MISMATCH"
 (out/"ASYNC_DRAFT_UPLOAD_METHOD_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("OFFLINE_NETLIFY_ASYNC_DRAFT_MANIFEST_QA",json.dumps(report,ensure_ascii=False),flush=True)
 return 0 if report["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
