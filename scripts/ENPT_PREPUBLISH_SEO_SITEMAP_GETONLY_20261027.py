#!/usr/bin/env python3
"""Prepublish SEO-only GET checks: robots, sitemap index and all child XML, indexability and canonical.
No writes to services, no form submissions.
"""
import collections,datetime,json,os,pathlib,re,urllib.error,urllib.request,xml.etree.ElementTree as ET
from html.parser import HTMLParser
ROOT="https://englishpt.kr"
OUT=pathlib.Path("region-prepublish-seo-20261027");OUT.mkdir(exist_ok=True)
class Meta(HTMLParser):
 def __init__(self):
  super().__init__();self.canon=[];self.robots=[];self.description=[];self.title=[];self.capture=False
 def handle_starttag(self,tag,attr):
  d=dict(attr)
  if tag=="link" and d.get("rel","").lower()=="canonical":self.canon.append(d.get("href",""))
  if tag=="meta" and d.get("name","").lower()=="robots":self.robots.append(d.get("content",""))
  if tag=="meta" and d.get("name","").lower()=="description":self.description.append(d.get("content",""))
  if tag=="title":self.capture=True
 def handle_endtag(self,tag):
  if tag=="title":self.capture=False
 def handle_data(self,text):
  if self.capture:self.title.append(text)
def request(url,maxsize=15000000):
 try:
  req=urllib.request.Request(url,method="GET",headers={"User-Agent":"ENPT-Owner-SEO-Prepublish-GETONLY"})
  with urllib.request.urlopen(req,timeout=45) as r:return {"url":url,"status":r.status,"content_type":r.headers.get("content-type",""),"x_robots":r.headers.get("x-robots-tag",""),"body":r.read(maxsize),"final_url":r.geturl()}
 except urllib.error.HTTPError as e:return {"url":url,"status":e.code,"error":str(e)}
 except Exception as e:return {"url":url,"status":None,"error":type(e).__name__+":"+str(e)[:200]}
def main():
 report={"time_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"read_only":True,"form_submissions":0,"production_writes":0,"urls":[],"sitemaps":[],"errors":[]}
 for path in ["/robots.txt","/sitemap-index.xml","/englishpt.html","/courses.html","/student-english.html","/exam-english.html","/stations.html"]:
  r=request(ROOT+path)
  entry={k:v for k,v in r.items() if k!="body"}
  if r["status"]==200 and path.endswith(".html"):
   p=Meta();p.feed(r["body"].decode("utf8","replace"));entry.update(title="".join(p.title)[:170],canonical=p.canon,robots_meta=p.robots,meta_description_count=len(p.description))
   if p.canon!=[ROOT+path]:report["errors"].append({"path":path,"error":"NONSELF_CANONICAL","observed":p.canon})
   if any("noindex" in t.lower() for t in p.robots):report["errors"].append({"path":path,"error":"CORE_NOINDEX"})
  if r["status"]!=200:report["errors"].append({"path":path,"error":"HTTP_UNAVAILABLE","observed":r.get("error") or r["status"]})
  report["urls"].append(entry)
 idx=request(ROOT+"/sitemap-index.xml")
 if idx["status"]==200:
  try:
   root=ET.fromstring(idx["body"])
   locs=[(e.text or "").strip() for e in root.iter() if e.tag.endswith("loc")]
   report["sitemap_index_child_count"]=len(locs)
   for u in locs[:100]:
    s=request(u)
    obj={"url":u,"status":s["status"],"bytes":len(s.get("body",b""))}
    if s["status"]==200:
     try:
      xml=ET.fromstring(s["body"]);urls=[(e.text or "").strip() for e in xml.iter() if e.tag.endswith("loc")]
      obj["url_count"]=len(urls)
     except Exception as err:obj["parse_error"]=str(err)[:140];report["errors"].append({"url":u,"error":"XML_PARSE"})
    else:report["errors"].append({"url":u,"error":"SITEMAP_NOT_200","status":s["status"]})
    report["sitemaps"].append(obj)
  except Exception as err:report["errors"].append({"error":"INDEX_XML_PARSE","detail":str(err)[:180]})
 report["sitemap_total_loc_count"]=sum(x.get("url_count",0) for x in report["sitemaps"])
 report["status"]="PASS_SEO_SITEMAP" if not report["errors"] else "REVIEW_SEO_ERRORS"
 (OUT/"ENPT_PUBLISH_GUARD_SEO_SITEMAPS.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
 print("ENPT_SEO_SITEMAP_SUMMARY",json.dumps({k:v for k,v in report.items() if k not in ("urls","sitemaps")},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
