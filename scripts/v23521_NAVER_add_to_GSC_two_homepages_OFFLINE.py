#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OFFLINE surgical Naver HTML site verification meta preserving existing Google verification for englishpt.kr.
Changes EXACTLY TWO HOME HTML CONTENTS: /index.html (static redirecting entrypoint)
and /englishpt.html (served via /__pages/xx/englishpt.page Edge payload).
All remaining 180,798 files byte-for-byte preserved; never deploy, no Netlify POST.
"""
import argparse,collections,copy,datetime,gzip,hashlib,io,json,pathlib,re,subprocess,tarfile,sys
OLD_SHA="3ee78c417da2a91bc6f86d2cfd0c4be6c196334a0eaa89a222d99e83365a2acb"
CODE="340f4e7dc8c5f3ec806e68f6f09b9949f941a0de"
GOOGLE_TAG=b'<meta name="google-site-verification" content="OTG-5ooTZYTm-HnTOi8I0TRV4bZHUD-uSYSOih3E8ig" />'
TAG=('<meta name="naver-site-verification" content="'+CODE+'" />').encode("utf8")
def digest(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()
def insert(name,body):
 if TAG in body:raise ValueError("Tag already exists in immutable input "+name)
 if b'naver-site-verification' in body.lower():raise ValueError("Other existing Naver verification tag; needs manual inspection")
 if body.count(GOOGLE_TAG)!=1:raise ValueError("Existing Google verification tag not exactly once "+name)
 if len(re.findall(rb'(?i)</head\s*>',body))!=1 or len(re.findall(rb'(?i)<head(?:\s|>)',body))!=1:
  raise ValueError("Invalid homepage <head> delimiter "+name)
 new=re.sub(rb'(?i)</head\s*>',b'\n'+TAG+b'\n</head>',body,count=1)
 if new.count(TAG)!=1:raise ValueError("Tag insertion failed "+name)
 if new.count(GOOGLE_TAG)!=1:raise ValueError("Existing Google tag changed "+name)
 if b'<link rel="canonical" href="https://englishpt.kr/englishpt.html"' not in body:
  raise ValueError("Home canonical unexpectedly different "+name)
 if new==body:raise ValueError("Content patch unexpectedly no-op")
 return new
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source",required=True)
 p.add_argument("--original-manifest",required=True)
 p.add_argument("--out",required=True)
 p.add_argument("--patched-map",required=True)
 p.add_argument("--report",required=True)
 a=p.parse_args()
 if digest(a.source)!=OLD_SHA:raise ValueError("Original immutable live-source archive SHA256 changed")
 with gzip.open(a.original_manifest,"rt",encoding="utf8") as f:mp=json.load(f)
 paths=mp["target_SHA1_by_path"]
 routes=mp["original_public_html_to_data_payload"]
 if len(paths)!=180800 or len(routes)!=158571:raise ValueError("Frozen source inventory mismatch")
 actual="englishpt.html"
 if actual not in routes:raise ValueError("Canonical home public .html missing from route map")
 edge_path=routes[actual]["to"]
 if not edge_path.startswith("__pages/") or not edge_path.endswith("/englishpt.page"):
  raise ValueError("Unexpected canonical homepage data path "+edge_path)
 targets={"index.html",edge_path}
 # Small set of exact modified paths; rest of original file contents remain unchanged.
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 patched_map=copy.deepcopy(mp)
 newhash=patched_map["target_SHA1_by_path"]
 stat=collections.Counter();changed={}
 source=subprocess.Popen(["zstd","-dc",a.source],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 fout=open(out,"wb")
 comp=subprocess.Popen(["zstd","-T2","-5","-q","-c"],stdin=subprocess.PIPE,stdout=fout)
 ok=False
 try:
  with tarfile.open(fileobj=source.stdout,mode="r|") as origin:
   with tarfile.open(fileobj=comp.stdin,mode="w|") as result:
    for m in origin:
     if not m.isfile():raise ValueError("Unexpected nonfile member")
     name=m.name.removeprefix("./")
     if name not in paths:raise ValueError("Member not in manifest "+name)
     data=origin.extractfile(m).read()
     original=hashlib.sha1(data).hexdigest()
     if original!=paths[name]:raise ValueError("Old source changed "+name)
     new=insert(name,data) if name in targets else data
     if name in targets:
      changed[name]={"source_sha1":original,"new_sha1":hashlib.sha1(new).hexdigest(),
                     "source_bytes":len(data),"new_bytes":len(new)}
      newhash[name]=changed[name]["new_sha1"]
      if name==edge_path:patched_map["original_public_html_to_data_payload"][actual]["sha1"]=newhash[name]
     header=tarfile.TarInfo(name);header.mode=m.mode;header.mtime=m.mtime
     header.size=len(new);header.uid=0;header.gid=0
     result.addfile(header,io.BytesIO(new))
     stat["files"]+=1
     stat["static_html"]+=int(name.endswith(".html"))
     stat["pages"]+=int(name.endswith(".page"))
     if stat["files"]%30000==0:
      print("NAVER_META_ONLY_PATCH_PROGRESS",stat["files"],flush=True)
  if source.wait(timeout=120)!=0:raise ValueError("Input ZSTD stream failed")
  comp.stdin.close()
  if comp.wait(timeout=120)!=0:raise ValueError("Output ZSTD compression failed")
  ok=True
 finally:
  try:source.stdout.close()
  except:pass
  try:comp.stdin.close()
  except:pass
  fout.close()
 if not ok:raise ValueError("Output compressor incomplete")
 if set(changed)!=targets or stat["files"]!=180800 or stat["static_html"]!=4 or stat["pages"]!=158571:
  raise ValueError("Exact 2-file content patch count failed "+str((changed,stat)))
 with gzip.open(a.patched_map,"wt",encoding="utf8",compresslevel=6) as f:
  json.dump(patched_map,f,separators=(",",":"),ensure_ascii=False)
 newcandidate=digest(out)
 report={"status":"PASS_SURGICAL_NAVER_TAG_PRESERVE_GOOGLE_ONLY_TWO_HOME_REAL_ARCHIVE",
   "created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
   "original_live_candidate_sha256":OLD_SHA,"new_candidate_sha256":newcandidate,
   "new_candidate_bytes":out.stat().st_size,
   "output_regular_files":stat["files"],"static_html":stat["static_html"],
   "preserved_158571_page_routes":stat["pages"],
   "modified_exactly_two_files":sorted(changed),
   "unchanged_files_verified_sha1":stat["files"]-len(changed),
   "google_tag_retained":GOOGLE_TAG.decode("utf8"),
   "naver_tag_added":TAG.decode("utf8"),
   "main_home_page_public_path":"https://englishpt.kr/englishpt.html",
   "index_redirect_page":"https://englishpt.kr/",
   "original_forms_seo_sitemaps_and_Edge_unchanged":True,
   "netlify_deploy_created":False,"production_modified":False,"search_console_verified":False}
 dest=pathlib.Path(a.report);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("PASS_ACTUAL_NAVER_TAG_SITE_CANDIDATE_BUILT",json.dumps(report,ensure_ascii=False),flush=True)
if __name__=="__main__":sys.exit(main())
