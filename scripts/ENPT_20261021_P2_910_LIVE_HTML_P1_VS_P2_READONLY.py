#!/usr/bin/env python3
"""Actual 910 elementary HTML from P1 and P2 unpublished Netlify aliases, GET only."""
import concurrent.futures,csv,hashlib,json,os,pathlib,re,urllib.request,collections,datetime,time
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=pathlib.Path("p2-910-draft-realhtml-qa");OUT.mkdir(exist_ok=True)
ST=json.loads((ROOT/"data/stations.json").read_text("utf8"))["stations"]
BASES={"P1":"https://enptp1stationsreview20261021--englishpt-seo.netlify.app","P2":"https://enptp2elementaryreview20261021--englishpt-seo.netlify.app"}
assert len(ST)==911
class Parser(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.inside=False;self.tag=None;self.buf=[];self.lines=[]
 def handle_starttag(self,t,a):
  if t=="main":self.inside=True
  if self.inside and self.tag is None and t in ("p","h2","h3","li"):self.tag=t;self.buf=[]
 def handle_data(self,d):
  if self.inside and self.tag:self.buf.append(d)
 def handle_endtag(self,t):
  if self.tag==t:
   s=re.sub(r"\s+"," ","".join(self.buf)).strip()
   if len(s)>=34:self.lines.append(s)
   self.tag=None
  if t=="main":self.inside=False
def normalize(text,st):
 for x in [st["name"],st["name"].removesuffix("역"),st.get("city"),*(st.get("areas") or [])]:
  if x and len(x)>=2:text=text.replace(x,"[지역]")
 return re.sub(r"\s+"," ",text).strip()
def get_one(item):
 edition,st=item
 route="station-"+st["slug"]+"-elem-tutor.html"
 url=BASES[edition]+"/"+route
 req=urllib.request.Request(url,headers={"User-Agent":"ENPT-910-GETONLY-SEO-AUDIT"},method="GET")
 with urllib.request.urlopen(req,timeout=75) as resp:
  raw=resp.read(500000).decode("utf8","replace")
  assert resp.status==200 and resp.headers.get("content-type","").startswith("text/html")
  assert 'name="englishpt-consultation"' in raw and '<meta name="robots" content="index,follow' in raw and '<link rel="canonical" href="https://englishpt.kr/' in raw
  assert ("data-enpt-elem-originality=" in raw)==(edition=="P2")
 p=Parser();p.feed(raw)
 lines=[normalize(x,st) for x in p.lines]
 return (edition,route,lines)
items=[(e,s) for e in BASES for s in ST if s["slug"]!="gukjegeumyungsenteo-busaneunhaeng"]
assert len(items)==1820
rec={e:{} for e in BASES}
def robust_get(item):
 last=None
 for attempt in range(5):
  try:return get_one(item)
  except Exception as exc:
   last=exc
   print('P2_RETRY',item[0],item[1]['slug'],attempt+1,str(exc)[:85],flush=True)
   time.sleep(1.5*(attempt+1))
 raise last
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
 for i,(edition,route,lines) in enumerate(pool.map(robust_get,items),1):
  rec[edition][route]=lines
  if i%455==0:print("P2_COMPARE_PROGRESS",i,flush=True)
def stats(d):
 count=collections.Counter()
 groups=collections.defaultdict(list)
 for r,ls in d.items():
  count.update(set(hashlib.sha1(s.encode()).digest() for s in ls))
  groups[hashlib.sha256("\n".join(ls).encode()).hexdigest()].append(r)
 details={}
 for route,lines in d.items():
  total=sum(map(len,lines));common=sum(len(s) for s in lines if count[hashlib.sha1(s.encode()).digest()]>=10)
  details[route]={"chars":total,"shared":round(common/max(total,1),4),"exact_group":len(groups[hashlib.sha256("\n".join(lines).encode()).hexdigest()])}
 duplicates=sum(len(x) for x in groups.values() if len(x)>1)
 return {"count":len(d),"normalized_exact_duplicate_urls":duplicates,"average_shared":round(sum(x["shared"] for x in details.values())/len(details),4),"80pct_or_more":sum(x["shared"]>=.8 for x in details.values())},details
b,bd=stats(rec["P1"]);a,ad=stats(rec["P2"])
rows=[{"url":"https://englishpt.kr/"+route,"P1_shared":bd[route]["shared"],"P2_shared":ad[route]["shared"],"delta":round(ad[route]["shared"]-bd[route]["shared"],4),"P1_chars":bd[route]["chars"],"P2_chars":ad[route]["chars"],"P2_dup_group":ad[route]["exact_group"]} for route in sorted(ad)]
with (OUT/"ALL_910_P1_VS_P2_REAL_HTML.csv").open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
res={"status":"PASS_BOTH_ALIASES_910_EACH_ALL_GET_200","old_P1":b,"new_P2":a,"mean_shared_fraction_change":round(a["average_shared"]-b["average_shared"],4),"improved_urls":sum(x["delta"]<0 for x in rows),"worsened_urls":sum(x["delta"]>0 for x in rows),"unchanged_urls":sum(x["delta"]==0 for x in rows),"all_1820_HTTP_200":True,"form_POSTs":0,"production_published":False,"time_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/"P2_910_COMPARE.json").write_text(json.dumps(res,ensure_ascii=False,indent=2),"utf8")
print("P2_910_OLD_NEW_RESULT",json.dumps(res,ensure_ascii=False),flush=True)
