#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline: repackage ALL 158571 original SEO .html as byte-identical .page assets;
Edge responds to legacy public .html with text/html. Preserve 21964 indexable and
136607 noindex content, Forms via one static HTML blueprint, sitemaps unchanged.
No credentials, Netlify upload, POST, Production changes or indexing actions.
"""
import argparse,collections,datetime,gzip,hashlib,io,json,pathlib,re,subprocess,tarfile,sys
from v23521_small_payload_edge_real_candidate_OFFLINE import EDGE
SOURCE_SHA="e27ffd3e94687e0f2fc58c3951ee1262bca8fd22bd684cf7b4bdb62d014326b1"
TUTOR_NAME="gyeongnam-milyang-naeidong-elem-tutor.html"
FORM_PATTERN=re.compile(rb'<form\b[^>]*\bname="englishpt-consultation"[^>]*>.*?</form\s*>',re.I|re.S)
ROBOTS_PATTERN=re.compile(rb'<meta\s+name="robots"\s+content="([^"]+)"',re.I)
def file_sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def main():
 cli=argparse.ArgumentParser()
 cli.add_argument("--source",required=True);cli.add_argument("--source-map",required=True)
 cli.add_argument("--output",required=True);cli.add_argument("--map-output",required=True);cli.add_argument("--report",required=True)
 a=cli.parse_args()
 if file_sha(a.source)!=SOURCE_SHA:raise ValueError("The original full sharded source archive changed")
 with gzip.open(a.source_map,"rt",encoding="utf8") as z:m=json.load(z)
 oldsha=m["full_output_sha1"];oldmapping=m["original_to_new"]
 assert len(oldsha)==180799 and len(oldmapping)>=180797,(len(oldsha),len(oldmapping))
 out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 created=collections.Counter();sha_out={};new_mapping={};folders=collections.Counter()
 blueprint=None;redirects=None;content_bytes=0;indexable=noindex=0
 compressor_output=open(out,"wb")
 decomp=subprocess.Popen(["zstd","-dc",a.source],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 comp=subprocess.Popen(["zstd","-T2","-5","-q","-c"],stdin=subprocess.PIPE,stdout=compressor_output)
 try:
  with tarfile.open(fileobj=decomp.stdout,mode="r|") as source:
   with tarfile.open(fileobj=comp.stdin,mode="w|") as dest:
    for member in source:
     if member.isdir():continue
     if not member.isfile():raise ValueError("Non regular site file "+member.name)
     name=member.name.removeprefix("./")
     if name not in oldsha:raise ValueError("Unexpected source member "+name)
     content=source.extractfile(member).read()
     if hashlib.sha1(content).hexdigest()!=oldsha[name]:
      raise ValueError("Source content mismatch: "+name)
     created["input_members"]+=1
     new_path=name
     if name.startswith("__pages/") and name.endswith(".html"):
      if name.count("/")!=2:raise ValueError("Unexpected nested generated HTML path")
      new_path=name[:-5]+".page"
      created["converted_generated_HTML"]+=1
      match=ROBOTS_PATTERN.search(content)
      if not match:raise ValueError("robots meta missing on "+name)
      if b"noindex" in match.group(1).lower():noindex+=1
      else:indexable+=1
      old_slug=name.rsplit("/",1)[-1]
      info=oldmapping[old_slug]
      if info["to"]!=name or info["sha1"]!=oldsha[name]:
       raise ValueError("Legacy SEO original-to-shard map invalid "+old_slug)
      new_mapping[old_slug]={"to":new_path,"sha1":oldsha[name],"bytes":len(content),
         "noindex":b"noindex" in match.group(1).lower()}
      if old_slug==TUTOR_NAME:
       match=FORM_PATTERN.search(content)
       if not match:raise ValueError("Cannot locate one complete consultation form")
       blueprint=match.group(0)
     if name=="_redirects":
      redirects=[ln.split()[0] for ln in content.decode("utf8").splitlines() if len(ln.split())>=3 and ln.split()[2].startswith("301")]
      if len(set(redirects))<70:raise ValueError("Legacy 301 list unexpectedly small")
     if name=="netlify/edge-functions/shard-router.js":
      # The small pilot's forced noindex only applies to a Draft. In full Production,
      # per-page robots meta remains authoritative; we remove raw .page noindex headers
      # from the Edge-public response so 21964 indexable routes remain indexable.
      if not redirects:
       raise ValueError("Edge encountered before _redirects; avoid building wrong 301 precedence")
      txt=EDGE.replace("__LEGACY_REDIRECTS__",json.dumps(sorted(set(redirects)),ensure_ascii=False))
      txt=txt.replace('headers.set("X-Robots-Tag", "noindex, nofollow");',
                      'headers.delete("X-Robots-Tag");')
      if 'headers.delete("X-Robots-Tag");' not in txt:
       raise ValueError("Netlify public indexable noindex guard not converted")
      content=txt.encode("utf8")
      created["edge_modified"]+=1
     if name=="_headers":
      content += (b"\n# Block indexing internal payload source files\n"
                   b"/__pages/*\n  X-Robots-Tag: noindex, nofollow\n"
                   b"/__internal/*\n  X-Robots-Tag: noindex, nofollow\n")
      created["headers_modified"]+=1
     if new_path in sha_out:raise ValueError("Duplicate target file "+new_path)
     tarinfo=tarfile.TarInfo(new_path);tarinfo.size=len(content)
     tarinfo.mode=0o644;tarinfo.mtime=0
     dest.addfile(tarinfo,io.BytesIO(content))
     sha_out[new_path]=hashlib.sha1(content).hexdigest()
     folders[new_path.rsplit("/",1)[0] if "/" in new_path else "(root)"]+=1
     if new_path.endswith(".html"):created["static_html_count"]+=1
     if new_path.endswith(".page"):created["static_payload_count"]+=1
     if new_path.endswith(".png"):created["original_png_count"]+=1
     content_bytes+=len(content)
     if created["input_members"]%30000==0:
      print("FULL_PAYLOAD_BUILD_PROGRESS",created["input_members"],created["converted_generated_HTML"],flush=True)
    if created["input_members"]!=180799 or created["converted_generated_HTML"]!=158571:
     raise ValueError("Missing full input/generated HTML count")
    if indexable!=21964 or noindex!=136607:
     raise ValueError("SEO robots distribution changed "+str((indexable,noindex)))
    if blueprint is None:raise ValueError("Static Netlify Forms blueprint missing")
    # Preserve exact form inputs without exposing a second SEO page.
    form_page=(b'<!doctype html><html lang="ko"><head><meta charset="utf-8">'
      b'<meta name="robots" content="noindex,nofollow"></head><body>'
      +blueprint+b'</body></html>')
    bp="__internal/consultation-blueprint.html"
    form_header=tarfile.TarInfo(bp);form_header.size=len(form_page);form_header.mode=0o644;form_header.mtime=0
    dest.addfile(form_header,io.BytesIO(form_page))
    sha_out[bp]=hashlib.sha1(form_page).hexdigest()
    folders["__internal"]+=1
    created["static_html_count"]+=1
    content_bytes+=len(form_page)
  if decomp.wait(timeout=75)!=0:raise ValueError("Source zstd failed")
  comp.stdin.close()
  if comp.wait(timeout=90)!=0:raise ValueError("New archive compressor failed")
 finally:
  try:decomp.stdout.close()
  except:pass
  try:comp.stdin.close()
  except:pass
  compressor_output.close()
 assert len(sha_out)==180800
 assert created["static_payload_count"]==158571 and created["static_html_count"]==4
 assert folders["(root)"]==20,folders["(root)"]
 if max(folders.values())>=54000:raise ValueError("Netlify per-directory file cap violation")
 manifest=pathlib.Path(a.map_output);manifest.parent.mkdir(parents=True,exist_ok=True)
 with gzip.open(manifest,"wt",encoding="utf8",compresslevel=6) as f:
  json.dump({"source_SHA256":SOURCE_SHA,"original_public_html_to_data_payload":new_mapping,
             "target_SHA1_by_path":sha_out},f,ensure_ascii=False,separators=(",",":"))
 report={"status":"PASS_158571_SEO_PAGES_PRESERVED_IN_FULL_PAYLOAD_CANDIDATE",
    "source_full_sharded_sha256":SOURCE_SHA,
    "new_full_payload_archive_sha256":file_sha(out),
    "new_archive_bytes":out.stat().st_size,"generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "output_file_count":len(sha_out),"converted_generated_html_pages":created["converted_generated_HTML"],
    "Netlify_static_html_to_postprocess":created["static_html_count"],
    "all_public_HTML_routes_preserved_by_Edge":True,
    "original_SEO_indexable_pages":indexable,"original_SEO_noindex_pages":noindex,
    "new_payload_source_bytes_sum":content_bytes,
    "root_files":folders["(root)"],"max_directory_files":max(folders.values()),
    "all_original_images_kept":created["original_png_count"],"legacy_301_count":len(set(redirects)),
    "consultation_form_blueprint":bp,"original_form_mark_up_preserved":True,
    "raw_payload_noindex_headers":True,"public_indexable_noindex_header_stripped":True,
    "netlify_operations":0,"production_published":False,"form_POST_count":0,
    "runtime_warning":"Small pilot passed real Edge GET on isolated Review. Full 180800-file deploy still NOT tested; Forms registration and email require validation before Production."}
 rep=pathlib.Path(a.report);rep.parent.mkdir(parents=True,exist_ok=True)
 rep.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("FULL_HTML_PAYLOAD_SOURCE_ARCHIVE_OFFLINE_PASS",json.dumps(report,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
