#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v23.5.1 158571 page comprehensive indexing and sitemap preproduction audit.
Strictly read-only: never deploys and never writes to site root.
"""
import argparse
import json
import re
import sys
import traceback
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, unquote
from datetime import datetime,timezone

SITE="https://englishpt.kr"
ROBOTS=re.compile(r'<meta\s+name="robots"\s+content="([^"]+)"',re.I)
CANONICAL=re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"',re.I)
HTML_DESC=re.compile(r'<meta\s+name="description"\s+content="([^"]+)"',re.I)
HEAD_TITLE=re.compile(r'<title>(.*?)</title>',re.I|re.S)
OG=re.compile(r'<meta\s+property="og:image"\s+content="([^"]+)"',re.I)
LOCS=re.compile(r'<loc>([^<]+)</loc>')
def local(url):
    u=urlsplit(url.strip())
    if u.scheme!="https" or u.netloc not in ("englishpt.kr","www.englishpt.kr") or u.query or u.fragment:
        raise ValueError("Invalid or non-local sitemap URL: "+url)
    key=unquote(u.path).lstrip("/")
    if not key or ".." in key.split("/"):raise ValueError("Unsafe sitemap path: "+url)
    return key
def xml_loc(path):
    tree=ET.parse(path)
    root=tree.getroot()
    typ=root.tag.rsplit("}",1)[-1]
    if typ not in ("sitemapindex","urlset"):
        raise ValueError("invalid XML root "+typ)
    tags=["sitemap","url"] if typ=="sitemapindex" else ["url"]
    refs=[]
    for item in list(root):
        if item.tag.rsplit("}",1)[-1] not in tags:
            continue
        loc=next((x.text for x in list(item) if x.tag.rsplit("}",1)[-1]=="loc"),None)
        if not loc:raise ValueError("sitemap entry missing <loc> in "+str(path))
        refs.append(loc.strip())
    return typ,refs
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    args=parser.parse_args()
    root=args.root.resolve()
    results={
        "version":"v23.5.1","source_run":38864767374,
        "original_source_run":38689660290,
        "original_source_sha":"a18b8901ecda7d37f65e35b15f03d579ec63c70f",
        "status":"RUNNING","production_deployed":False,
        "html_total":0,"generated_total":0,
        "indexable_count":0,"noindex_count":0,
        "new_student_pages_count":0,"new_student_noindex_count":0,
        "invalid_robots_count":0,"canonicals_matched":0,
        "canonical_duplicates":0,
        "html_missing_title":0,"html_missing_description":0,"html_missing_og":0,
        "sitemap_index_refs":0,"sitemap_xml_files":0,"sitemap_total_entries":0,
        "sitemap_unique_urls":0,"sitemap_duplicate_urls":0,
        "indexable_missing_from_sitemaps":0,"noindex_in_sitemaps":0,
        "sitemap_nonexistent_html":0,"sitemap_noncanonical_urls":0,
        "sitemap_extra_or_nonindexable":0,
        "robots_sitemap_declared":False,"robots_crawler_allowed":False,
        "site_header_draft_noindex":False,
        "errors_count":0,"error_reason_counts":{},"error_samples":[],
        "excluded_filenames":["index.html","404.html"],
        "limitations":["Live search-engine indexation is not verified by offline XML audit",
          "All locality detail pages preserve noindex; their absence from sitemap is intentional until deliberate rollout",
          "Live form submission and email notification excluded"]
    }
    errors=[];counter=Counter()
    def fail(where,reason,extra=""):
        results["errors_count"]+=1;counter[reason]+=1
        if len(errors)<100:errors.append({"file":where,"reason":reason,"detail":str(extra)[:200]})
    try:
        pages=sorted(root.glob("*.html"))
        results["html_total"]=len(pages)
        generated=[p for p in pages if p.name not in ("index.html","404.html")]
        results["generated_total"]=len(generated)
        if len(generated)!=158571:fail("(root)","generated_count_mismatch",len(generated))
        if len(pages)!=158573:fail("(root)","all_html_count_mismatch",len(pages))
        names={p.name for p in pages}
        indexable=set();noindex=set();canonical_seen=set()
        new_suffixes=("-mid-tutor.html","-high-tutor.html","-elem-conv.html")
        for i,p in enumerate(generated):
            text=p.read_text("utf-8",errors="replace")
            canonical=CANONICAL.findall(text)
            if len(canonical)!=1 or canonical[0]!=SITE+"/"+p.name:
                fail(p.name,"canonical_wrong_or_missing",canonical[:2])
            else:results["canonicals_matched"]+=1
            if canonical and canonical[0] in canonical_seen:
                results["canonical_duplicates"]+=1;fail(p.name,"canonical_duplicate",canonical[0])
            canonical_seen.update(canonical)
            if len(HEAD_TITLE.findall(text))!=1:
                results["html_missing_title"]+=1;fail(p.name,"title_missing_or_duplicate")
            if len(HTML_DESC.findall(text))!=1:
                results["html_missing_description"]+=1;fail(p.name,"description_missing_or_duplicate")
            if len(OG.findall(text))!=1:
                results["html_missing_og"]+=1;fail(p.name,"og_image_missing_or_duplicate")
            robots=ROBOTS.findall(text)
            if len(robots)!=1:
                results["invalid_robots_count"]+=1;fail(p.name,"robots_meta_count",len(robots))
                continue
            tokens={s.strip().lower() for s in robots[0].split(",")}
            if "noindex" in tokens and "index" in tokens:
                results["invalid_robots_count"]+=1;fail(p.name,"conflicting_robots")
            if "noindex" in tokens:noindex.add(SITE+"/"+p.name)
            else:indexable.add(SITE+"/"+p.name)
            # Only the 6060 locality clusters expanded by v23.5.1 count as NEW.
            # 911 station routes and Songhyeondong share suffix names but predate v23.5.1.
            suffix=next((x for x in new_suffixes if p.name.endswith(x)),None)
            if suffix:
                slug=p.name[:-len(suffix)]
                is_regional=(root/(slug+"-worker-english-conv-academy.html")).is_file() and (
                    root/(slug+"-mid-conv.html")).is_file() and (
                    root/(slug+"-high-conv.html")).is_file()
                if is_regional:
                    results["new_student_pages_count"]+=1
                    if "noindex" in tokens:results["new_student_noindex_count"]+=1
                    else:fail(p.name,"new_student_page_unexpectedly_indexable")
            if (i+1)%35000==0:
                print("SEO_INDEX_AUDIT_PROGRESS",i+1,len(generated),
                      "indexable",len(indexable),"noindex",len(noindex),flush=True)
        results["indexable_count"]=len(indexable)
        results["noindex_count"]=len(noindex)
        if len(indexable)!=21964:fail("(totals)","indexable_count_unexpected",len(indexable))
        if len(noindex)!=136607:fail("(totals)","noindex_count_unexpected",len(noindex))
        if results["new_student_pages_count"]!=18180:fail("(totals)","new_student_page_count",results["new_student_pages_count"])
        if results["new_student_noindex_count"]!=18180:fail("(totals)","new_student_noindex_count",results["new_student_noindex_count"])
        if len(indexable&noindex):fail("(totals)","indexable_and_noindex_overlap",len(indexable&noindex))
        robots_path=root/"robots.txt"
        if not robots_path.is_file():fail("robots.txt","robots_txt_missing")
        else:
            robots=robots_path.read_text("utf-8",errors="replace")
            results["robots_sitemap_declared"]=("Sitemap: https://englishpt.kr/sitemap-index.xml" in robots)
            results["robots_crawler_allowed"]=bool(re.search(r'User-agent:\s*\*\s*\n\s*Allow:\s*/',robots,re.I))
            if not results["robots_sitemap_declared"]:fail("robots.txt","sitemap_directive_missing")
            if not results["robots_crawler_allowed"]:fail("robots.txt","general_crawler_allow_missing")
            # Critical: a disallow wildcard means no pages can be crawled despite site metadata.
            if re.search(r'(?im)^\s*Disallow:\s*/\s*$',robots):
                fail("robots.txt","root_disallow_present")
        headers=(root/"_headers").read_text("utf-8",errors="replace") if (root/"_headers").exists() else ""
        results["site_header_draft_noindex"]="X-Robots-Tag: noindex" in headers
        # Source can be a Draft artifact with _headers:noindex, but production should not inherit this rule.
        if results["site_header_draft_noindex"]:
            results.setdefault("warnings",[]).append(
                "Frozen Review-only archive contains global X-Robots-Tag: noindex. This header MUST be stripped and revalidated in any future Production package; otherwise even the 21964 indexable pages cannot index.")
        pending=["sitemap-index.xml"];visited=set();sitemap_urls=[];sitemap_file_refs=0;index_details=[]
        while pending:
            name=pending.pop(0)
            if name in visited:continue
            visited.add(name)
            path=root/name
            if not path.is_file():
                fail(name,"sitemap_referenced_file_missing")
                continue
            try:
                typ,locations=xml_loc(path)
            except Exception as exc:
                fail(name,"xml_invalid",exc);continue
            if typ=="sitemapindex":
                index_details.append({"file":name,"children":len(locations)})
                sitemap_file_refs+=len(locations)
                for url in locations:
                    try:child=local(url)
                    except Exception as exc:
                        fail(name,"invalid_sitemap_index_loc",exc);continue
                    pending.append(child)
            else:
                results["sitemap_xml_files"]+=1
                sitemap_urls.extend(locations)
            if len(visited)>15000:
                fail("(sitemaps)","xml_index_cycle_or_excessive_shards",len(visited));break
        results["sitemap_index_refs"]=sitemap_file_refs
        results["sitemap_total_entries"]=len(sitemap_urls)
        results["sitemap_unique_urls"]=len(set(sitemap_urls))
        results["sitemap_duplicate_urls"]=len(sitemap_urls)-len(set(sitemap_urls))
        if results["sitemap_duplicate_urls"]:
            fail("(sitemaps)","sitemap_duplicate_urls",results["sitemap_duplicate_urls"])
        sitemap=set(sitemap_urls)
        missing=indexable-sitemap
        inserted_noindex=sitemap&noindex
        extra=sitemap-indexable
        results["indexable_missing_from_sitemaps"]=len(missing)
        results["noindex_in_sitemaps"]=len(inserted_noindex)
        results["sitemap_extra_or_nonindexable"]=len(extra)
        results["sitemap_shards_reachable"]=len(visited)
        results["index_details"]=index_details[:100]
        for u in list(sorted(missing))[:15]:
            fail("(sitemaps)","indexable_missing_from_sitemap",u)
        for u in list(sorted(inserted_noindex))[:15]:
            fail("(sitemaps)","noindex_in_sitemap",u)
        if len(missing)>15:results["errors_count"]+=len(missing)-15;counter["indexable_missing_from_sitemap"]+=len(missing)-15
        if len(inserted_noindex)>15:results["errors_count"]+=len(inserted_noindex)-15;counter["noindex_in_sitemap"]+=len(inserted_noindex)-15
        for u in sorted(extra)[:20]:
            if u not in noindex:
                fail("(sitemaps)","extra_or_invalid_sitemap_url",u)
        for u in sitemap:
            try:
                location=local(u)
                if location not in names:
                    results["sitemap_nonexistent_html"]+=1
                    # URLs representing directory home index can be valid; record, but flag for canonical validation.
                    if results["sitemap_nonexistent_html"]<=15:
                        fail("(sitemaps)","sitemap_url_lacks_html",u)
                elif location not in ("index.html","404.html") and u!=SITE+"/"+location:
                    results["sitemap_noncanonical_urls"]+=1
                    if results["sitemap_noncanonical_urls"]<=15:
                        fail("(sitemaps)","noncanonical_sitemap_url",u)
            except Exception as exc:fail("(sitemaps)","invalid_sitemap_url",exc)
        results["sitemap_samples"]=sorted(sitemap)[:8]
        results["sample_missing_indexable"]=sorted(missing)[:20]
        results["sample_noindex_leak"]=sorted(inserted_noindex)[:20]
        print("SEO_AUDIT_TOTALS",json.dumps({k:results[k] for k in (
            "generated_total","indexable_count","noindex_count","new_student_noindex_count",
            "sitemap_unique_urls","indexable_missing_from_sitemaps",
            "noindex_in_sitemaps","sitemap_nonexistent_html","errors_count")}),flush=True)
    except Exception:
        fail("(runner)","audit_crashed",traceback.format_exc()[-2400:])
    finally:
        results["error_reason_counts"]=dict(counter)
        results["error_samples"]=errors
        results["status"]="PASS_V2351_INDEXING_SITEMAP_FULL_QA" if results["errors_count"]==0 else "HOLD_V2351_INDEXING_SITEMAP_FULL_QA"
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(results["status"],"errors",results["errors_count"],"reasons",dict(counter),flush=True)
    return 0 if results["status"].startswith("PASS") else 1
if __name__=="__main__":sys.exit(main())
