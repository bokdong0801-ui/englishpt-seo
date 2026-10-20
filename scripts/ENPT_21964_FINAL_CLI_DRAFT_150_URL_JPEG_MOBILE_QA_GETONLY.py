#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GET-only QA of final corrected nonpublished CLI full site.
Test 150 independently mapped routes and actual JPEGs, no form POST / Netlify upload.
"""
import csv,datetime,hashlib,io,json,os,pathlib,re,subprocess,concurrent.futures,urllib.request,urllib.error
from PIL import Image,ImageDraw
root=pathlib.Path.cwd()
out=root/'og21964-final-live-qa'
out.mkdir(exist_ok=True)
source=root/'signed-route-map'
ledger=root/'all-jpeg-qa'
BASE='https://enptog21964clifinalqa20--englishpt-seo.netlify.app'
DRAFT='6ad727......'  # dynamic matched via Netlify title; never trust an imagined ID
SITE='98d96cc5-f0b7-4d3d-8072-6476d93e55a3'
PROD='6ad5eb4918f9411c4d5e1ba4'
MARKER='ENPT-21964-FINAL-CLI-BUNDLE-SEO-HEADER-ROBOTS-FIX-DRAFT-ONLY-20261020'
token=os.environ['NETLIFY_AUTH_TOKEN']
def api(path):
 req=urllib.request.Request('https://api.netlify.com/api/v1/'+path,headers={'Authorization':'Bearer '+token},method='GET')
 with urllib.request.urlopen(req,timeout=30) as resp:return json.load(resp)
site=api('sites/'+SITE)
assert site['id']==SITE and site['custom_domain']=='englishpt.kr'
assert site['published_deploy']['id']==PROD
ds=api('sites/'+SITE+'/deploys?per_page=100')
matching=[x for x in ds if x.get('title')==MARKER]
assert len(matching)==1 and matching[0]['state']=='ready' and matching[0].get('published_at') is None
d=matching[0]
records=json.loads((source/'PILOT_150_IMAGE_ROWS.json').read_text('utf8'))
assert len(records)==150
with (source/'ALL_21964_INDEXABLE_THUMBNAIL_MAP.csv').open(encoding='utf-8-sig',newline='') as f:
 rows={x['route']:x for x in csv.DictReader(f)}
with (ledger/'ALL21964_IMAGE_HASH_AND_URL.csv').open(encoding='utf-8-sig',newline='') as f:
 hashes={x['url_path']:x for x in csv.DictReader(f)}
assert len(rows)==len(hashes)==21964
assert len({x['route'] for x in records})==150
def get(url, attempt=0):
 req=urllib.request.Request(url,method='GET',headers={'User-Agent':'ENPT-Og21964-final-GETONLY-QA'})
 try:
  with urllib.request.urlopen(req,timeout=38) as resp:
   if resp.status!=200 or not resp.geturl().startswith(BASE):
    raise ValueError('Wrong status or host '+url)
   return resp.read(1000000),{k.lower():v for k,v in resp.headers.items()}
 except (TimeoutError,urllib.error.URLError) as e:
  if attempt<2:return get(url,attempt+1)
  raise
def verify(record):
 route=record['route'];item=rows[route];expected=hashes[route]
 assert item['indexable']=='TRUE' and item['mapping_status']=='READY_METADATA_ONLY'
 data,headers=get(BASE+'/'+route)
 assert 'noindex' in headers.get('x-robots-tag','').lower(),('Preview noindex header missing',route)
 assert b'meta name="google-site-verification"' in data or route!='englishpt.html'
 assert b'meta name="naver-site-verification"' in data or route!='englishpt.html'
 og='<meta property="og:image" content="'+item['planned_og_image_url']+'">'
 assert data.count(og.encode('utf8'))==1,(route,'og:image unique mismatch')
 assert b'meta property="og:image:width" content="1200"' in data
 assert b'meta property="og:image:height" content="1200"' in data
 assert item['search_keyword'].replace(' ','').encode('utf8') not in b'X-DO-NOT-CHECK'  # mapping row guard only
 assert b'<link rel="canonical"' in data or b'rel="canonical"' in data
 raw,ih=get(BASE+'/'+item['planned_image_path'])
 if not ih.get('content-type','').lower().startswith('image/jpeg'):raise ValueError('JPEG mime mismatch '+route)
 if hashlib.sha256(raw).hexdigest()!=expected['sha256']:raise ValueError('Original JPEG SHA mismatch '+route)
 with Image.open(io.BytesIO(raw)) as im:
  im.load()
  assert im.size==(1200,1200) and im.format=='JPEG'
 return {'route':route,'bytes_html':len(data),'bytes_img':len(raw),'jpeg_sha256':expected['sha256'],
  'image_path':item['planned_image_path'],'category':item['category'],
  'header':item['header_label'],'keyword':item['search_keyword']},raw
result={'status':'HOLD','draft_id':d['id'],'preview_url':BASE,'qa_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'published_production_id':PROD,'production_changed':False,'draft_published':False,
  'netlify_mutations':0,'image_qa':0,'html_qa':0,'errors':[],'mobile_sizes':[102,156,200],
  'image_original_sha256_matches':0}
passed=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 futures={pool.submit(verify,rec):rec['route'] for rec in records}
 for f in concurrent.futures.as_completed(futures):
  try:passed.append(f.result())
  except Exception as exc:result['errors'].append(futures[f]+': '+type(exc).__name__+': '+str(exc)[:180])
passed.sort(key=lambda x:x[0]['route'])
result['image_qa']=result['html_qa']=result['image_original_sha256_matches']=len(passed)
result['category_distribution']={}
for r,raw in passed:
 result['category_distribution'][r['category']]=result['category_distribution'].get(r['category'],0)+1
# Test homepage and index HTTP ownership + X-Robots, and ensure robots lines are separated.
for path in ('/index.html','/englishpt.html','/robots.txt','/sitemap-index.xml','/__pages/23/englishpt.page'):
 try:
  b,h=get(BASE+path)
  result['status_'+path]={'bytes':len(b),'content_type':h.get('content-type'),'x_robots':h.get('x-robots-tag','')}
  if path.endswith('.html'):
   if 'noindex' not in h.get('x-robots-tag','').lower():raise ValueError('Preview root HTML indexable: '+path)
   if b.count(b'google-site-verification')!=1 or b.count(b'naver-site-verification')!=1:
    raise ValueError('Owner tag mismatch '+path)
  if path=='/robots.txt':
   assert b.decode('utf8').splitlines()==['User-agent: *','Disallow: /'],('robots.txt malformed',b[:60])
 except Exception as e:result['errors'].append('ROOT '+path+': '+str(e)[:180])
# Crop 30 verified actual images to 102px and 156px and save visible contact sheets.
if len(passed)>=30:
 for size in (102,156):
  cols=6;cellw=188;cellh=222
  sheet=Image.new('RGB',(cols*cellw,5*cellh),'#F4F6F3');pen=ImageDraw.Draw(sheet)
  for i,(record,raw) in enumerate(passed[:30]):
   with Image.open(io.BytesIO(raw)) as im:
    thumb=im.convert('RGB').resize((size,size),Image.Resampling.LANCZOS)
   x=(i%cols)*cellw+6;y=(i//cols)*cellh+6
   sheet.paste(thumb,(x,y))
   pen.text((x,y+165),record['header']+' '+record['keyword'][:12],fill='#2c3935')
  sheet.save(out/('LIVE_30_OG_THUMBNAILS_'+str(size)+'PX.jpg'),quality=90)
# Real 390px Chrome browser screenshot for home and one student or TOEIC route
chrome='/usr/bin/google-chrome'
if pathlib.Path(chrome).exists():
 for uri,filename in [('/englishpt.html','MOBILE_390PX_ENGLISHPT_HOME.png'),
                      ('/'+(passed[0][0]['route'] if passed else 'englishpt.html'),'MOBILE_390PX_SAMPLE_SEO_PAGE.png')]:
  p=subprocess.run([chrome,'--headless=new','--no-sandbox','--disable-dev-shm-usage',
    '--disable-gpu','--hide-scrollbars','--window-size=390,844','--virtual-time-budget=2400',
    '--screenshot='+str(out/filename),BASE+uri],capture_output=True,timeout=45)
  result[filename]='PASS' if p.returncode==0 and (out/filename).is_file() else 'HOLD_SCREENSHOT_UNAVAILABLE'
else:result['browser_screenshot']='HOLD_CHROME_NOT_AVAILABLE'
result['status']='PASS_FINAL_DRAFT_150_LIVE_HTTP_JPEG_SHA_SEO_NOIDX' if len(passed)==150 and not result['errors'] else 'HOLD_FINAL_DRAFT_QA_NEEDS_FIX'
(out/'FINAL_150_LIVE_FULL_DRAFT_PAGE_IMAGE_MOBILE_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('ENPT_FINAL_21964_LIVE_150_SAMPLE_FULL_QA',json.dumps(result,ensure_ascii=False)[:19000],flush=True)
if result['status'].startswith('HOLD'):raise SystemExit(1)
