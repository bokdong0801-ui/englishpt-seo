#!/usr/bin/env python3
# coding: utf-8
"""Resume from Netlify's IMMUTABLE initial required-SHA snapshot, not empty required after partial PUT.

Only existing nonpublished Draft 6ad708...; no images, no new deploy, no Production publish.
One SHA file is sent once, at most BATCH_SIZE; checkpoint each 25 responses.
"""
import csv,gzip,hashlib,json,os,pathlib,sys,urllib.request,urllib.parse,concurrent.futures,datetime,threading,time
ROOT=pathlib.Path.cwd()
sys.path.insert(0,str(ROOT/'scripts'))
import ENPT_21964_ASYNC_DRAFT_REQUIRED_SHA_BOUNDED_FIRST_BATCH as base
OUT=ROOT/'resumable-sha-evidence';OUT.mkdir(exist_ok=True)
SRC=ROOT/'resumable-original'
DRAFT='6ad708da374d457504481d5c'
MARKER='ENPT-21964-OG-ASYNC-DIGEST-ONE-DRAFT-NOT-PRODUCTION-20261020'
SITE='98d96cc5-f0b7-4d3d-8072-6476d93e55a3'
PROD='6ad5eb4918f9411c4d5e1ba4'
BATCH=int(os.environ.get('BATCH_SIZE','1000'))
if not (1<=BATCH<=1500):raise SystemExit('HOLD: no more than 1500 files per run')
def write(name,record):
 (OUT/name).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('ENPT_RESUME_BATCH_STATE',name,json.dumps({k:v for k,v in record.items() if k not in ('completed','failed','ambiguous')},ensure_ascii=False)[:2000],flush=True)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def h(data):return hashlib.sha1(data).hexdigest()
def guard():
 x=base.get('sites/'+SITE)
 d=base.get('sites/'+SITE+'/deploys/'+DRAFT)
 if x.get('id')!=SITE or x.get('custom_domain')!='englishpt.kr' or (x.get('published_deploy') or {}).get('id')!=PROD:
  raise ValueError('Production drift; STOP')
 if d.get('site_id')!=SITE or d.get('id')!=DRAFT or d.get('title')!=MARKER or d.get('published_at') is not None or d.get('draft') is False:
  raise ValueError('Draft identity or publish changed; STOP')
 if d.get('state') not in ('prepared','uploading'):
  raise ValueError('Draft state not eligible for further one-time file SHA PUT: '+str(d.get('state')))
 return d
def find_one(top,name):
 a=list(pathlib.Path(top).rglob(name))
 if len(a)!=1:raise ValueError('Expected exactly one '+name+' inside '+top+'; found '+str(len(a)))
 return a[0]
def ledger_select():
 d=guard()
 all_file=find_one('required-snapshot','REQUIRED_SHA_TO_PATHS.csv')
 rows=list(csv.DictReader(all_file.open(encoding='utf-8-sig',newline='')))
 if len(rows)!=20600 or len({r['required_sha1'] for r in rows})!=20600:
  raise ValueError('Initial required SHA1 snapshot not full 20600')
 initial=find_one('first200-snapshot','03_BATCH_SHA_PUT_CHECKPOINT.json')
 first=json.loads(initial.read_text('utf8'))
 done=first['completed_files']
 if first['status']!='PASS_ALL_REQUESTED_FIRST_BATCH_UPLOAD_HTTP' or len(done)!=200 or first['verified_http_PUTs']!=200 or first['unknown_status_PUTs'] or first['failed_PUTs']:
  raise ValueError('First 200 proof not signed PASS')
 done_set={x['sha'] for x in done}
 if len(done_set)!=200:raise ValueError('Duplicate first200 SHA')
 original={r['required_sha1']:r['url_path'].lstrip('/') for r in rows}
 if any(x not in original for x in done_set):raise ValueError('Previously uploaded SHA absent from original initial required snapshot')
 pending=[(r['url_path'].lstrip('/'),r['required_sha1']) for r in rows if r['required_sha1'] not in done_set]
 if len(pending)!=20400:raise ValueError('Expected 20400 remaining, got '+str(len(pending)))
 batch=pending[:BATCH]
 for p,sha in batch:
  if not p.startswith('__pages/') or not p.endswith('.page'):
   raise ValueError('Only indexed physical SEO pages may be uploaded now: '+p)
 digest=find_one('prior-digest','FULL_202765_STATIC_SHA1_DIGEST.json.gz')
 with gzip.open(digest,'rt',encoding='utf8') as f:sha_paths=json.load(f)
 if len(sha_paths)!=202765:raise ValueError('Signed static SHA manifest changed')
 for p,sha in batch:
  if sha_paths.get('/'+p)!=sha:raise ValueError('SHA1/path not in original initial digest '+p)
 (OUT/'WANTED_ORIGINAL_PATHS.txt').write_text(''.join(p+'\n' for p,_ in batch),encoding='utf8')
 (OUT/'BATCH_SHA_LIST.json').write_text(json.dumps([{'path':p,'sha1':s} for p,s in batch],ensure_ascii=False,indent=2),encoding='utf8')
 r={'timestamp':now(),'status':'PASS_INITIAL_NETLIFY_DIFF_LEDGER_SELECTED',
  'original_required_sha':len(rows),'previously_HTTP200_verified':len(done_set),
  'outstanding_from_original_snapshot':len(pending),
  'chosen_batch_count':len(batch),'ready_after_this_if_all_complete':False,
  'published_id_verified':PROD,'existing_Draft_id':DRAFT,
  'current_state':d.get('state'),'currently_returned_required_length':len(d.get('required') or []),
  'new_netlify_deploy_POSTs':0,'images_uploaded':0,'production_publish_attempts':0}
 write('01_IMMUTABLE_REQUIRED_SHA_BATCH_PLAN.json',r)
 return batch,sha_paths
def reconstruct(pairs):
 if not SRC.exists():raise ValueError('Original files not extracted')
 mapp=find_one('signed-route-map','ALL_21964_INDEXABLE_THUMBNAIL_MAP.csv')
 rows={r['source_edge_path']:r for r in csv.DictReader(mapp.open(encoding='utf-8-sig',newline=''))}
 if len(rows)!=21964:raise ValueError('Indexed mapping must be 21964')
 signed=find_one('signed-qa-map','NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz')
 with gzip.open(signed,'rt',encoding='utf8') as f:orig=json.load(f)['original_public_html_to_data_payload']
 if len(orig)!=158571:raise ValueError('Sharded original routes not 158571')
 cache={}
 total=0
 for p,sha in pairs:
  row=rows.get(p)
  if row is None:raise ValueError('Requested source not in indexed map '+p)
  doc=orig.get(row['route'])
  if not doc or doc['noindex'] or doc['to']!=p:raise ValueError('noindex or route mapping changed '+p)
  original=(SRC/p).read_bytes()
  if h(original)!=row['source_page_sha1'] or h(original)!=doc['sha1']:
   raise ValueError('Original signed Edge page SHA1 mismatch '+p)
  modified=base.patch_img(original,row)
  if h(modified)!=sha:raise ValueError('Exact planned og:image patched SHA mismatch '+p)
  cache[p]=(sha,modified)
  total+=len(modified)
 if total>55000000:
  raise ValueError('Batch >55MB safety cap')
 status={'timestamp':now(),'status':'PASS_REBUILT_REQUESTED_PAGE_BYTES_SHA1',
    'selected':len(pairs),'bytes':total,'indexed_source_verification':True,'images_uploaded':0,
    'netlify_deploys_created':0,'published_production_changed':False}
 write('02_VERIFIED_RECONSTRUCTION_QA.json',status)
 return cache
def send(pairs):
 d=guard()
 result={'timestamp':now(),'status':'HOLD',
  'target_existing_Draft':DRAFT,'attempted':0,'http_success':0,
  'ambiguous':[],'failed':[],'completed':[],
  'bytes_sent':0,'new_draft_posts':0,'production_changes':0,'image_puts':0}
 write('03_RESUMABLE_PUT_PROGRESS.json',result)
 token=os.environ.get('NETLIFY_AUTH_TOKEN')
 if not token:raise ValueError('No token')
 def fn(item):
  rel,(sha,body)=item
  req=urllib.request.Request('https://api.netlify.com/api/v1/deploys/'+DRAFT+'/files/'+urllib.parse.quote(rel,safe='/'),
    method='PUT',data=body,headers={'Authorization':'Bearer '+token,'Content-Type':'application/octet-stream'})
  try:
   with urllib.request.urlopen(req,timeout=50) as response:
    code=response.status
    response.read(150)
   return rel,sha,code,None
  except Exception as e:return rel,sha,None,str(e)[:200]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
  futures=[executor.submit(fn,item) for item in pairs.items()]
  for f in concurrent.futures.as_completed(futures):
   rel,sha,code,error=f.result()
   result['attempted']+=1;result['bytes_sent']+=len(pairs[rel][1])
   if error:result['ambiguous'].append({'path':rel,'sha':sha,'error':error})
   elif code not in (200,201,202,204):result['failed'].append({'path':rel,'sha':sha,'http':code})
   else:
    result['http_success']+=1
    result['completed'].append({'path':rel,'sha':sha})
   if result['attempted']%25==0 or result['attempted']==len(pairs):
    write('03_RESUMABLE_PUT_PROGRESS.json',result)
 if result['ambiguous'] or result['failed']:
  result['status']='HOLD_PARTIAL_OR_UNCERTAIN_UPLOAD_DO_NOT_REPEAT'
 else:result['status']='PASS_NEXT_BATCH_ALL_REQUIRED_SHA_ACCEPTED'
 write('03_RESUMABLE_PUT_PROGRESS.json',result)
 latest=guard()
 result['state_after']=latest.get('state')
 result['current_API_required_count_after']=len(latest.get('required') or [])
 result['remaining_from_original_snapshot_estimate']=20400-len(result['completed'])
 result['needs_followup_batch']=result['remaining_from_original_snapshot_estimate']>0
 write('04_POST_BATCH_PUBLISHED_UNCHANGED.json',result)
 if result['status'].startswith('HOLD_'):raise SystemExit('HOLD; no ambiguous retries')
if __name__=='__main__':
 mode=sys.argv[1] if len(sys.argv)>1 else 'select'
 if mode=='select':ledger_select()
 elif mode=='upload':
  a,b=ledger_select()
  send(reconstruct(a))
 else:raise ValueError('Invalid mode')
