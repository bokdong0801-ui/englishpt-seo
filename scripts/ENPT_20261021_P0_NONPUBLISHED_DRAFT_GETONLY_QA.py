#!/usr/bin/env python3
"""GET-only QA: verify new P0 sections live on nonpublished alias, and production remains unchanged."""
import concurrent.futures,datetime,json,os,re,urllib.request,urllib.error,pathlib,hashlib
from html.parser import HTMLParser
BASE="https://enptp01816review20261021--englishpt-seo.netlify.app"
PROD="https://englishpt.kr"
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
DRAFT="6ad80ed015411e9a053bfd2d"
PUBLISHED="6ad7506cdeb778280a54ee2a"
OUT=pathlib.Path("p0-draft-live-readonly-qa");OUT.mkdir(exist_ok=True)
def api(path):
 req=urllib.request.Request("https://api.netlify.com/api/v1/"+path,headers={"Authorization":"Bearer "+os.environ["NETLIFY_AUTH_TOKEN"]},method="GET")
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def get(base,path):
 req=urllib.request.Request(base+path,headers={"User-Agent":"ENPT-P0-READONLY-VERIFY/1","Cache-Control":"no-cache"},method="GET")
 with urllib.request.urlopen(req,timeout=40) as r:
  body=r.read(3_000_000);return r.status,body.decode("utf8","replace"),r.headers.get("content-type",""),r.geturl()
site=api("sites/"+SITE);assert (site.get("published_deploy") or {}).get("id")==PUBLISHED
d=api("sites/"+SITE+"/deploys/"+DRAFT)
assert d["state"]=="ready" and d.get("published_at") is None,(d.get("state"),d.get("published_at"))
stations=json.loads(pathlib.Path("data/stations.json").read_text("utf8"))["stations"]
omit_hub={"incheonairport-t1","busandaeyangsankaempeoseu","gukjegeumyungsenteo-busaneunhaeng","toseong","bokhammunhwayunghapdanji"}
omit_elem={"gukjegeumyungsenteo-busaneunhaeng"}
slugs=[s["slug"] for s in stations]
selected=[slugs[i] for i in sorted(set([0,1,2,3,4,5,7,10,30,50,100,150,200,300,400,500,600,700,800,900,910]))]
checks=[("station-"+slug+("-elem-tutor" if kind=="elem" else "")+".html",slug,kind) for slug in selected for kind,omit in [("hub",omit_hub),("elem",omit_elem)] if slug not in omit]
def check(t):
 path,slug,kind=t
 try:
  status,html,ctype,final=get(BASE,"/"+path)
  expected="https://englishpt.kr/"+path
  errors=[]
  if status!=200 or not ctype.startswith("text/html") or not final.startswith(BASE):errors.append("HTTP/type")
  if html.count('data-enpt-p0="20261021"')!=1:errors.append("patch_marker_missing_or_duplicate")
  if '<link rel="canonical" href="'+expected+'">' not in html:errors.append("canonical")
  if 'property="og:image"' not in html:errors.append("og")
  if '<meta name="robots" content="index,follow' not in html:errors.append("robots_index")
  if 'name="englishpt-consultation"' not in html:errors.append("consultation_form")
  if html.count('</main>')!=1:errors.append("main")
  return {"path":path,"kind":kind,"status":status,"bytes":len(html.encode()),"sha256":hashlib.sha256(html.encode()).hexdigest(),"errors":errors}
 except Exception as e:return {"path":path,"kind":kind,"status":0,"errors":[type(e).__name__+":"+str(e)[:100]]}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(check,checks))
p0errors=[r for r in rows if r["errors"]]
production_checks=[]
for path in ("/station-ganeung.html","/station-ganeung-elem-tutor.html"):
 try:
  code,body,ctype,_=get(PROD,path)
  production_checks.append({"path":path,"HTTP":code,"no_p0_marker":'data-enpt-p0="20261021"' not in body,"canonical_present":'rel="canonical"' in body})
 except Exception as e:production_checks.append({"path":path,"error":str(e)[:150]})
finalsite=api("sites/"+SITE)
passed=not p0errors and all(x.get("HTTP")==200 and x.get("no_p0_marker") for x in production_checks) and (finalsite.get("published_deploy") or {}).get("id")==PUBLISHED
result={"checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"status":"PASS_P0_1816_DRAFT_LIVE_PATCHED_SAMPLES_PROD_UNCHANGED" if passed else "HOLD_P0_DRAFT_LIVE_QA","draft_id":DRAFT,"draft_alias":BASE,"production_id_unchanged":PUBLISHED if (finalsite.get("published_deploy") or {}).get("id")==PUBLISHED else None,"all_1816_source_qa_passed_in_prior_run":True,"sampled_modified_html":len(checks),"issues":p0errors,"production_checks":production_checks,"rows":rows,"writes":0,"form_POSTs":0}
(OUT/"P0_LIVE_DRAFT_SAMPLE_QA.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
print("P0_READONLY_LIVE_DRAFT_QA",json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False),flush=True)
if not passed:raise SystemExit(1)
