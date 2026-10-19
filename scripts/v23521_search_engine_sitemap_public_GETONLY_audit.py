#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only complete englishpt.kr XML sitemap audit for Google and Naver registration.
No GSC/Naver login, submissions, IndexNow or Netlify mutations. Detect anomalies.
"""
import concurrent.futures,datetime,hashlib,json,pathlib,re,sys,urllib.parse,urllib.request,urllib.error,xml.etree.ElementTree as ET
HOST="englishpt.kr";SITE="https://"+HOST
INDEX=SITE+"/sitemap-index.xml"
HEADERS={"User-Agent":"ENGLISHPT-search-registration-preflight-readonly/1.0","Accept":"application/xml,text/xml,text/plain,text/html,*/*"}
OUT=pathlib.Path("search-registration-evidence");OUT.mkdir(parents=True,exist_ok=True)
def GET(url,limit=7000000):
    u=urllib.parse.urlsplit(url)
    if u.scheme!="https" or u.hostname!=HOST:
        raise ValueError("Only englishpt.kr exact host permitted")
    req=urllib.request.Request(url,headers=HEADERS,method="GET")
    with urllib.request.urlopen(req,timeout=35) as r:
        redirected=urllib.parse.urlsplit(r.geturl())
        if redirected.hostname!=HOST or redirected.scheme!="https":
            raise ValueError("Off-site redirect unexpected")
        return {"http":r.status,"final":r.geturl(),
          "headers":{"content_type":r.headers.get("Content-Type",""),
                     "x_robots_tag":r.headers.get("X-Robots-Tag","")},
          "data":r.read(limit+1)}
def parse_xml(blob,expected):
    if len(blob)>7000000:raise ValueError("XML unexpectedly >7 MB")
    root=ET.fromstring(blob)
    if root.tag.split("}")[-1]!=expected:raise ValueError("Wrong sitemap tag "+str(root.tag))
    locs=[]
    for node in root:
        loc=next((c.text for c in node if c.tag.split("}")[-1]=="loc"),None)
        if not loc:raise ValueError("Missing sitemap loc")
        locs.append(loc.strip())
    return locs
def one_child(url):
    r=GET(url)
    if r["http"]!=200:raise ValueError("Child sitemap not 200")
    urls=parse_xml(r["data"],"urlset")
    for u in urls:
        parsed=urllib.parse.urlsplit(u)
        if parsed.scheme!="https" or parsed.netloc!=HOST:
            raise ValueError("Unexpected child sitemap page host")
        if not parsed.path.endswith(".html"):
            raise ValueError("Unexpected indexable URL path "+parsed.path[:90])
    return {"sitemap":url,"url_count":len(urls),"bytes":len(r["data"]),
            "xml_sha256":hashlib.sha256(r["data"]).hexdigest()},urls
def verify_page(url):
    res=GET(url,600000)
    status=res["http"];body=res["data"].decode("utf8",errors="replace")
    canonical=re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"',body,re.I)
    bots=re.search(r'<meta\s+name="robots"\s+content="([^"]+)"',body,re.I)
    code=status==200 and canonical and canonical.group(1)==url and bots and "noindex" not in bots.group(1).lower() and "noindex" not in res["headers"]["x_robots_tag"].lower()
    return {"url":url,"http":status,"canonical_same":canonical is not None and canonical.group(1)==url,
            "robots_meta_indexable":bots is not None and "noindex" not in bots.group(1).lower(),
            "no_global_x_robots_noindex":"noindex" not in res["headers"]["x_robots_tag"].lower(),
            "pass":bool(code)}
def main():
    rep={"status":"HOLD","date_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "site":SITE,"sitemap_index":INDEX,"read_only":True,"HTTP_methods":["GET"],
         "Google_Search_Console_submission":False,"Naver_Search_Advisor_submission":False,
         "indexnow_not_used":True,"Netlify_changes":0,"errors":[]}
    try:
        robots=GET(SITE+"/robots.txt",120000)
        if robots["http"]!=200:raise ValueError("Robots not 200")
        rtext=robots["data"].decode("utf8","replace")
        if re.search(r"(?im)^\s*disallow:\s*/\s*$",rtext):
            raise ValueError("Robots has global Disallow /")
        rep["robots_http"]=robots["http"]
        rep["robots_contains_sitemap_directive"]=INDEX in rtext
        rep["robots_sitemap_directives"]=re.findall(r"(?im)^\s*Sitemap:\s*(.+?)\s*$",rtext)
        index=GET(INDEX)
        if index["http"]!=200:raise ValueError("Sitemap index not 200")
        rep["sitemap_index_http"]=index["http"]
        rep["sitemap_index_content_type"]=index["headers"]["content_type"]
        children=parse_xml(index["data"],"sitemapindex")
        if len(children)!=44 or len(set(children))!=44:
            raise ValueError("Expected precisely 44 unique child sitemaps")
        for child in children:
            p=urllib.parse.urlsplit(child)
            if p.scheme!="https" or p.hostname!=HOST:
                raise ValueError("Sitemap child offsite")
        rep["child_sitemaps_declared"]=len(children)
        allurls=set();duplicates=[];details=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures={pool.submit(one_child,u):u for u in children}
            for f in concurrent.futures.as_completed(futures):
                detail,urls=f.result();details.append(detail)
                for u in urls:
                    if u in allurls:
                        duplicates.append(u)
                    allurls.add(u)
        rep["child_sitemaps"]=sorted(details,key=lambda x:x["sitemap"])
        rep["indexable_unique_sitemap_urls"]=len(allurls)
        rep["duplicate_urls_count"]=len(duplicates)
        if duplicates:raise ValueError("Duplicate URL across sitemap shards")
        if len(allurls)!=21964:
            raise ValueError("Expected exactly 21964 unique canonical sitemap URLs")
        urls=sorted(allurls)
        sample=[urls[i*len(urls)//24] for i in range(24)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            rep["sampled_public_indexable"]=sorted(pool.map(verify_page,sample),key=lambda x:x["url"])
        rep["public_sample_count"]=len(rep["sampled_public_indexable"])
        rep["public_sample_pass_count"]=sum(x["pass"] for x in rep["sampled_public_indexable"])
        if rep["public_sample_pass_count"]!=24:raise ValueError("Some public sample URLs invalid")
        home=GET(SITE+"/",200000)
        rep["home_http"]=home["http"]
        rep["home_has_naver_verification_meta"]=bool(re.search(r'name=["\']naver-site-verification["\']',home["data"].decode("utf8","replace"),re.I))
        rep["home_has_google_verification_meta"]=bool(re.search(r'name=["\']google-site-verification["\']',home["data"].decode("utf8","replace"),re.I))
        if home["http"]!=200:raise ValueError("Homepage failed")
        rep["status"]="PASS_LIVE_SITEMAP_INDEX_44_CHILD_21964_UNIQUE_AND_24_INDEXABLE_SAMPLE"
    except Exception as err:
        rep["errors"].append(type(err).__name__+": "+str(err)[:350])
        rep["status"]="HOLD_LIVE_SITEMAP_AUDIT"
    target=OUT/"LIVE_GOOGLE_NAVER_SITEMAP_GETONLY_PREFLIGHT.json"
    target.write_text(json.dumps(rep,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("ENPT_GOOGLE_NAVER_LIVE_SITEMAP_PREFLIGHT",json.dumps(
        {k:v for k,v in rep.items() if k not in ("child_sitemaps","sampled_public_indexable")},ensure_ascii=False),flush=True)
    return 0 if rep["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
