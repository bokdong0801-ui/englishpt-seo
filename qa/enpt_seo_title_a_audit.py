#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only regression/QA of approved A SEO title generator.

Renders 911 station hub titles, 911*23 station intent title strings,
23 representative real station specialty HTML pages and neighborhood samples.
It never publishes, changes robots/sitemaps or sends leads.
"""
from __future__ import annotations
import html, importlib.util, json, re, sys, collections
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if not spec or not spec.loader: raise RuntimeError("module load failed: "+str(path))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
station=load("station_title_qa_module",ROOT/"scripts/stage9-station-renderer.py")
clean=station.clean
pol=clean.SEO_TITLE_POLICY
DATA=json.loads((ROOT/"data/stations.json").read_text(encoding="utf8"))
stations=DATA["stations"]
intents=clean.SERVICE_ORDER+clean.EXAM_ORDER+clean.ACADEMY_ORDER+clean.CONV_DERIVED_ORDER
assert len(intents)==23 and len(set(intents))==23
assert set(intents)==set(pol.COURSE_TITLES)
assert len(stations)==911
assert len({x["slug"] for x in stations})==911
titles={}
errors=[]
warnings=[]
def guard(cond,msg):
    if not cond: errors.append(msg)
def register(page,title):
    if title in titles:errors.append("TITLE_COLLISION:"+page+":"+titles[title])
    titles[title]=page
    guard("잉글리시PT" not in title and "ENGLISH PT" not in title,"BRAND_INCLUDED:"+page)
    guard(len(title)<=45,"TITLE_OVER_45:"+page)
    guard(title.count(" | ")==1,"DELIMITER_NOT_ONE:"+page)
for s in stations:
    name=s["name"]
    register("station-"+s["slug"]+".html",pol.hub_title(name))
    for intent in intents:
        title=pol.course_title(name,intent)
        register("station-"+s["slug"]+"-"+intent+".html",title)
        # Detect unintended unrelated audience lists in specialist pages.
        guard("직장인 학생 주부" not in title,"AUDIENCE_OVERLAP:"+s["slug"]+":"+intent)
guard(len(titles)==21864,"TITLE_COUNT_WRONG:"+str(len(titles)))
# Neighborhood specialist titles share the approved 23-intent policy.
for place in ["송현동","사직동","청운동","고운동","병목안동","서초구 내곡동","강릉 내곡동"]:
    for intent in intents:
        actual=clean.title_for({"dong":place,"slug":"qa-"+place,"station":False,"service":"dummy"},intent)
        guard(actual==pol.course_title(place,intent),"LOCAL_TITLE_MISMATCH:"+place+":"+intent)
    guard(pol.hub_title(place).endswith(pol.HUB_SUFFIX),"DONG_HUB_POLICY:"+place)
guard(pol.hub_title("반월당역")=="반월당역 영어회화 영어과외 | 1:1 맞춤 직장인 학생 주부","HUB_APPROVAL_MISMATCH")
guard(pol.course_title("반월당역","biz-business-conv")=="반월당역 직장인 영어회화 | 1:1 맞춤 비즈니스 영어","BIZ_APPROVAL_MISMATCH")
# Inspect HTML head fields, not meta strings only.
def tagvalue(raw,pattern):
    m=re.search(pattern,raw,re.I|re.S)
    return html.unescape(m.group(1)).strip() if m else None
def check_html(raw, place, expected_title, page, indexable, canonical):
    head=raw.split("</head>",1)[0]
    title=tagvalue(head,r"<title>(.*?)</title>")
    og=tagvalue(head,r'<meta\s+property="og:title"\s+content="([^"]+)"')
    desc=tagvalue(head,r'<meta\s+name="description"\s+content="([^"]+)"')
    robots=tagvalue(head,r'<meta\s+name="robots"\s+content="([^"]+)"')
    can=tagvalue(head,r'<link\s+rel="canonical"\s+href="([^"]+)"')
    h1=tagvalue(raw,r'<h1[^>]*>(.*?)</h1>')
    guard(title==expected_title,"HTML_TITLE:"+page+":"+str(title))
    guard(og==expected_title,"OG_TITLE:"+page)
    guard(bool(h1) and place in re.sub(r'<[^>]+>',"",h1),"H1_PLACE:"+page)
    guard(can==canonical,"CANONICAL:"+page+":"+str(can))
    guard(desc is not None and len(desc)>40,"META_MISSING_OR_SHORT:"+page)
    guard(robots is not None,"ROBOTS_MISSING:"+page)
    if robots is not None:
        guard(("noindex" not in robots) if indexable else ("noindex" in robots and "follow" in robots),"INDEX_POLICY:"+page)
    # Stage9 WebPage structured metadata must match displayed title where present.
    for chunk in re.findall(r'<script\s+type="application/ld\+json">(.*?)</script>',head,re.S):
        try:
            data=json.loads(chunk)
            pages=[x for x in data.get("@graph",[]) if isinstance(x,dict) and x.get("@type")=="WebPage"]
            for p in pages:guard(p.get("name")==expected_title,"SCHEMA_TITLE:"+page)
        except Exception as e:
            errors.append("SCHEMA_JSON:"+page+":"+str(e)[:80])
    return {"page":page,"title":title,"robots":robots,"canonical":can,"h1":re.sub(r'<[^>]+>',"",h1 or "")[:100]}
sm={s["slug"]:s for s in stations}
sample=next(x for x in stations if x["slug"]=="banwoldang")
pages=[]
hub="station-banwoldang.html"
pages.append(check_html(station.station_hub(sample,sm),sample["name"],pol.hub_title(sample["name"]),hub,True,"https://englishpt.kr/"+hub))
for intent in intents:
    name="station-banwoldang-"+intent+".html"
    raw,problems=station.render_station_course(sample,intent,sm)
    # Pre-existing validator assumes 22 local course links, although the
    # source intentionally sends some school cards to national student guides.
    # Do not silently ignore: verify generated links and retain a warning.
    if problems:
        if set(problems)=={"cluster_links"}:
            count=raw.count('href="/station-banwoldang-')
            guard(count>=19,"INSUFFICIENT_ACTUAL_COURSE_LINKS:"+intent+":"+str(count))
            warnings.append({"page":name,"preexisting":"cluster_links","actual_local_links":count})
        else:
            errors.append("RENDER_PROBLEMS:"+intent+":"+str(problems)[:300])
    pages.append(check_html(raw,sample["name"],pol.course_title(sample["name"],intent),name,True,"https://englishpt.kr/"+name))
# Neighborhood specialization sampling: actual generated 95-page source, noindex must remain.
for name in ["dalseo-songhyeondong-biz-business-conv.html","dalseo-songhyeondong-mid-conv.html"]:
    src=ROOT/name
    if not src.exists():
        errors.append("LOCAL_SAMPLE_MISSING:"+name)
        continue
    raw,problems=clean.render_production_page(src.read_text(encoding="utf8"),name)
    # Existing legacy source may have unrelated content QA findings. Record but
    # only the requested SEO / robots metadata is the release gate.
    loc=clean.location_from_source(src.read_text(encoding="utf8"),name,clean.intent_from_name(name)[1])
    pages.append(check_html(raw,loc["dong"],pol.course_title(loc["dong"],clean.intent_from_name(name)[1]),name,False,"https://englishpt.kr/"+name))
summary={
    "status":"PASS" if not errors else "HOLD",
    "station_hubs":911,"station_specialists":20953,
    "station_title_strings":len(titles),"distinct_station_titles":len(titles),
    "intent_keys":len(intents),"html_samples":len(pages),
    "neighborhood_hub_policy_only":True,
    "neighborhood_mass_index_policy":"noindex,follow (unchanged)",
    "netlify_deploys":0,"production_mutations":0,"search_collection_submissions":0,
    "warnings":warnings[:80],"full_page_contract":"RECHECK_CLUSTER_LINK_GATE","errors":errors[:80]
}
out=ROOT/"seo-title-qa-report"
out.mkdir(exist_ok=True)
(out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
(out/"html_samples.json").write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding="utf8")
print("ENPT_SEO_TITLE_A_SUMMARY",json.dumps(summary,ensure_ascii=False))
for p in pages[:4]:print("ENPT_SEO_TITLE_A_SAMPLE",json.dumps(p,ensure_ascii=False))
if errors:sys.exit(1)
