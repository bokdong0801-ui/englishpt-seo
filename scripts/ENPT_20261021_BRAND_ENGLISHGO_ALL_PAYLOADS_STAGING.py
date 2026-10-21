#!/usr/bin/env python3
# coding:utf-8
"""Stage ENGLISH GO rebrand on the exact signed, pre-PROD candidate. NO production publish.
All 158571 generated HTML payloads + public static HTML + brand-text SVG.
Protect domain, canonical URLs, robots, verification, forms, Edge, redirects & sitemaps.
"""
import os,hashlib,json,pathlib,re,datetime,collections,gzip
ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/"thumb-21964-candidate"
OUT=ROOT/"brand-englishgo-qa";OUT.mkdir(exist_ok=True)
assert SITE.is_dir()
with gzip.open(ROOT/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz","rt",encoding="utf8") as f:
 signed=json.load(f)["original_public_html_to_data_payload"]
assert len(signed)==158571
home_path=SITE/signed["englishpt.html"]["to"]
assert home_path.is_file()
OLD_KO="잉글리시PT";OLD_EN="ENGLISH PT"
NEW_KO="잉글리시GO";NEW_EN="ENGLISH GO"
CHANGES=[("잉글리시PT",NEW_KO),("ENGLISH PT",NEW_EN),("English PT","English GO"),("english PT","english GO")]
STRICT_PROTECTED=["robots.txt","_headers","_redirects","netlify.toml","netlify/edge-functions/shard-router.js",
                  "sitemap-index.xml","assets/site.js","assets/locality-index.json"]
protected_before={f:hashlib.sha256((SITE/f).read_bytes()).hexdigest() for f in STRICT_PROTECTED if (SITE/f).is_file()}
assert len(protected_before)>=6
HEAD=re.compile(r"<head\b[^>]*>.*?</head>",re.I|re.S)
CANON=re.compile(r'<link\b[^>]*rel=["\']canonical["\'][^>]*>',re.I)
ROBOTS=re.compile(r'<meta\b[^>]*name=["\']robots["\'][^>]*>',re.I)
VERIFY=re.compile(r'<meta\b[^>]*name=["\'](?:google-site-verification|naver-site-verification)["\'][^>]*>',re.I)
FORM=re.compile(r'<form\b[^>]*name=["\']englishpt-consultation["\']',re.I)
LOGO=re.compile(r'(<span class="brand-mark">)PT(</span>)')
pages=0;changed=0;generated=0;old_before=collections.Counter();old_after=collections.Counter();samples=[]
def patch(raw,path):
 for t,_ in CHANGES:old_before[t]+=raw.count(t)
 new=raw
 for a,b in CHANGES:new=new.replace(a,b)
 new=LOGO.sub(r'\1GO\2',new)
 # Pinned brand marker only on homepage canonical; title & visible name controlled above.
 # OpenGraph site-name is consistent on every HTML head where any other OG tags already exist.
 if '<meta property="og:title"' in new and 'property="og:site_name"' not in new:
  new=new.replace('</head>','<meta property="og:site_name" content="'+NEW_KO+'"></head>',1)
 # Existing WebSite structured data supports a single canonical name and optional alternative.
 if path==home_path or path.name=="index.html":
  new=new.replace('"@type":"WebSite","@id"', '"@type":"WebSite","alternateName":["잉글리시GO","English GO"],"@id"',1)
 # Signature route/SEO policies MUST NEVER mutate during presentation branding.
 for rex in (CANON,ROBOTS,VERIFY,FORM):
  assert rex.findall(new)==rex.findall(raw),(str(path.relative_to(SITE)),rex.pattern)
 assert new.count('name="englishpt-consultation"')==raw.count('name="englishpt-consultation"')
 assert len(HEAD.findall(new))==len(HEAD.findall(raw))
 assert 'https://englishgo.kr/' not in new,(str(path),"accidental_domain_change")
 for t,_ in CHANGES:old_after[t]+=new.count(t)
 return new
def html_files():
 for folder,ds,fs in os.walk(SITE):
  # Skip byte-addressed thumbnail/media assets; full generated page payload is __pages/*.page.
  ds[:]=[d for d in ds if d not in ("node_modules",".git","seo-square","existing-jpegs")]
  for f in fs:
   if f.endswith(".html") or f.endswith(".page"):
    yield pathlib.Path(folder)/f
for p in html_files():
 raw=p.read_text("utf8")
 new=patch(raw,p)
 pages+=1
 if p.suffix==".page":generated+=1
 if new!=raw:
  p.write_text(new,"utf8")
  changed+=1
  if len(samples)<12:samples.append(str(p.relative_to(SITE)))
assert generated==158571,("not_exact_generated_payload_count",generated)
assert pages>=158571
assert old_before[OLD_KO]+old_before[OLD_EN]>10000,("no_site_brand_found",old_before)
assert old_after[OLD_KO]==0 and old_after[OLD_EN]==0,("old_brand_remains",old_after)
# Existing brand mark SVG is text only; retain SVG shapes/palette/geometry unchanged.
fav=SITE/"assets/favicon.svg"
if fav.is_file():
 svg=fav.read_text("utf8")
 assert ">PT</text>" in svg
 new_svg=svg.replace(">PT</text>",">GO</text>")
 assert new_svg!=svg and new_svg.count(">GO</text>")==1
 fav.write_text(new_svg,"utf8")
 assert fav.read_text("utf8").startswith("<svg")
for f,digest in protected_before.items():
 assert hashlib.sha256((SITE/f).read_bytes()).hexdigest()==digest,("protected_file_changed",f)
for route in ("englishpt.html","student-english.html","english-conversation.html","guides/senior-english.html","guides/international-school-english.html"):
 p=SITE/(signed[route]["to"] if route in signed else route)
 assert p.is_file(),route
 html=p.read_text("utf8")
 assert NEW_KO in html or NEW_EN in html,route
 assert OLD_KO not in html and OLD_EN not in html,route
 assert f'<meta property="og:site_name" content="{NEW_KO}">' in html,route
 assert 'name="englishpt-consultation"' in html,route
for route in ("englishpt.html","student-english.html"):
 raw=(SITE/route).read_text("utf8")
 assert '"name":"'+NEW_EN+'"' in raw,("schema_website_name",route)
 assert '"alternateName":["'+NEW_KO+'","English GO"]' in raw,("schema_alternate_name",route)
result={"status":"PASS_ENGLISHGO_BRAND_ALL_158571_GENERATED_PAGES_PRESERVED_SEO_AND_FORMS",
  "generated_edge_payloads":generated,"html_total":pages,"brand_changed_html":changed,
  "before":{"korean":old_before[OLD_KO],"english":old_before[OLD_EN]},
  "after":{"korean":old_after[OLD_KO],"english":old_after[OLD_EN]},
  "display_brand":NEW_KO,"roman_brand":NEW_EN,"domain_unchanged":"englishpt.kr",
  "old_site_urls_unchanged":True,"old_index_noindex_policy_unchanged":True,
  "forms_and_recipient_unchanged":True,"google_naver_verification_unchanged":True,
  "all_protected_infrastructure_files_unchanged":True,"favicon_letter_text_only":"GO",
  "registered_trademark_cleared":False,"unpublished_only":True,"production_published":False,
  "sample_file_paths":samples,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/"BRAND_ALL_SITE_REPORT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
print("ENPT_ENGLISHGO_ALL_BRAND_QA",json.dumps(result,ensure_ascii=False),flush=True)
