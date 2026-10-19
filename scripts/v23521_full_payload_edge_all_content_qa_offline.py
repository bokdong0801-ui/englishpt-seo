#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify ALL 180800 actual full payload candidate members, 158571 original contents,
canonical robots counts, 44 sitemaps, Netlify Forms blueprint and 29 OG PNG.
No network and no user-facing deploy changes.
"""
import argparse,collections,gzip,hashlib,json,pathlib,re,subprocess,tarfile,xml.etree.ElementTree as ET
from urllib.parse import urlsplit,unquote
ROBOTS=re.compile(rb'<meta\s+name="robots"\s+content="([^"]+)"',re.I)
OG=set("beginner toeic ielts toefl opic tos duolingo elementary middle high student worker college jobseeker housewife stations region academy tutor conversation exam courses englishpt reading writing international phone video general".split())
TUTORS=("gyeongnam-milyang-naeidong-elem-tutor.html","gyeongnam-milyang-naeidong-mid-tutor.html","gyeongnam-milyang-naeidong-high-tutor.html",
"seoul-jongno-sajikdong-elem-tutor.html","seoul-jongno-sajikdong-mid-tutor.html","seoul-jongno-sajikdong-high-tutor.html")
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--manifest",required=True)
 p.add_argument("--report",required=True);p.add_argument("--support-dir",required=True);a=p.parse_args()
 with gzip.open(a.manifest,"rt",encoding="utf8") as f:m=json.load(f)
 paths=m["target_SHA1_by_path"];routing=m["original_public_html_to_data_payload"]
 assert m["source_SHA256"]=="e27ffd3e94687e0f2fc58c3951ee1262bca8fd22bd684cf7b4bdb62d014326b1"
 assert len(routing)==158571 and len(paths)==180800
 out=pathlib.Path(a.support_dir);out.mkdir(parents=True,exist_ok=True)
 report={"status":"RUNNING","QA_is_offline":True,"production_published":False,
   "uploaded_to_Netlify":False,"site_files_sha1_verified":0,"payload_original_html_count":0,
   "static_html_count":0,"indexable":0,"noindex":0,"route_canonical_errors":[],
   "form_samples":[],"OG_29":[],"png_total":0,"site_map_urls":0}
 files=set();indexed=set();noindexed=set();xmls={};static_form=False;static_form_fragment=b"";headers_checked=False;edge_checked=False
 h=hashlib.sha256()
 with open(a.source,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 report["archive_sha256"]=h.hexdigest()
 z=subprocess.Popen(["zstd","-dc",a.source],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 try:
  with tarfile.open(fileobj=z.stdout,mode="r|") as tar:
   for member in tar:
    if member.isdir():continue
    path=member.name.removeprefix("./")
    if path in files or path not in paths:raise ValueError("Bad target or unknown member "+path)
    files.add(path)
    b=tar.extractfile(member).read()
    if hashlib.sha1(b).hexdigest()!=paths[path]:
     raise ValueError("Source SHA1 content not preserved "+path)
    report["site_files_sha1_verified"]+=1
    if path.endswith(".page"):
     report["payload_original_html_count"]+=1
     basename=path.rsplit("/",1)[-1].removesuffix(".page")+".html"
     if routing.get(basename,{}).get("to")!=path or routing[basename]["sha1"]!=paths[path]:
      raise ValueError("Invalid route-to-source parity "+path)
     canonical=b"https://englishpt.kr/"+basename.encode("utf8")
     if canonical not in b:raise ValueError("Canonical changed "+path)
     mrobots=ROBOTS.search(b)
     if not mrobots:raise ValueError("Missing source robots "+path)
     if b"noindex" in mrobots.group(1).lower():noindexed.add(basename)
     else:indexed.add(basename)
     if (b"noindex" in mrobots.group(1).lower())!=routing[basename]["noindex"]:
      raise ValueError("Noindex metadata parity missing")
     if basename in TUTORS:
      for tag in (b'name="englishpt-consultation"',b'data-netlify="true"',b'name="form-name"',b'name="requestType"',b'name="subject"'):
       if tag not in b:raise ValueError("Consultation form source lost "+basename+" "+str(tag))
      report["form_samples"].append(basename)
    if path.endswith(".html"):report["static_html_count"]+=1
    if path=="__internal/consultation-blueprint.html":
     static_form=True;static_form_fragment=b
     assert b'name="englishpt-consultation"' in b and b'name="form-name"' in b
     assert b'<meta name="robots" content="noindex,nofollow">' in b
    if path=="_headers":
     if b"\n/*\n  X-Robots-Tag: noindex" in b:
      raise ValueError("Global Draft noindex accidentally carried to full candidate")
     if b"/__pages/*\n  X-Robots-Tag: noindex" not in b:
      raise ValueError("Raw .page source noindex header missing")
     headers_checked=True
    if path=="netlify/edge-functions/shard-router.js":
     if b'headers.delete("X-Robots-Tag");' not in b:raise ValueError("Public indexable robots header not cleaned")
     edge_checked=True
     (out/"shard-router.mjs").write_bytes(b)
    if path=="_redirects":(out/"_redirects").write_bytes(b)
    if path=="netlify.toml":
     import tomllib
     cfg=tomllib.loads(b.decode("utf8"))
     if len(cfg.get("edge_functions",[]))!=1:raise ValueError("Edge TOML missing")
    if path=="pilot.js":
     assert hashlib.sha256(b).hexdigest()=="d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede"
    if path=="sitemap-index.xml" or path.startswith("sitemaps/") and path.endswith(".xml"):xmls[path]=b
    if path.endswith(".png"):
     report["png_total"]+=1
     if path.startswith("assets/images/og-pages/"):
      stem=path.rsplit("/",1)[-1].removesuffix(".png")
      if stem in OG:
       import struct
       if b[:8]!=bytes.fromhex("89504e470d0a1a0a") or struct.unpack(">II",b[16:24])!=(1200,630):
        raise ValueError("Broken OG editorial "+path)
       report["OG_29"].append(stem)
    if report["site_files_sha1_verified"]%30000==0:
     print("FULL_PAYLOAD_SEO_QA_PROGRESS",report["site_files_sha1_verified"],len(indexed),len(noindexed),flush=True)
  if z.wait(timeout=90)!=0:raise ValueError("ZSTD full QA failed")
 finally:z.stdout.close()
 if files!=set(paths):raise ValueError("Not all output files in archive")
 if len(indexed)!=21964 or len(noindexed)!=136607 or len(indexed|noindexed)!=158571:
  raise ValueError("Generated SEO indexing distribution incorrect "+str((len(indexed),len(noindexed))))
 if len(xmls)!=45:raise ValueError("Expected 44 shards plus sitemap-index")
 found=set();indexlist=[]
 for name,xml in xmls.items():
  root=ET.fromstring(xml)
  locs=[c.text.strip() for item in root for c in item if c.tag.endswith("loc") and c.text]
  if name=="sitemap-index.xml":indexlist=locs
  else:
   for url in locs:
    parsed=urlsplit(url)
    if parsed.netloc!="englishpt.kr" or parsed.scheme!="https":raise ValueError("Incorrect sitemap public host")
    path=unquote(parsed.path).lstrip("/")
    if path in found:raise ValueError("Duplicate sitemap canonical")
    found.add(path)
 if len(indexlist)!=44 or found!=indexed:
  raise ValueError("Original 21964 intended-index sitemap URL set changed")
 if not static_form or not headers_checked or not edge_checked:raise ValueError("Missing Netlify Forms/static headers/edge")
 if len(report["form_samples"])!=6 or set(report["OG_29"])!=OG:raise ValueError("Original Form or editorial OG coverage changed")
 if report["site_files_sha1_verified"]!=180800 or report["static_html_count"]!=4:
  raise ValueError("Netlify HTML scan reduction not achieved")
 if report["png_total"]!=22088:raise ValueError("Missing original PNG image")
 report.update({"status":"PASS_FULL_158571_PAYLOAD_SEO_URL_PARITY_AND_FOUR_HTML_NETLIFY",
  "indexable":len(indexed),"noindex":len(noindexed),"site_map_urls":len(found),"sitemaps":len(xmls),
  "real_Netlify_form_blueprint":True,"public_edge_removes_raw_asset_noindex":True,
  "HTML_sending_visitors_unchanged":True})
 rp=pathlib.Path(a.report);rp.parent.mkdir(parents=True,exist_ok=True)
 rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("PASS_FULL_180800_SHA1_AND_158571_SEO_WITH_FOUR_STATIC_HTML",json.dumps({k:v for k,v in report.items() if k not in ("form_samples","OG_29","route_canonical_errors")},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
