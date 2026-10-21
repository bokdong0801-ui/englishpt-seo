#!/usr/bin/env python3
"""Source-original against live nonpublished P0 Draft: ALL 906 hubs+910 elementary."""
import concurrent.futures,csv,datetime,hashlib,html,json,os,pathlib,re,subprocess,tarfile,time
from collections import Counter,defaultdict
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=pathlib.Path("p2-1816-before-after-readonly");OUT.mkdir(exist_ok=True)
SRC=pathlib.Path("frozen-source/ENGLISHPT_v23.5.2.1_SHARDED_EDGE_NEW_CANDIDATE_NOT_DEPLOYED.tar.zst")
BASE="https://enptp2englodamreview20261021--englishpt-seo.netlify.app"
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
EXPECTED_DRAFT="6ad8210ee66d91af1613dae4"
EXPECTED_PROD="6ad7506cdeb778280a54ee2a"
SOURCE_SHA256="e27ffd3e94687e0f2fc58c3951ee1262bca8fd22bd684cf7b4bdb62d014326b1"
ALL=json.loads((ROOT/"data/stations.json").read_text("utf8"))["stations"]
OMIT_HUB={"incheonairport-t1","busandaeyangsankaempeoseu","gukjegeumyungsenteo-busaneunhaeng","toseong","bokhammunhwayunghapdanji"}
OMIT_ELEM={"gukjegeumyungsenteo-busaneunhaeng"}
wanted={}
for st in ALL:
 for kind,omit in (("hub",OMIT_HUB),("elem-tutor",OMIT_ELEM)):
  if st["slug"] in omit:continue
  base="station-"+st["slug"]+("-elem-tutor" if kind=="elem-tutor" else "")+".html"
  wanted[base]=(st,kind)
assert len(wanted)==1816 and len([v for v in wanted.values() if v[1]=="hub"])==906
def http_json(path):
 import urllib.request
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"]},method="GET")
 with urllib.request.urlopen(req,timeout=30) as f:return json.load(f)
def preflight():
 site=http_json("sites/"+SITE)
 draft=http_json("sites/"+SITE+"/deploys/"+EXPECTED_DRAFT)
 assert (site.get("published_deploy") or {}).get("id")==EXPECTED_PROD
 assert draft.get("state")=="ready" and not draft.get("published_at"),(draft.get("state"),draft.get("published_at"))
 class Parse(HTMLParser):
  def __init__(self):super().__init__(convert_charrefs=True);self.main=False;self.capture=0;self.buf=[];self.ps=[];self.skip=0
  def handle_starttag(self,tag,attrs):
   if tag=="main":self.main=True
   if tag in ("script","style"):self.skip+=1
   if self.main and not self.skip and tag in ("p","h2","h3","li") and not self.capture:self.capture=1;self.buf=[]
  def handle_data(self,data):
   if self.main and self.capture and not self.skip:self.buf.append(data)
  def handle_endtag(self,tag):
   if self.capture and tag in ("p","h2","h3","li"):
    v=re.sub(r"\s+"," ","".join(self.buf)).strip()
    if len(v)>=34:self.ps.append(v)
    self.capture=0
   if tag in ("script","style") and self.skip:self.skip-=1
   if tag=="main":self.main=False
 def normalize(s,st):
  for z in [st["name"],st["name"].removesuffix("역"),st.get("city"),*(st.get("areas") or [])]:
   if z and len(z)>=2:s=s.replace(z,"[지역]")
  return re.sub(r"\s+"," ",s).strip()
 def stats(raw,st):
  p=Parse();p.feed(raw)
  ps=[normalize(x,st) for x in p.ps]
  h=[hashlib.sha256(x.encode()).hexdigest() for x in ps]
  return {"ps":ps,"hashes":h,"chars":sum(map(len,ps)),"fullsha":hashlib.sha256("\n".join(ps).encode()).hexdigest()}
 return Parse,normalize,stats
_,_,stats=preflight()
# Exact original bytes from immutable source, not code-regenerated variants.
assert SRC.exists()
sha=hashlib.sha256()
with SRC.open("rb") as f:
 for block in iter(lambda:f.read(8*1024*1024),b""):sha.update(block)
assert sha.hexdigest()==SOURCE_SHA256
original={}
p=subprocess.Popen(["zstd","-dc",str(SRC)],stdout=subprocess.PIPE)
with tarfile.open(fileobj=p.stdout,mode="r|") as tar:
 for member in tar:
  if not member.isfile():continue
  basename=pathlib.PurePosixPath(member.name).name
  if basename in wanted:
   assert basename not in original,basename
   old=tar.extractfile(member).read()
   original[basename]={"text":old.decode("utf8","replace"),"stats":stats(old.decode("utf8","replace"),wanted[basename][0])}
p.stdout.close()
assert p.wait()==0 and set(original)==set(wanted),("missing",len(set(wanted)-set(original)))
print("P0_BEFORE_SOURCE_1816_VERIFIED",len(original),flush=True)
# Use real public HTTP from nonpublished deploy, GET only.
def fetch(item):
 path,(st,kind)=item
 import urllib.request
 url=BASE+"/"+path;err=""
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"ENPT-P0-SEO-CONTENT-GET-ONLY/1.0","Cache-Control":"no-cache"},method="GET")
   with urllib.request.urlopen(req,timeout=35) as resp:
    raw=resp.read(3_000_000).decode("utf8","replace")
    assert resp.status==200 and "text/html" in resp.headers.get("content-type",""),"HTTP_MIME"
    assert resp.geturl().startswith(BASE),"cross_host"
   assert raw.count('data-enpt-p0="20261021"')==1,"P0_MARKER"
   assert '<link rel="canonical" href="https://englishpt.kr/'+path+'">' in raw,"CANONICAL"
   assert 'name="englishpt-consultation"' in raw,"FORM"
   assert '<meta name="robots" content="index,follow' in raw,"INDEX_ROBOTS"
   assert 'property="og:image"' in raw,"OG"
   return path,{"text":raw,"stats":stats(raw,st)},None
  except Exception as e:
   err=type(e).__name__+":"+str(e)[:130];time.sleep(.5*(attempt+1))
 return path,None,err
after={};failed={}
with concurrent.futures.ThreadPoolExecutor(max_workers=14) as pool:
 for i,(path,rec,error) in enumerate(pool.map(fetch,wanted.items()),1):
  if error:failed[path]=error
  else:after[path]=rec
  if i%300==0:print("P0_LIVE_DRAFT_GET_PROGRESS",i,len(after),len(failed),flush=True)
(OUT/"FETCH_ERRORS.json").write_text(json.dumps(failed,ensure_ascii=False,indent=2),encoding="utf8")
assert not failed and set(after)==set(wanted),("Live Draft misses",len(failed))
print("P0_AFTER_LIVE_DRAFT_1816_VERIFIED",len(after),flush=True)
def group_metrics(data,kind):
 names=[k for k,v in wanted.items() if v[1]==kind]
 counts=Counter()
 for n in names:counts.update(set(data[n]["stats"]["hashes"]))
 hashes=defaultdict(list)
 for n in names:hashes[data[n]["stats"]["fullsha"]].append(n)
 duplicates=[grp for grp in hashes.values() if len(grp)>1]
 allrows={}
 for name in names:
  rec=data[name]["stats"]
  total=rec["chars"]
  freqchars=sum(len(p) for p,h in zip(rec["ps"],rec["hashes"]) if counts[h]>=10)
  allrows[name]={"chars":total,"paragraphs":len(rec["ps"]),"shared_chars_fraction":round(freqchars/max(1,total),4),"normalized_sha":rec["fullsha"],"exact_dup_group_size":len(hashes[rec["fullsha"]])}
 return {"url_count":len(names),"unique_normalized_bodies":len(hashes),"normalized_duplicate_url_count":sum(len(g) for g in duplicates),"normalized_duplicate_groups":len(duplicates),"shared_chars_average":round(sum(r["shared_chars_fraction"] for r in allrows.values())/len(allrows),4),"shared_chars_p90":round(sorted(r["shared_chars_fraction"] for r in allrows.values())[int(len(allrows)*.9)],4)},allrows
summary={"status":"PASS_1816_LIVE_DRAFT_BEFORE_AFTER_GETONLY","checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"source_sha256":SOURCE_SHA256,"draft_id":EXPECTED_DRAFT,"published_original":EXPECTED_PROD,"compared":1816,"groups":{},"writes":0,"form_POSTs":0}
rows=[]
for kind in ("hub","elem-tutor"):
 before,brow=group_metrics(original,kind);aft,arow=group_metrics(after,kind)
 summary["groups"][kind]={"before":before,"after":aft,"duplicate_url_delta":aft["normalized_duplicate_url_count"]-before["normalized_duplicate_url_count"],"average_shared_fraction_change":round(aft["shared_chars_average"]-before["shared_chars_average"],4)}
 for k in brow:
  b=brow[k];a=arow[k]
  rows.append({"URL":"https://englishpt.kr/"+k,"group":kind,"before_chars":b["chars"],"after_chars":a["chars"],"added_chars":a["chars"]-b["chars"],"before_exact_dup_size":b["exact_dup_group_size"],"after_exact_dup_size":a["exact_dup_group_size"],"before_common_fraction":b["shared_chars_fraction"],"after_common_fraction":a["shared_chars_fraction"],"before_paragraphs":b["paragraphs"],"after_paragraphs":a["paragraphs"],"issue":"REVIEW_STILL_DUPLICATED" if a["exact_dup_group_size"]>1 else ("REVIEW_COMMON_OVER_80PCT" if a["shared_chars_fraction"]>=.8 else "SCREEN_PASS")})
summary["issues"]=dict(Counter(r["issue"] for r in rows))
with (OUT/"ALL_1816_BEFORE_AFTER.csv").open("w",newline="",encoding="utf-8-sig") as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
with (OUT/"REMAINING_RISK_URLS_ONLY.csv").open("w",newline="",encoding="utf-8-sig") as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows([r for r in rows if r["issue"]!="SCREEN_PASS"])
(OUT/"COMPARISON_SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
print("P0_1816_BEFORE_AFTER_RESULT",json.dumps(summary,ensure_ascii=False),flush=True)
# This is a measurement, not a policy decision; do not fail solely because duplicates remain.
