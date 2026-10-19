#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full 180,799-file SHA1 parity, SEO, sitemaps, OG and six Forms of real new .tar.zst.
Never a Netlify operation; all candidate content from the built archive.
"""
import argparse,collections,gzip,hashlib,json,pathlib,re,subprocess,sys,tarfile,xml.etree.ElementTree as ET
from urllib.parse import urlsplit,unquote
ROBOTS=re.compile(rb'<meta\s+name="robots"\s+content="([^"]+)"',re.I)
CANONICAL=re.compile(rb'<link\s+rel="canonical"\s+href="([^"]+)"',re.I)
OG_PNGS=set(("beginner toeic ielts toefl opic tos duolingo elementary middle high "
 "student worker college jobseeker housewife stations region academy tutor "
 "conversation exam courses englishpt reading writing international phone video general").split())
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--archive",required=True);p.add_argument("--manifest",required=True)
 p.add_argument("--report",required=True);p.add_argument("--extract-support",required=True)
 a=p.parse_args()
 with gzip.open(a.manifest,"rt",encoding="utf8") as f:manifest=json.load(f)
 expected=manifest["full_output_sha1"];old_to_new=manifest["original_to_new"]
 r={"status":"RUNNING","production_deployed":False,"review_draft_deployed":False,"errors":[],
    "files_verified":0,"html_verified":0,"generated_pages_verified":0,"indexable":0,"noindex":0,
    "sitemap_count":0,"sitemap_unique_urls":0,"legacy_html_missing":0,
    "form_samples":[],"static_og_29":[],"new_candidate_sha256":None,"netlify_site_contacted":False}
 ah=hashlib.sha256()
 with open(a.archive,"rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):ah.update(chunk)
 r["new_candidate_sha256"]=ah.hexdigest()
 files=set();sitemaps={};candidates=set();indexable=set();noindex=set();htmls={}
 out=pathlib.Path(a.extract_support);out.mkdir(parents=True,exist_ok=True)
 proc=subprocess.Popen(["zstd","-dc",a.archive],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 try:
  with tarfile.open(fileobj=proc.stdout,mode="r|") as t:
   for member in t:
    if member.isdir():continue
    name=member.name.removeprefix("./")
    if not member.isfile():raise ValueError("Non-regular output archive entry")
    if name in files:raise ValueError("Duplicate output path")
    files.add(name)
    payload=t.extractfile(member).read()
    sha=hashlib.sha1(payload).hexdigest()
    if expected.get(name)!=sha:raise ValueError("Output SHA1 does not match source: "+name)
    r["files_verified"]+=1
    if name.endswith(".html"):
      r["html_verified"]+=1
      if name.startswith("__pages/"):
        basename=name.rsplit("/",1)[-1]
        if name.count("/")!=2 or old_to_new.get(basename,{}).get("to")!=name:
          raise ValueError("Broken original public URL shard map: "+name)
        candidates.add(basename)
        expected_canonical=b"https://englishpt.kr/"+basename.encode("utf8")
        if expected_canonical not in payload:
          raise ValueError("Expected canonical URL absent from preserved HTML: "+basename)
        robots=ROBOTS.search(payload)
        if robots is None:raise ValueError("Missing robots on generated page: "+basename)
        if b"noindex" in robots.group(1).lower():noindex.add(basename)
        else:indexable.add(basename)
        if basename in (
          "gyeongnam-milyang-naeidong-elem-tutor.html",
          "gyeongnam-milyang-naeidong-mid-tutor.html",
          "gyeongnam-milyang-naeidong-high-tutor.html",
          "seoul-jongno-sajikdong-elem-tutor.html",
          "seoul-jongno-sajikdong-mid-tutor.html",
          "seoul-jongno-sajikdong-high-tutor.html"):
          h=payload.decode("utf8",errors="replace")
          if ('name="englishpt-consultation"' not in h or 'data-netlify="true"' not in h or
              'name="form-name"' not in h or 'name="requestType"' not in h or 'name="subject"' not in h):
            raise ValueError("Missing static consultation form contract "+basename)
          r["form_samples"].append(basename)
    if name=="pilot.js":
      if hashlib.sha256(payload).hexdigest()!="d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede":
        raise ValueError("Wrong final pilot.js SHA")
    if name=="_headers" and b"X-Robots-Tag: noindex" in payload:
      raise ValueError("Global Review noindex leaked into Production candidate")
    if name=="netlify.toml":
      import tomllib
      parsed=tomllib.loads(payload.decode("utf8"))
      edges=parsed.get("edge_functions",[])
      if len(edges)!=1 or edges[0].get("function")!="shard-router" or edges[0].get("pattern")!="^/[^/]+[.]html$":
        raise ValueError("Invalid Netlify Edge declaration in real sharded site")
    if name=="netlify/edge-functions/shard-router.js":
      (out/"shard-router.mjs").write_bytes(payload)
    if name=="_redirects":
      (out/"_redirects").write_bytes(payload)
    if name=="netlify.toml":
      (out/"netlify.toml").write_bytes(payload)
    if name=="sitemap-index.xml" or name.startswith("sitemaps/") and name.endswith(".xml"):
      sitemaps[name]=payload
    if name.startswith("assets/images/og-pages/") and name.endswith(".png"):
      r["og_directory_files"]=r.get("og_directory_files",0)+1
    if name.startswith("assets/images/og/") and name.endswith(".png"):
      r["og_assets_files"]=r.get("og_assets_files",0)+1
    if r["files_verified"]%30000==0:print("SHARDED_FULL_QA_PROGRESS",r["files_verified"],len(indexable),len(noindex),flush=True)
  if proc.wait(timeout=90)!=0:raise ValueError("Output ZSTD decode failure")
 finally:
  proc.stdout.close()
 if files!=set(expected):raise ValueError("Manifest-vs-output file set mismatch")
 r.update({"sitemap_count":len(sitemaps),"generated_pages_verified":len(candidates),
     "indexable":len(indexable),"noindex":len(noindex),
     "form_sample_count":len(r["form_samples"]),"all_files_sha1_match_source":True,
     "config_edge_exists":"netlify/edge-functions/shard-router.js" in files})
 if len(sitemaps)!=45:raise ValueError("Expected index+44 XML sitemaps")
 locs=set();idx=[]
 for name,b in sitemaps.items():
  xml=ET.fromstring(b)
  typ=xml.tag.split("}")[-1]
  if typ not in ("urlset","sitemapindex"):raise ValueError("Invalid XML sitemap tag "+name)
  this=[]
  for item in list(xml):
    for child in item:
      if child.tag.split("}")[-1]=="loc" and child.text:this.append(child.text.strip())
  if typ=="sitemapindex":idx=this
  else:
    for url in this:
      p=urlsplit(url)
      if p.scheme!="https" or p.netloc!="englishpt.kr":raise ValueError("Wrong sitemap hostname")
      n=unquote(p.path).lstrip("/")
      if n in locs:raise ValueError("Duplicate sitemap URL")
      locs.add(n)
 if len(idx)!=44:raise ValueError("Not exactly 44 sitemap index entries")
 if locs!=indexable:raise ValueError("Sitemap original public URL list does not equal generated indexable set")
 if len(candidates)!=158571 or len(indexable)!=21964 or len(noindex)!=136607:
  raise ValueError("SEO totals wrong: "+str((len(candidates),len(indexable),len(noindex))))
 if len(r["form_samples"])!=6 or r["files_verified"]!=180799 or r["html_verified"]!=158574:
  raise ValueError("Full target inventory/forms unexpected")
 if r.get("og_directory_files")!=21990:raise ValueError("OG generated PNG inventory mismatch")
 if "netlify/edge-functions/shard-router.js" not in files:raise ValueError("Edge handler missing")
 r["sitemap_unique_urls"]=len(locs)
 # Separate JS test uses extracted actual Edge bundle and original redirect routes.
 # Never run Netlify CLI during this QA job.
 r["status"]="PASS_FULL_ACTUAL_SHARDED_180799_FILES_SHA1_AND_158571_SEO_PAGES"
 report=pathlib.Path(a.report);report.parent.mkdir(parents=True,exist_ok=True)
 report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("PASS_ACTUAL_SHARDED_FULL_SEO_SITEMAP_FORMS_QA",json.dumps(r,ensure_ascii=False),flush=True)
 return 0
if __name__=="__main__":sys.exit(main())
