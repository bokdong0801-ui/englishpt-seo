#!/usr/bin/env python3
"""Make REAL 1000 and 5000 legacy URL Review Draft samples from fully verified
180800 file full payload release. Exact HTML source bytes, no Production, no Netlify APIs.
Global noindex and robots disallow, no full sitemap (sampled site only).
"""
import argparse,collections,gzip,hashlib,io,json,pathlib,subprocess,tarfile
FULLSHA="0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8"
TUTORS=set(a+"-"+g+"-tutor.html" for a in ("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong") for g in ("elem","mid","high"))
EDITORIAL=set("beginner toeic ielts toefl opic tos duolingo elementary middle high student worker college jobseeker housewife stations region academy tutor conversation exam courses englishpt reading writing international phone video general".split())
def sha256(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(1048576),b""):h.update(c)
 return h.hexdigest()
def evenly(items,count):
 if count<=0:return set()
 if count>=len(items):return set(items)
 return {items[(i*len(items))//count] for i in range(count)}
def samples(mapping,target,prior=None):
 orig=list(mapping);idx=sorted(x for x in orig if not mapping[x]["noindex"]);no=sorted(x for x in orig if mapping[x]["noindex"])
 keep=set(TUTORS)|{"englishpt.html"}|(prior or set())
 if len(keep)>target:raise ValueError("Prior stage larger than target")
 idxgoal=round(target*(len(idx)/len(orig)))
 # Keep samples from both page families so scaling doesn't bias the benchmark.
 keep|=evenly(idx,max(0,idxgoal-sum(n in idx for n in keep)))
 noleft=max(0,target-len(keep))
 keep|=evenly([x for x in no if x not in keep],noleft)
 if len(keep)!=target:
  for x in idx+no:
   if len(keep)==target:break
   keep.add(x)
 assert len(keep)==target,(len(keep),target)
 return keep
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source",required=True);p.add_argument("--source-map",required=True);p.add_argument("--output-dir",required=True)
 a=p.parse_args()
 if sha256(a.source)!=FULLSHA:raise ValueError("Wrong full 158571 candidate")
 with gzip.open(a.source_map,"rt",encoding="utf8") as f:m=json.load(f)
 routes=m["original_public_html_to_data_payload"];digest=m["target_SHA1_by_path"]
 assert len(routes)==158571 and len(digest)==180800
 s1=samples(routes,1000)
 s5=samples(routes,5000,prior=s1)
 out=pathlib.Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
 subsets={1000:s1,5000:s5}
 lookups={n:{info["to"] for slug,info in routes.items() if slug in members} for n,members in subsets.items()}
 imglookups={n:{slug.removesuffix(".html") for slug in members} for n,members in subsets.items()}
 paths={}
 procs={}
 for n in subsets:
  file=out/f"ENGLISHPT_PAYLOAD_EDGE_{n}_PAGES_DRAFT_SAMPLE_NOINDEX_NOT_DEPLOYED.tar.zst"
  fout=open(file,"wb")
  zstd=subprocess.Popen(["zstd","-T2","-4","-q","-c"],stdin=subprocess.PIPE,stdout=fout)
  outtar=tarfile.open(fileobj=zstd.stdin,mode="w|")
  procs[n]=(file,fout,zstd,outtar)
  paths[n]=collections.Counter()
 old=subprocess.Popen(["zstd","-dc",a.source],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 try:
  with tarfile.open(fileobj=old.stdout,mode="r|") as src:
   for item in src:
    if not item.isfile():continue
    path=item.name.removeprefix("./")
    chosen={}
    for n in subsets:
     match=False
     if path in lookups[n]:match=True
     elif path in ("index.html","404.html","_headers","_redirects","robots.txt","pilot.js","netlify.toml",
      "netlify/edge-functions/shard-router.js","__internal/consultation-blueprint.html","privacy/index.html"):match=True
     elif path.startswith("assets/") and not path.endswith(".png") and not path.endswith(".json"):match=True
     elif path.startswith("assets/images/og-pages/") and path.endswith(".png"):
      stem=path.rsplit("/",1)[-1].removesuffix(".png")
      if stem in EDITORIAL or stem in imglookups[n]:match=True
     elif path.startswith("assets/images/") and path.endswith(".png") and path.count("/")<=3:match=True
     chosen[n]=match
    if not any(chosen.values()):continue
    original=src.extractfile(item).read()
    if hashlib.sha1(original).hexdigest()!=digest[path]:
     raise ValueError("Full source file hash mismatch "+path)
    for n,selected in chosen.items():
     if not selected:continue
     body=original
     if path=="_headers":
      body += b"\n/*\n  X-Robots-Tag: noindex, nofollow\n"
     elif path=="robots.txt":
      body=b"User-agent: *\nDisallow: /\n"
     elif path=="netlify/edge-functions/shard-router.js":
      before=b'headers.delete("X-Robots-Tag");'
      if before not in body:raise ValueError("Expected public original Edge mode missing")
      body=body.replace(before,b'headers.set("X-Robots-Tag", "noindex, nofollow");')
     h=tarfile.TarInfo(path);h.size=len(body);h.mtime=0;h.mode=0o644
     procs[n][3].addfile(h,io.BytesIO(body))
     paths[n]["files"]+=1;paths[n]["bytes"]+=len(body)
     if path.endswith(".page"):paths[n]["payload_pages"]+=1
     if path.endswith(".html"):paths[n]["static_html"]+=1
     if path.endswith(".png"):paths[n]["png"]+=1
   if old.wait(timeout=120)!=0:raise RuntimeError("Full source decompression failed")
 finally:
  old.stdout.close()
  for n,(file,fout,zstd,t) in procs.items():
   t.close()
   zstd.stdin.close()
   if zstd.wait(timeout=90)!=0:raise ValueError("zstd stage failed "+str(n))
   fout.close()
 reports={}
 for n in subsets:
  file=procs[n][0]
  if paths[n]["payload_pages"]!=n or paths[n]["static_html"]!=4:raise ValueError("Broken static HTML subset count "+str((n,paths[n])))
  reports[str(n)]={"status":"PASS_OFFLINE_SCALED_PAYLOAD_REVIEW_SAMPLE",
   "full_original_sha256":FULLSHA,
   "sample_sha256":sha256(file),"sample_tar_bytes":file.stat().st_size,
   "sampled_full_public_urls":n,"indexable_original_pages_sampled":sum(not routes[x]["noindex"] for x in subsets[n]),
   "original_noindex_pages_sampled":sum(routes[x]["noindex"] for x in subsets[n]),
   "Netlify_static_HTML":paths[n]["static_html"],"Netlify_payload_files":paths[n]["payload_pages"],
   "total_regular_files":paths[n]["files"],"included_PNG":paths[n]["png"],
   "payload_from_exact_full_source_SHA1_verified":True,
   "globally_noindex_as_Draft_only":True,
   "full_sitemap_deliberately_not_included":True,"Draft_deployed":False,
   "production_published":False}
 result={"status":"PASS_1000_AND_5000_REAL_PAYLOAD_STAGE_SAMPLE_CREATED","source_full_sha256":FULLSHA,
   "reports":reports}
 (out/"SCALING_STAGE_1000_5000_QA.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("PASS_1000_5000_STAGE_PAYLOAD_SITE_SAMPLE_BUILD",json.dumps(result,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
