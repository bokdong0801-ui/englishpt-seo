#!/usr/bin/env python3
"""GET-only verify Google ownership meta in live englishpt.kr root and canonical home."""
import datetime,json,pathlib,re,urllib.request,urllib.parse,sys
HOST="englishpt.kr"
CODE="OTG-5ooTZYTm-HnTOi8I0TRV4bZHUD-uSYSOih3E8ig"
TAG=('<meta name="google-site-verification" content="'+CODE+'" />').encode()
OUT=pathlib.Path("publish-evidence");OUT.mkdir(exist_ok=True)
def get(path):
 u="https://englishpt.kr"+path
 req=urllib.request.Request(u,method="GET",headers={"User-Agent":"ENPT-GoogleOwnership-POST-PUBLISH-GETONLY"})
 with urllib.request.urlopen(req,timeout=30) as r:
  if r.status!=200:raise ValueError("HTTP not 200 "+path)
  if urllib.parse.urlsplit(r.geturl()).hostname!=HOST:raise ValueError("Host changed")
  return r.read(600000),r.headers.get("Content-Type","")
def run():
 report={"status":"HOLD","checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "production_modified_by_this_check":False,"google_property_verified":False,
         "site_maps_submitted":False,"form_POSTs":0,"checks":[],"errors":[]}
 for path in ["/index.html","/englishpt.html"]:
  try:
   b,typ=get(path)
   m=re.search(rb"<head\b[^>]*>(.*?)</head>",b,re.I|re.S)
   if not m or m.group(1).count(TAG)!=1:raise ValueError("Exact meta missing/duplicated in HEAD")
   if "text/html" not in typ.lower():raise ValueError("Not HTML")
   if path=="/englishpt.html":
    if b'<link rel="canonical" href="https://englishpt.kr/englishpt.html"' not in b:
     raise ValueError("Expected existing canonical not present")
   report["checks"].append({"path":path,"http":200,"tag_in_head":True})
  except Exception as exc:report["errors"].append({"path":path,"problem":type(exc).__name__+": "+str(exc)})
 try:
  b,typ=get("/robots.txt")
  if b"Disallow: /" in b:raise ValueError("Robots globally disallows")
  report["checks"].append({"path":"/robots.txt","http":200})
 except Exception as exc:report["errors"].append({"path":"/robots.txt","problem":str(exc)})
 try:
  b,typ=get("/sitemap-index.xml")
  if b"sitemapindex" not in b:raise ValueError("Bad sitemap")
  report["checks"].append({"path":"/sitemap-index.xml","http":200})
 except Exception as exc:report["errors"].append({"path":"/sitemap-index.xml","problem":str(exc)})
 report["status"]="PASS_GSC_EXACT_TAG_ON_REAL_PUBLISHED_HOME" if not report["errors"] else "HOLD_GSC_TAG_ON_LIVE"
 (OUT/"GSC_EXACT_OWNERSHIP_META_ON_LIVE_HOMEPAGE.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("GSC_META_LIVE_POSTPUBLISH",json.dumps(report,ensure_ascii=False),flush=True)
 return 0 if not report["errors"] else 1
if __name__=="__main__":sys.exit(run())
