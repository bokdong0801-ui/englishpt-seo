#!/usr/bin/env python3
"""All 910 station elementary pages P1 vs P3, actual HTML via GET only, SEO safe."""
import collections,concurrent.futures,csv,datetime,hashlib,json,pathlib,re,time,urllib.request
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/"p3-live-910-comparison";OUT.mkdir(exist_ok=True)
ST=json.loads((ROOT/"data/stations.json").read_text(encoding="utf8"))["stations"]
SITES={"P1":"https://enptp1stationsreview20261021--englishpt-seo.netlify.app","P3":"https://enptp3guide20261021--englishpt-seo.netlify.app"}
PATHS=[("station-"+s["slug"]+"-elem-tutor.html",s) for s in ST if s["slug"]!="gukjegeumyungsenteo-busaneunhaeng"]
assert len(PATHS)==910
class Text(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.inmain=False;self.cap=None;self.parts=[];self.ps=[]
 def handle_starttag(self,t,a):
  if t=="main":self.inmain=True
  if self.inmain and self.cap is None and t in ("h1","h2","h3","p","li"):self.cap=t;self.parts=[]
 def handle_data(self,s):
  if self.inmain and self.cap:self.parts.append(s)
 def handle_endtag(self,t):
  if t==self.cap:
   p=re.sub(r"\s+"," ","".join(self.parts)).strip()
   if len(p)>=34:self.ps.append(p)
   self.cap=None
  if t=="main":self.inmain=False
def normalized(s,st):
 for x in [st["name"],st["name"].removesuffix("역"),st.get("city"),*(st.get("areas") or [])]:
  if x and len(x)>=2:s=s.replace(x,"[지역]")
 return re.sub(r"\s+"," ",s).strip()
def fetch(item):
 era,(path,st)=item;url=SITES[era]+"/"+path
 req=urllib.request.Request(url,headers={"User-Agent":"ENPT-P3-READONLY-NAV-QA/1.0"},method="GET")
 with urllib.request.urlopen(req,timeout=70) as r:
  raw=r.read(500000).decode("utf8","replace")
  assert r.status==200 and "text/html" in r.headers.get("content-type",""),path
 assert '<meta name="robots" content="index,follow' in raw,path
 assert '<link rel="canonical" href="https://englishpt.kr/'+path+'">' in raw,path
 assert 'name="englishpt-consultation"' in raw,path
 if era=="P3":
  assert raw.count('data-enpt-elemdir="20261021"')==1,path
  assert 'href="/elementary-english-guide.html"' in raw,path
  assert 'class="section mass-context"' not in raw and 'data-enpt-p0="20261021"' not in raw,path
 else:
  assert 'data-enpt-p0="20261021"' in raw,path
 p=Text();p.feed(raw)
 ps=[normalized(x,st) for x in p.ps]
 return era,path,ps,len(raw)
def robust(item):
 last=None
 for i in range(5):
  try:return fetch(item)
  except Exception as e:
   last=e;print("P3_FETCH_RETRY",item[0],item[1][0],i+1,str(e)[:90],flush=True);time.sleep(1.3*(i+1))
 raise last
items=[(era,pair) for era in SITES for pair in PATHS]
records={k:{} for k in SITES};sizes={k:{} for k in SITES}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 for i,(era,path,ps,size) in enumerate(pool.map(robust,items),1):
  records[era][path]=ps;sizes[era][path]=size
  if i%455==0:print("P3_LIVE_QA_PROGRESS",i,flush=True)
def characterize(d):
 freq=collections.Counter();groups=collections.defaultdict(list)
 for path,ls in d.items():
  freq.update(set(hashlib.sha1(s.encode()).digest() for s in ls))
  groups[hashlib.sha256("\n".join(ls).encode()).hexdigest()].append(path)
 detail={}
 for p,ls in d.items():
  chars=sum(map(len,ls))
  shared=sum(len(x) for x in ls if freq[hashlib.sha1(x.encode()).digest()]>=10)
  detail[p]={"chars":chars,"common_frac":round(shared/max(chars,1),4),"paras":len(ls),"full_hash":hashlib.sha256("\n".join(ls).encode()).hexdigest()}
 dups=sum(len(v) for v in groups.values() if len(v)>1)
 return {"urls":len(d),"avg_shared_frac":round(sum(v["common_frac"] for v in detail.values())/len(detail),4),
 "pct80_urls":sum(v["common_frac"]>=.8 for v in detail.values()),"full_normalized_duplicate_urls":dups,
 "avg_text_chars":round(sum(v["chars"] for v in detail.values())/len(detail),1)},detail
p1,before=characterize(records["P1"]);p3,after=characterize(records["P3"])
rows=[{"url":"https://englishpt.kr/"+p,"P1_chars":before[p]["chars"],"P3_chars":after[p]["chars"],
 "P1_shared_fraction":before[p]["common_frac"],"P3_shared_fraction":after[p]["common_frac"],
 "delta_shared_fraction":round(after[p]["common_frac"]-before[p]["common_frac"],4),"P3_paragraphs":after[p]["paras"],
 "P3_body_hash":after[p]["full_hash"]} for p,_ in PATHS]
with (OUT/"ALL_910_P1_VS_P3_REAL_HTML.csv").open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
guide_req=urllib.request.Request(SITES["P3"]+"/elementary-english-guide.html",method="GET")
with urllib.request.urlopen(guide_req,timeout=40) as r:
 guide=r.read(500000).decode("utf8","replace")
 assert r.status==200 and "text/html" in r.headers.get("content-type","")
 assert 'name="robots" content="noindex,follow"' in guide
 assert guide.count('id="reading"')==1 and guide.count('id="routine"')==1
summary={"status":"PASS_910_P1_P3_ACTUAL_HTML_GETONLY","P1":p1,"P3":p3,
 "mean_common_change":round(p3["avg_shared_frac"]-p1["avg_shared_frac"],4),
 "improved_urls":sum(r["delta_shared_fraction"]<0 for r in rows),
 "worsened_urls":sum(r["delta_shared_fraction"]>0 for r in rows),
 "same_urls":sum(r["delta_shared_fraction"]==0 for r in rows),
 "guide_http_200":True,"guide_noindex":True,
 "urls_fetched":len(items)+1,"forms_submitted":0,"production_publishes":0,
 "utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/"SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
print("P3_910_LIVE_COMPARE_FINAL",json.dumps(summary,ensure_ascii=False),flush=True)
