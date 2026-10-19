#!/usr/bin/env python3
"""Prepare a small REAL static+Edge Draft diagnostic package from the frozen FULL sharded archive.
NO Netlify calls, NO deployments, NO change to full candidate or Production.
100 page samples + 6 tutors + index + real Edge code. All pages are ORIGINAL bytes.
Draft-only global X-Robots-Tag noindex is added to diagnostic _headers.
This small pilot intentionally omits the full sitemap and 36.8 MB JSON.
"""
import argparse,collections,datetime,gzip,hashlib,io,json,pathlib,subprocess,tarfile,sys
EXPECT="e27ffd3e94687e0f2fc58c3951ee1262bca8fd22bd684cf7b4bdb62d014326b1"
TUTORS=tuple(a+"-"+g+"-tutor.html" for a in ("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong") for g in ("elem","mid","high"))
OG_STEMS=("beginner toeic ielts toefl opic tos duolingo elementary middle high "
"student worker college jobseeker housewife stations region academy tutor "
"conversation exam courses englishpt reading writing international phone video general").split()
def sha256_file(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for x in iter(lambda:f.read(1048576),b""):h.update(x)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--input",required=True);p.add_argument("--source-map",required=True)
 p.add_argument("--output",required=True);p.add_argument("--report",required=True)
 a=p.parse_args()
 if sha256_file(a.input)!=EXPECT:raise ValueError("Wrong source SHA")
 with gzip.open(a.source_map,"rt",encoding="utf8") as f:manifest=json.load(f)
 assert manifest["source_sha256"]=="e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba"
 original_to_new=manifest["original_to_new"];hashes=manifest["full_output_sha1"]
 html=sorted(p for p,d in original_to_new.items() if p.endswith(".html") and d["to"].startswith("__pages/"))
 assert len(html)==158571
 sampled={html[len(html)*i//96] for i in range(96)}
 sampled.update(TUTORS);sampled.add("englishpt.html")
 sharded={original_to_new[x]["to"] for x in sampled}
 files={}
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 fout=open(out,"wb")
 zipproc=subprocess.Popen(["zstd","-T2","-4","-q","-c"],stdin=subprocess.PIPE,stdout=fout)
 decom=subprocess.Popen(["zstd","-dc",a.input],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 retained=[];omitted=collections.Counter();sha_verified=0;selected_imgs=0
 try:
  with tarfile.open(fileobj=decom.stdout,mode="r|") as inp:
   with tarfile.open(fileobj=zipproc.stdin,mode="w|") as tar:
    for member in inp:
     if not member.isfile():continue
     name=member.name.removeprefix("./")
     chosen=False
     if name in sharded:chosen=True
     elif name in ("index.html","404.html","_headers","_redirects","robots.txt","netlify.toml",
        "netlify/edge-functions/shard-router.js","pilot.js"):chosen=True
     elif name.startswith("assets/") and not name.endswith(".png") and not name.endswith(".json"):chosen=True
     elif name.startswith("assets/images/og-pages/") and name.endswith(".png"):
      stem=name.rsplit("/",1)[-1].removesuffix(".png")
      if stem in OG_STEMS or stem+".html" in sampled:chosen=True
     elif name.startswith("assets/images/") and name.endswith(".png"):
      # Preserve common editorials and site graphics from assets images.
      if name.count("/")<=3:chosen=True
     if not chosen:
      omitted["excluded_files"]+=1;continue
     blob=inp.extractfile(member).read()
     if hashlib.sha1(blob).hexdigest()!=hashes[name]:
      raise ValueError("Source HTML/asset integrity changed: "+name)
     sha_verified+=1
     if name=="_headers":
      if b"X-Robots-Tag: noindex" in blob:raise ValueError("Source already globally noindex")
      blob += b"\n/*\n  X-Robots-Tag: noindex\n"
     elif name=="robots.txt":
      blob=b"User-agent: *\nDisallow: /\n"
     header=tarfile.TarInfo(name)
     header.mode=0o644;header.size=len(blob);header.mtime=0
     tar.addfile(header,io.BytesIO(blob))
     retained.append(name)
     files[name]=hashlib.sha256(blob).hexdigest()
     if name.endswith(".png"):selected_imgs+=1
  if decom.wait(timeout=60)!=0:raise ValueError("Unzip reader failure")
  if zipproc.stdin.closed is False:zipproc.stdin.close()
  if zipproc.wait(timeout=60)!=0:raise ValueError("Output compression failed")
 finally:
  try:decom.stdout.close()
  except:pass
  try:zipproc.stdin.close()
  except:pass
  fout.close()
 for pth in sharded:
  if pth not in files:raise ValueError("Pilot HTML not found: "+pth)
 if "netlify/edge-functions/shard-router.js" not in files:raise ValueError("Pilot Edge code missing")
 if "_headers" not in files:raise ValueError("Pilot draft noindex missing")
 assert len(files)==len(set(files))
 report={"status":"PASS_SMALL_DIAGNOSTIC_DRAFT_CANDIDATE_BUILT_OFFLINE",
   "full_candidate_original_sha256":EXPECT,
   "pilot_sha256":sha256_file(out),"pilot_archive_bytes":out.stat().st_size,
   "included_files":len(files),"source_sha1_verified_files":sha_verified,
   "retained_html_count":sum(x.endswith(".html") for x in files),
   "kept_original_root_page_samples":len(sampled),
   "six_student_tutors_present":all(original_to_new[x]["to"] in files for x in TUTORS),
   "edge_bundle":"netlify/edge-functions/shard-router.js",
   "pilot_global_header_noindex":True,"pilot_robots_disallow_all":True,
   "kept_png_count":selected_imgs,"kept_original_public_paths":sorted(sampled)[:15],
   "not_full_site":True,"not_for_Production":True,
   "Netlify_Draft_created":False,"Production_modified":False,"real_Form_posted":False,
   "note":"Deliberately omits most 158k pages, 44 XML sitemaps and 36MB thumbnail manifest; diagnostic only."}
 rp=pathlib.Path(a.report);rp.parent.mkdir(parents=True,exist_ok=True)
 rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("PASS_SMALL_SHARDED_NETLIFY_DRAFT_PILOT_OFFLINE",json.dumps(report,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
