#!/usr/bin/env python3
# coding: utf-8
"""ENPT nonpublished async-digest Draft: exact missing-SHA batched upload only.
Never creates deploy, modifies Production, or sends images. Idempotency via GET required SHA list.
"""
import collections,csv,gzip,hashlib,html,json,os,pathlib,re,sys,time,urllib.request,urllib.error,urllib.parse,concurrent.futures,datetime,threading
from pathlib import Path
ROOT=Path.cwd()
OUT=ROOT/"bounded-sha-upload-evidence"
OUT.mkdir(exist_ok=True)
SRC=ROOT/"bounded-original"
MAP=ROOT/"signed-route-map"/"ALL_21964_INDEXABLE_THUMBNAIL_MAP.csv"
SOURCES=ROOT/"signed-qa-map"/"NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
SHA=ROOT/"prior-digest"/"async-og-21964-evidence"/"FULL_202765_STATIC_SHA1_DIGEST.json.gz"
SITE_ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
DRAFT_ID="6ad708da374d457504481d5c"
PROD_ID="6ad5eb4918f9411c4d5e1ba4"
MARKER="ENPT-21964-OG-ASYNC-DIGEST-ONE-DRAFT-NOT-PRODUCTION-20261020"
HEADER_GLOBAL="\n/*\n  X-Robots-Tag: noindex, nofollow\n"
API='https://api.netlify.com/api/v1/'
IMAGE_META=re.compile(r'<meta\b(?=[^>]*(?:property|name)\s*=\s*["\x27](?:og:image(?:[:][-\w]+)?|twitter:image(?:[:][-\w]+)?|twitter:card)["\x27])[^>]*>',re.I)
HEAD=re.compile(r"<head\b[^>]*>(.*?)</head\s*>",re.I|re.S)
ROBOTS=re.compile(r'<meta\b[^>]*name=["\x27]robots["\x27][^>]*>',re.I)
CANONICAL=re.compile(r'<link\b[^>]*rel=["\x27]canonical["\x27][^>]*>',re.I)
def write(name,x):
 (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print('ENPT_BATCH_REQUIRED_SHA_AUDIT',name,json.dumps({k:v for k,v in x.items() if k not in ('completed_files','files','errors')},ensure_ascii=False)[:1800],flush=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def token():
 t=os.environ.get('NETLIFY_AUTH_TOKEN')
 if not t:raise ValueError('No Netlify credentials')
 return t
def get(p):
 req=urllib.request.Request(API+p,method='GET',headers={'Authorization':'Bearer '+token(),'Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=37) as response:return json.load(response)
def guard():
 site=get('sites/'+SITE_ID)
 d=get('sites/'+SITE_ID+'/deploys/'+DRAFT_ID)
 if (site.get('published_deploy') or {}).get('id')!=PROD_ID or site.get('custom_domain')!='englishpt.kr':
  raise ValueError('Production status changed: HOLD')
 if d.get('id')!=DRAFT_ID or d.get('site_id')!=SITE_ID or d.get('title')!=MARKER or d.get('published_at') is not None:
  raise ValueError('Draft identity changed: HOLD')
 if d.get('draft') is False:raise ValueError('Draft flag false: HOLD')
 if d.get('state') not in ('prepared','uploading','uploaded','ready'):
  raise ValueError('Invalid target Draft state: '+str(d.get('state')))
 return d
def h(x):return hashlib.sha1(x).hexdigest()
def patch_img(b,row):
 src=b.decode('utf8')
 match=HEAD.search(src)
 if not match:raise ValueError('head missing '+row['route'])
 head=match.group(1)
 before_robot=ROBOTS.search(head)
 before_can=CANONICAL.search(head)
 if not before_robot or not before_can:raise ValueError('SEO canonical/robots missing')
 url=row['planned_og_image_url']
 label=html.escape(row['header_label']+' '+row['search_keyword'],quote=True)
 payload=('<meta property="og:image" content="'+url+'">'
          '<meta property="og:image:secure_url" content="'+url+'">'
          '<meta property="og:image:type" content="image/jpeg">'
          '<meta property="og:image:width" content="1200">'
          '<meta property="og:image:height" content="1200">'
          '<meta property="og:image:alt" content="'+label+'">'
          '<meta name="twitter:card" content="summary">'
          '<meta name="twitter:image" content="'+url+'">')
 new_head=IMAGE_META.sub('',head)+payload
 if ROBOTS.search(new_head).group(0)!=before_robot.group(0) or \
    CANONICAL.search(new_head).group(0)!=before_can.group(0):
  raise ValueError('SEO metadata altered for '+row['route'])
 return (src[:match.start(1)]+new_head+src[match.end(1):]).encode('utf8')
def prepare():
 assert MAP.is_file() and SOURCES.is_file() and SHA.is_file(),'Missing signed files'
 with gzip.open(SHA,'rt',encoding='utf8') as f: sha_by_path=json.load(f)
 assert len(sha_by_path)==202765
 bysha=collections.defaultdict(list)
 for p,d in sha_by_path.items():bysha[d].append(p)
 d=guard()
 req=d.get('required') or []
 maxnum=int(os.environ.get('BATCH_SIZE','200'))
 if not(1<=maxnum<=300):raise ValueError('Unsafe batch size')
 priority=['/_headers','/netlify.toml']
 selected_sha=[]
 for p in priority:
  if p in sha_by_path and sha_by_path[p] in req:selected_sha.append(sha_by_path[p])
 for sha in sorted(req):
  if len(selected_sha)>=maxnum:break
  if sha not in selected_sha:selected_sha.append(sha)
 if len(selected_sha)>maxnum:raise ValueError('Batch oversized')
 pathsha=[]
 for sha in selected_sha:
  if sha not in bysha or len(bysha[sha])!=1:raise ValueError('Unmapped or nonunique required SHA')
  pathsha.append((bysha[sha][0].lstrip('/'),sha))
 for path,sha in pathsha:
  if not(path.startswith('__pages/') or path in ('_headers','netlify.toml')):
   raise ValueError('Unapproved required file class '+path)
 with (OUT/'WANTED_ORIGINAL_PATHS.txt').open('w',encoding='utf8') as f:
  for path,sha in pathsha:f.write(path+'\n')
 with (OUT/'WANTED_UPLOAD_SHA_PATHS.json').open('w',encoding='utf8') as f:
  json.dump([{'path':p,'sha1':s} for p,s in pathsha],f,ensure_ascii=False,indent=2)
 proof={'time_utc':now(),'status':'PASS_EXACT_200_REQUIRED_SHA_SELECTED',
   'required_before':len(req),'batch_target':len(pathsha),
   'target_url':DRAFT_ID,'production_unchanged':True,
   'draft_state':d.get('state'),'JPEGs_to_upload':0,'new_draft_POST_attempts':0,
   'no_duplicate_SHA':len(set(selected_sha))==len(selected_sha),
   'files_rewritten':0,'files_uploaded':0}
 write('01_GUARDED_WANTED_SHA_AND_ORIGINAL_PATHS.json',proof)
 return pathsha,sha_by_path
def prepare_bytes(pathsha,sha_by_path):
 if not SRC.is_dir():raise ValueError('No original extraction directory')
 rows={}
 with MAP.open(encoding='utf-8-sig',newline='') as f:
  for x in csv.DictReader(f):rows[x['source_edge_path']]=x
 if len(rows)!=21964:raise ValueError('Unexpected mapping 21964')
 with gzip.open(SOURCES,'rt',encoding='utf8') as f:signed=json.load(f)
 source=signed['original_public_html_to_data_payload']
 result={}
 fullbytes=0
 for rel,expected in pathsha:
  orig=(SRC/rel)
  if not orig.is_file():raise ValueError('Requested original source missing '+rel)
  b=orig.read_bytes()
  if rel in ('netlify.toml',):
   replacement=b
  elif rel=='_headers':
   if h(b)!=signed['target_SHA1_by_path']['_headers']:raise ValueError('Original _headers source SHA mismatched')
   replacement=b+HEADER_GLOBAL.encode('utf8')
  else:
   row=rows.get(rel)
   if row is None:raise ValueError('Required physical Edge source path not indexable '+rel)
   doc=source[row['route']]
   if doc['noindex'] or doc['to']!=rel or h(b)!=doc['sha1']:
    raise ValueError('Canonical noindex/source SHA mismatch for '+rel)
   replacement=patch_img(b,row)
  if h(replacement)!=expected:
   raise ValueError('Reconstructed actual bytes do not match proposed async digest: '+rel)
  result[rel]=(expected,replacement)
  fullbytes+=len(replacement)
 if fullbytes>18000000:raise ValueError('Safety cap exceeded, no uploading (total size)')
 qa={'checked_utc':now(),'status':'PASS_ORIGINAL_EDGE_PAGE_PATCH_BYTE_FOR_BYTE_SHA1',
     'file_count':len(result),'total_bytes':fullbytes,
     'original_source_verify':True,'destination_async_draft':DRAFT_ID,
     'published_prod_unchanged':True,'production_mutations':0,
     'all_SHA1_expected_digest_matched':True,'requested_JPEG_count':0}
 write('02_LOCAL_RECONSTRUCT_ONLY_QA.json',qa)
 return result
def upload_only(data):
 status={'date_utc':now(),'status':'HOLD','target_Draft_id':DRAFT_ID,
   'attempted_PUTs':0,'verified_http_PUTs':0,'completed_files':[],
   'unknown_status_PUTs':[],'failed_PUTs':[],'total_attempted_bytes':0,
   'prod_posts':0,'netlify_new_deploys':0}
 before=guard()
 required=set(before.get('required') or [])
 if any(expected not in required for expected,_ in data.values()):
  raise ValueError('Required SHA changed before PUT; do not blindly upload')
 write('03_BATCH_SHA_PUT_CHECKPOINT.json',status)
 lock=threading.Lock()
 def put(item):
  rel,(sha,buf)=item
  url=API+'deploys/'+DRAFT_ID+'/files/'+urllib.parse.quote(rel,safe='/')
  request=urllib.request.Request(url,data=buf,method='PUT',headers={
    'Authorization':'Bearer '+token(),'Content-Type':'application/octet-stream'})
  try:
   with urllib.request.urlopen(request,timeout=50) as resp:
    code=resp.status
    resp.read(100)
   return rel,sha,code,None
  except Exception as e:return rel,sha,None,str(e)[:250]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  future={pool.submit(put,q):q[0] for q in data.items()}
  for f in concurrent.futures.as_completed(future):
   rel,sha,code,error=f.result()
   with lock:
    status['attempted_PUTs']+=1
    status['total_attempted_bytes']+=len(data[rel][1])
    if error:
     status['unknown_status_PUTs'].append({'path':rel,'sha':sha,'error':error})
    elif code not in (200,201,202,204):
     status['failed_PUTs'].append({'path':rel,'sha':sha,'code':code})
    else:
     status['verified_http_PUTs']+=1
     status['completed_files'].append({'path':rel,'sha':sha})
    if status['attempted_PUTs']%10==0 or status['attempted_PUTs']==len(data):
     write('03_BATCH_SHA_PUT_CHECKPOINT.json',status)
 if status['unknown_status_PUTs'] or status['failed_PUTs']:
  status['status']='HOLD_PARTIAL_UPLOAD_NO_RETRY_UNCERTAIN_FILES'
 else:status['status']='PASS_ALL_REQUESTED_FIRST_BATCH_UPLOAD_HTTP'
 write('03_BATCH_SHA_PUT_CHECKPOINT.json',status)
 latest=guard()
 remaining=set(latest.get('required') or [])
 done={x['sha'] for x in status['completed_files']}
 status['required_after']=len(remaining)
 status['verified_upload_SHA_disappeared_from_required']=len(done-remaining)
 status['all_verified_uploads_removed_from_required']=not bool(done&remaining)
 status['state_after']=latest.get('state')
 if status['status'].startswith('PASS_') and done&remaining:
  status['status']='HOLD_NETLIFY_DIFF_NOT_YET_SETTLED'
 write('04_NETLIFY_REQUIRED_SHA_AFTER_BATCH_GETONLY.json',status)
 if status['status'].startswith('HOLD_'):raise SystemExit('HOLD: no retry/restart until GET reconcile')
 return status
if __name__=='__main__':
 mode=sys.argv[1] if len(sys.argv)>1 else 'select'
 if mode=='select':prepare()
 elif mode=='upload':
  paths,shas=prepare()
  data=prepare_bytes(paths,shas)
  upload_only(data)
 else:raise ValueError('unknown mode')
