#!/usr/bin/env python3
"""v23.5.1 strictly-scoped SEO metadata overlay for 2733 off-sitemap routes.
Safe offline patch to a copied frozen release. Never touches Netlify or production.
"""
import argparse
import json
import re
import sys
import traceback
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit,unquote

BASE="https://englishpt.kr"
ROBOTS=re.compile(r'(<meta\s+name="robots"\s+content=")([^"]+)(")',re.I)
CANONICAL=re.compile(r'<link rel="canonical" href="([^"]+)">')
OG=re.compile(r'<meta property="og:image" content="([^"]+)">')
BAD_SUFFIXES=("-mid-tutor.html","-high-tutor.html","-elem-conv.html")
def collect_sitemap(root):
    seen=set();queue=["sitemap-index.xml"];urls=set()
    while queue:
        filename=queue.pop(0)
        if filename in seen:continue
        seen.add(filename)
        path=root/filename
        if not path.is_file():raise ValueError("missing referenced XML "+filename)
        doc=ET.parse(path).getroot()
        kind=doc.tag.rsplit("}",1)[-1]
        if kind not in ("sitemapindex","urlset"):raise ValueError("invalid sitemap XML "+filename)
        for item in doc:
            loc=next((x.text for x in item if x.tag.rsplit("}",1)[-1]=="loc"),None)
            if not loc:raise ValueError("sitemap loc missing "+filename)
            loc=loc.strip()
            u=urlsplit(loc)
            if u.scheme!="https" or u.netloc not in ("englishpt.kr","www.englishpt.kr"):
                raise ValueError("sitemap references external "+loc)
            if kind=="sitemapindex":queue.append(unquote(u.path).lstrip("/"))
            else:urls.add(loc)
    return urls,seen
def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--root",type=Path,required=True)
    arg.add_argument("--report",type=Path,required=True)
    arg.add_argument("--overlay-dir",type=Path,required=True)
    opts=arg.parse_args()
    root=opts.root.resolve()
    details={"version":"v23.5.1","source_run":38864767374,"status":"STARTED",
             "sitemap_urls":0,"unlisted_indexable_before":0,"corrected":0,
             "station_variants_corrected":0,"other_unlisted_corrected":0,
             "corrected_files":[],"errors":[],"errors_count":0,
             "prod_header_updated":False,
             "production_deployed":False,"netlify_deployed":False}
    sample=[]
    try:
        sitemap,xmls=collect_sitemap(root)
        details["sitemap_urls"]=len(sitemap)
        if len(sitemap)!=21964:raise ValueError("Sitemap unexpectedly changed "+str(len(sitemap)))
        targets=[]
        for i,page in enumerate(sorted(root.glob("*.html"))):
            if page.name in ("index.html","404.html"):continue
            url=BASE+"/"+page.name
            doc=page.read_text("utf8")
            match=ROBOTS.search(doc)
            if not match:raise ValueError("missing robots "+page.name)
            tokens={x.strip().lower() for x in match.group(2).split(",")}
            if "noindex" not in tokens and url not in sitemap:
                targets.append((page,doc,match))
            if (i+1)%45000==0:print("SEO_FIX_CANDIDATE_PROGRESS",i+1,flush=True)
        details["unlisted_indexable_before"]=len(targets)
        if len(targets)!=2733:raise ValueError("expected 2733 mismatched pages, got "+str(len(targets)))
        station=[p for p,_,_ in targets if p.name.startswith("station-") and p.name.endswith(BAD_SUFFIXES)]
        other=[p for p,_,_ in targets if p.name.startswith("dalseo-songhyeondong-") and p.name.endswith(BAD_SUFFIXES)]
        # Verified in actual full HTML: all 2733 off-sitemap indexables are
        # station variants. The three Songhyeondong suffix pages already have noindex.
        if len(station)!=2733 or len(other)!=0:
            raise ValueError(f"Unexpected target identities station={len(station)} other={len(other)}")
        for p,doc,m in targets:
            original_title=re.search(r'<title>(.*?)</title>',doc,re.S)
            canonical=CANONICAL.findall(doc);image=OG.findall(doc)
            if len(canonical)!=1 or canonical[0]!=BASE+"/"+p.name or len(image)!=1:
                raise ValueError("metadata identity invalid "+p.name)
            old_tokens=[x.strip() for x in m.group(2).split(",") if x.strip()]
            new_tokens=[x for x in old_tokens if x.lower() not in ("index","noindex")]
            # Preserve 'follow'; avoid accidental nofollow. Excluded URL may still
            # lead crawlers to another related page.
            if not any(x.lower()=="follow" for x in new_tokens):new_tokens.insert(0,"follow")
            new_tokens.insert(0,"noindex")
            replaced=doc[:m.start(2)]+",".join(new_tokens)+doc[m.end(2):]
            if CANONICAL.findall(replaced)!=canonical or OG.findall(replaced)!=image:
                raise ValueError("canonical/OG mutation "+p.name)
            if re.search(r'<title>(.*?)</title>',replaced,re.S).group(0)!=original_title.group(0):
                raise ValueError("title mutation "+p.name)
            p.write_text(replaced,encoding="utf8")
            overlay=opts.overlay_dir/p.name
            overlay.parent.mkdir(parents=True,exist_ok=True)
            overlay.write_text(replaced,encoding="utf8")
            details["corrected"]+=1
            details["station_variants_corrected"]+=int(p.name.startswith("station-"))
            details["other_unlisted_corrected"]+=int(not p.name.startswith("station-"))
            if len(sample)<60:sample.append({"file":p.name,"old":m.group(2),"new":",".join(new_tokens)})
            if details["corrected"]%500==0:
                print("SEO_POLICY_FIX_PROGRESS",details["corrected"],"/2733",flush=True)
        details["corrected_samples"]=sample
        details["status"]="PASS_V2351_2733_UNLISTED_ROBOTS_POLICY_CORRECTED"
    except Exception as exc:
        details["errors_count"]=1
        details["errors"].append({"reason":str(exc),"trace":traceback.format_exc()[-1400:]})
        details["status"]="FAIL_V2351_2733_UNLISTED_ROBOTS_POLICY_CORRECTED"
    finally:
        opts.report.parent.mkdir(parents=True,exist_ok=True)
        opts.report.write_text(json.dumps(details,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(details["status"],"fixed",details["corrected"],"errors",details["errors_count"],flush=True)
    return 0 if details["status"].startswith("PASS") else 1
if __name__=="__main__":sys.exit(main())
