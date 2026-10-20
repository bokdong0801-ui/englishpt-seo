#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ENPT 21,964-square-OG Netlify async digest, one nonpublished new draft ONLY.

Requires exact offline source QA and signed originals. Never restores or publishes.
One POST allowed only following immutable preflight. No blind retries/large bulk uploads.
"""
from __future__ import annotations
import collections
import concurrent.futures
import datetime
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"thumb-21964-candidate"
AUDIT=ROOT/"async-og-21964-evidence"
AUDIT.mkdir(parents=True,exist_ok=True)
STATIC_EXPECT=202765 # old 180800 + 21964 JPEG + 1 new Edge manifest
SOURCE_ARCHIVE_SHA="6d0272d1601a1a47abeccc4d740359af9e7678293ee0a3d257eecd2ca478d884"
SITE_ID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
PROD_ID="6ad5eb4918f9411c4d5e1ba4"
MARKER="ENPT-21964-OG-ASYNC-DIGEST-ONE-DRAFT-NOT-PRODUCTION-20261020"
TAR_SHA="1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b"
API="https://api.netlify.com/api/v1/"
MAX_ASSET_UPLOADS=250  # stop rather than retry >250 after stale Draft
MAX_ASSET_UPLOAD_BYTES=16000000 # upload at most 16 MB additional assets this pass


def now():
 return datetime.datetime.now(datetime.timezone.utc).isoformat()
def report(name,obj):
 (AUDIT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("ENPT_ASYNC_DRAFT_RESULT",name,json.dumps({k:v for k,v in obj.items() if k not in ("file_sha_map","required_sha_list")},ensure_ascii=False)[:7000],flush=True)
def hold(message):
 raise RuntimeError("HOLD: "+message)
def digest_file(path,algorithm="sha1"):
 h=hashlib.new(algorithm)
 with open(path,"rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
 return h.hexdigest()
def flags():
 return {'static_upload_limit':MAX_ASSET_UPLOADS,'upload_bytes_limit':MAX_ASSET_UPLOAD_BYTES,'no_production_publish':True,
  'old_full_stalled_Draft_reused':False,'new_deploy_draft':True,'new_deploy_async':True}
def get_token():
 t=os.environ.get('NETLIFY_AUTH_TOKEN')
 if not t:hold("Netlify credential missing")
 return t
def req_get(url):
 request=urllib.request.Request(url,headers={'Authorization':'Bearer '+get_token(),'Accept':'application/json'},method='GET')
 with urllib.request.urlopen(request,timeout=37) as response:return json.load(response)
def get(endpoint):
 return req_get(API+endpoint)
def site_and_deploy_guard(draft=None):
 site=get("sites/"+SITE_ID)
 if site.get('id')!=SITE_ID or site.get('custom_domain')!="englishpt.kr" or \
    (site.get("published_deploy") or {}).get("id")!=PROD_ID:
  hold("published Production ID drift OR site mismatch")
 if (site.get('processing_settings') or {}).get('ignore_html_forms') is not False:
  hold("Netlify Forms settings unexpectedly changed")
 if draft is not None:
  obj=get('sites/'+SITE_ID+'/deploys/'+draft)
  if obj.get('id')!=draft or obj.get('site_id')!=SITE_ID or obj.get('published_at') is not None:
   hold("Target Draft identity invalid or already published")
  if obj.get('draft') is False:hold("Netlify reports deploy draft=false")
  return site,obj
 return site,None


def preflight():
 global_root=SITE
 source=json.loads((ROOT/"thumb-draft-qa/CANDIDATE_21964_SOURCE_PRESERVATION_QA.json").read_text('utf8'))
 if source.get('status')!='PASS_DRAFT_CANDIDATE_21964_REAL_OG_LINKS_ALL_NOIDX_PRESERVED':
  hold("Existing full-site local audit not PASS")
 checks=[
 ('indexable_image_tags_added_exactly_once',21964),
 ('all_136607_noindex_edge_files_sha1_identical',136607),
 ('all_158571_SEO_urls_kept',158571),
 ('all_jpeg_images_verified_sha256_against_source',21964),
 ('new_image_count',21964),
 ('all_44_sitemap_shards_sha1_identical',44)
 ]
 for key,v in checks:
  if source.get(key)!=v:hold("Source QA mismatch "+key)
 if not source.get('both_google_naver_owner_tags_preserved'):hold('Search verification meta not preserved')
 if source.get('source_full_release_sha256')!=SOURCE_ARCHIVE_SHA:hold('signed archive mismatch')
 originals=(ROOT/'signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz')
 with gzip.open(originals,'rt',encoding='utf8') as f: signed=json.load(f)
 sha_index=signed['original_public_html_to_data_payload']
 if len(sha_index)!=158571 or sum(not z['noindex'] for z in sha_index.values())!=21964:hold("SEO original route/source count drift")
 # global Draft-only crawler shield; never pass this source to Production.
 header= (SITE/'_headers').read_text('utf8')
 if not header.endswith("\n/*\n  X-Robots-Tag: noindex, nofollow\n") or header.count("X-Robots-Tag: noindex, nofollow")!=1:
  hold("Draft-only global noindex missing or duplicated")
 original=(ROOT/'signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz')
 old_header_sha=signed['target_SHA1_by_path']['_headers']
 original_part=header.split("\n/*\n  X-Robots-Tag: noindex, nofollow\n")[0].encode('utf8')
 if hashlib.sha1(original_part).hexdigest()!=old_header_sha:hold("Original pre-Draft header content changed")
 # This explicit manifest is essential to the sharded .page routes.
 manifest_path=SITE/'.netlify/internal/edge-functions/manifest.json'
 if not manifest_path.is_file():hold("Missing CLI-shaped Netlify Edge manifest at original normalized path")
 manifest=json.loads(manifest_path.read_text('utf8'))
 if not any(r.get('function')=='shard-router' and r.get('pattern')=='^/[^/]+[.]html$' for r in manifest.get('routes',[])):
  hold("Edge routing regexp lost")
 if not any(b.get('format')=='tar' and b.get('asset')==TAR_SHA+'.tar.gz' for b in manifest.get('bundles',[])):
  hold('Matching TAR not in Edge manifest')
 # Source site home and noindex remain verifiably unchanged except 21964 OG tags.
 for page in ('index.html','__pages/23/englishpt.page'):
  text=(SITE/page).read_text('utf8')
  if text.count('name="google-site-verification"')!=1 or text.count('name="naver-site-verification"')!=1:
   hold("One of owner verification tags missing "+page)
 if len(list((SITE/'assets/images/seo-square/v1').glob('*.jpg')))!=21964:
  hold('Unique actual image count differs')
 # Full 202,765-file SHA1 digest, fail closed on symlinks and URL unsafe keys.
 files={}
 sha_to_path={}
 counted=collections.Counter()
 grand=0
 for directory, dirs, filenames in os.walk(SITE):
  dirs.sort(); filenames.sort()
  for name in filenames:
   p=Path(directory)/name
   if p.is_symlink() or not p.is_file():hold("Unexpected symlink or non-file")
   rel=p.relative_to(SITE).as_posix()
   if '?' in rel or '#' in rel or '\\' in rel:hold("Invalid URL path: "+rel)
   key='/'+rel
   if key in files:hold("Duplicated static file path")
   digest=digest_file(p)
   files[key]=digest
   sha_to_path.setdefault(digest,rel)
   sz=p.stat().st_size
   grand+=sz
   if rel.startswith('assets/images/seo-square/v1/'):counted["image"]+=1
   elif rel.startswith('__pages/'):counted["edge_page"]+=1
   elif rel.endswith('.html'):counted["html"]+=1
   else:counted['misc']+=1
 if len(files)!=STATIC_EXPECT:hold('Unmatched candidate static members '+str(len(files))+' expected '+str(STATIC_EXPECT))
 if counted['image']!=21964 or counted['edge_page']!=158571:hold('Image or SEO shard count mismatch')
 if sum('/'+rel not in files for rel in ('index.html','_headers','_redirects','robots.txt','sitemap-index.xml','netlify.toml'))!=0:
  hold('Missing critical site files')
 meta=json.loads((ROOT/'async-og-21964-evidence/EDGE_ASSET_MANIFEST_OFFLINE.json').read_text('utf8'))
 edge=meta['edge_functions']
 if edge.get('tar')!=TAR_SHA or set(edge)!=set(('tar','eszip2')):
  hold('Edge bundle sha map not exact')
 if not (ROOT/'async-og-21964-private-bundles'/('1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b.tar.gz')).is_file():
  hold("Matching Edge tar missing")
 for format_,sha in edge.items():
  path=ROOT/'async-og-21964-private-bundles'/(sha+'.'+('tar.gz' if format_=='tar' else 'eszip'))
  if not path.is_file() or digest_file(path,'sha256')!=sha:hold("Edge code digest does not match local source "+format_)
 # Store resumable hashes only in job artifact, not Netlify.
 path=AUDIT/'FULL_202765_STATIC_SHA1_DIGEST.json.gz'
 with gzip.open(path,'wt',encoding='utf8',compresslevel=6) as z:json.dump(files,z,ensure_ascii=False,separators=(',',':'))
 rows={
  'status':'PASS_FULL_SIGNED_SOURCE_SHA1_202765_ASYNC_NEW_DRAFT_READY',
  'date_utc':now(),
  'source_sha256':SOURCE_ARCHIVE_SHA,
  'original_seo_pages':158571,'indexable_og_pages':21964,'noindex_preserved':136607,
  'images_count':counted['image'],'static_files_count':len(files),'total_static_bytes':grand,
  'distinct_sha1_values':len(sha_to_path),'edge_functions':edge,
  'original_404_Draft_left_untouched':'6ad6daf01389db1fbe596f74',
  'expected_production_id':PROD_ID,'NETLIFY_POST_attempts':0,
  'global_noindex_in_new_draft':True,'status_flags':flags(),
  'sha_gz_file':path.name
 }
 report("01_FULL_STATIC_HASH_AND_PRESERVE_PREFLIGHT.json",rows)
 return files,sha_to_path,edge


def post_one_new_async_draft(files,edge):
 """At most one POST, no retry on ambiguity; query title is used for idempotency."""
 netstate={'date_utc':now(),'status':'HOLD','marker':MARKER,'request_draft':True,
  'request_async':True,'production_publishes':0,'attempted_new_deploy_POST':0,
  'target_old_Draft_reuploads':0,'new_file_uploads':0}
 try:
  site_and_deploy_guard()
  existing=get('sites/'+SITE_ID+'/deploys?per_page=100')
  if any((d.get('title') or '')==MARKER for d in existing):
   hold("Duplicate existing async Draft marker: never create twice")
  credit=get('accounts/'+get('sites/'+SITE_ID)['account_id'])
  if credit.get('usages_exceeded') or credit.get('configurable_limits_exceeded'):
   hold("Netlify credit/account limit reached")
  creditinfo=(credit.get('capabilities') or {}).get('credits') or {}
  if 'used' in creditinfo and 'included' in creditinfo and creditinfo['used']>=creditinfo['included']:
   hold("No remaining account credits")
  netstate['credits_preflight']=creditinfo
  payload={'files':files,'edge_functions':edge,'draft':True,'async':True,
           'branch':'enptog21964asyncdigestonce20'}
  body=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf8')
  netstate['request_bytes']=len(body)
  if len(body)>25000000:hold('Too-large digest payload')
  # Save one-shot attempt before network. Re-running never sends this POST automatically.
  netstate['attempted_new_deploy_POST']=1
  netstate['status']='POST_ATTEMPTED_DO_NOT_RETRY_UNTIL_GET_RECONCILIATION'
  report('02_ONE_ASYNC_DRAFT_CREATE_ATTEMPT.json',netstate)
  api_url=API+'sites/'+SITE_ID+'/deploys?'+urllib.parse.urlencode({'title':MARKER})
  request=urllib.request.Request(api_url,method='POST',data=body,headers={
    'Authorization':'Bearer '+get_token(),'Content-Type':'application/json','Accept':'application/json'})
  try:
   with urllib.request.urlopen(request,timeout=75) as resp:
    response=json.loads(resp.read(400000).decode('utf8'))
    netstate['post_http_status']=resp.status
  except urllib.error.HTTPError as err:
   netstate['post_http_status']=err.code
   netstate['post_error_excerpt']=err.read(900).decode('utf8',errors='replace')
   hold("Async draft POST rejected; do not retry blindly")
  draft=response.get('id')
  if not isinstance(draft,str) or not re.fullmatch(r'[0-9a-f]{24}',draft):
   hold("No valid async draft ID; reconcile Netlify GET manually")
  netstate['draft_id']=draft
  netstate['immediate_state']=response.get('state')
  netstate['returned_draft']=response.get('draft')
  netstate['status']='CREATED_NONPUBLISHED_ASYNC_DRAFT_ONCE_AWAIT_PREPARE'
  report('02_ONE_ASYNC_DRAFT_CREATE_ATTEMPT.json',netstate)
  return draft
 except Exception as e:
  netstate['status']='HOLD_ASYNC_DRAFT_CREATE'
  netstate['error']=str(e)[:400]
  report('02_ONE_ASYNC_DRAFT_CREATE_ATTEMPT.json',netstate)
  raise


def reconcile_only(draft):
 obj={'checked_utc':now(),'draft_id':draft,'status':'HOLD','state_history':[],
  'production_publish_attempts':0,'retry_posts':0,'retry_large_uploads':0,'manual_followup_required':False}
 try:
  for i in range(28):
   site,d=site_and_deploy_guard(draft)
   state=d.get('state')
   n=[len(d.get(name) or []) for name in ('required','required_edge_functions','required_functions','required_server')]
   obj['state_history'].append({'state':state,'counts':n,'utc':now()})
   if state in ('prepared','uploading','uploaded','ready'):
    obj['netlify_title']=d.get('title')
    if d.get('title')!=MARKER:hold('Draft marker differs')
    if state=='ready' or any(n):break
   if state in ('error','failed','cancelled'):hold('Draft error state '+str(state))
   time.sleep(4)
  if d.get('state') not in ('prepared','uploading','uploaded','ready'):
   hold("Async Netlify digest not prepared yet, no upload attempted")
  statics=d.get('required') or []
  need_edge=d.get('required_edge_functions') or []
  obj['required_static_sha_count']=len(statics)
  obj['required_edge_sha_count']=len(need_edge)
  obj['required_sha_prefixes']=[x[:9] for x in statics[:6]]
  obj['required_edge_codes']=need_edge
  obj['state']=d.get('state')
  if d.get('state')=='ready' and not statics and not need_edge:
   obj['status']='PASS_NEW_DRAFT_READY_NO_UPLOAD_REQUIRED'
  elif len(statics)>MAX_ASSET_UPLOADS:
   obj['status']='HOLD_MORE_THAN_250_REQUIRED_FILE_SHA1_NO_BLIND_UPLOAD'
   obj['manual_followup_required']=True
  elif need_edge and any(x not in edge_hashes for x in need_edge):
   obj['status']='HOLD_UNRECOGNIZED_EDGE_SHA'
   obj['manual_followup_required']=True
  else:
   obj['status']='PASS_REQUIRED_SHA_BOUNDED_UPLOAD_POSSIBLE'
  report('03_ASYNC_DEPLOY_DIFF_AND_REQUIRED_SHA_GETONLY.json',obj)
  return obj,statics,need_edge
 except Exception as e:
  obj['status']='HOLD_ASYNC_GET_RECONCILIATION'
  obj['error']=str(e)[:350]
  report('03_ASYNC_DEPLOY_DIFF_AND_REQUIRED_SHA_GETONLY.json',obj)
  raise

def bounded_upload(draft,sha_to_path,reqfiles,reqedge,edge):
 out={'time_utc':now(),'status':'HOLD','draft_id':draft,'static_attempts':0,'edge_attempts':0,
  'total_attempted_bytes':0,'completed_files':[],'completed_edge':[],
  'netlify_prod_mutations':0,'async_deploy_posts_retried':0}
 if len(reqfiles)>MAX_ASSET_UPLOADS:hold('Static files above safety cap')
 if len(set(reqfiles))!=len(reqfiles):hold("Unexpected duplicate required SHA")
 if any(x not in sha_to_path for x in reqfiles):hold("Netlify required SHA not in signed local manifest")
 maps={}
 for fmt,sha in edge.items():
  suffix='.tar.gz' if fmt=='tar' else '.eszip'
  maps[sha]=ROOT/'async-og-21964-private-bundles'/(sha+suffix)
 if any(x not in maps for x in reqedge):hold('Netlify requested unknown Edge SHA')
 count_bytes=sum((SITE/sha_to_path[x]).stat().st_size for x in reqfiles)
 if count_bytes>MAX_ASSET_UPLOAD_BYTES:hold("Needed static file bytes above 16MB; no bulk uploads")
 out['planned_required_static_count']=len(reqfiles)
 out['planned_required_static_bytes']=count_bytes
 out['planned_required_edge_count']=len(reqedge)
 report('04_BOUNDED_SHA_UPLOAD_LEDGER.json',out)
 for sha in reqfiles:
  site_and_deploy_guard(draft)
  rel=sha_to_path[sha]
  path=SITE/rel
  if digest_file(path)!=sha:hold('File bytes changed since signed digest')
  target=API+'deploys/'+draft+'/files/'+urllib.parse.quote(rel,safe='/')
  body=path.read_bytes()
  out['static_attempts']+=1
  out['total_attempted_bytes']+=len(body)
  report('04_BOUNDED_SHA_UPLOAD_LEDGER.json',out)
  request=urllib.request.Request(target,data=body,method='PUT',headers={
   'Authorization':'Bearer '+get_token(),'Content-Type':'application/octet-stream'})
  # Exactly one PUT per SHA, fail-closed if response ambiguous; no upload retry.
  try:
   with urllib.request.urlopen(request,timeout=45) as resp:
    if resp.status not in (200,201,202,204):hold('Unexpected static upload HTTP code')
    resp.read(120)
   out['completed_files'].append({'sha':sha,'path':rel})
   report('04_BOUNDED_SHA_UPLOAD_LEDGER.json',out)
  except Exception as err:
   out['status']='HOLD_STATIC_PUT_AMBIGUOUS_NO_RETRY'
   out['error']=str(err)[:360]
   report('04_BOUNDED_SHA_UPLOAD_LEDGER.json',out)
   raise
 for sha in reqedge:
  site_and_deploy_guard(draft)
  path=maps[sha]
  if digest_file(path,'sha256')!=sha:hold("Edge bundle mutated")
  out['edge_attempts']+=1
  report('04_BOUNDED_SHA_UPLOAD_LEDGER.json',out)
  request=urllib.request.Request(API+'deploys/'+draft+'/edge_functions/'+sha,
    method='PUT',data=path.read_bytes(),headers={'Authorization':'Bearer '+get_token(),
    'Content-Type':'application/octet-stream'})
  try:
   with urllib.request.urlopen(request,timeout=45) as resp:
    if resp.status not in (200,201,202,204):hold("Edge sha upload HTTP error")
    resp.read(300)
   out['completed_edge'].append(sha)
   report('04_BOUNDED_SHA_UPLOAD_LEDGER.json',out)
  except Exception as err:
   out['status']='HOLD_EDGE_PUT_AMBIGUOUS_NO_RETRY'
   out['error']=str(err)[:350]
   report('04_BOUNDED_SHA_UPLOAD_LEDGER.json',out)
   raise
 out['status']='PASS_ONLY_REQUESTED_SMALL_FILES_AND_EDGE_CODES_UPLOADED'
 report('04_BOUNDED_SHA_UPLOAD_LEDGER.json',out)
 return out

def check_ready(draft):
 results={'time_utc':now(),'draft_id':draft,'state_history':[],'status':'HOLD',
  'published_id_preserved':False,'changes_to_production':0,'unsafe_production_restore_count':0}
 try:
  for i in range(22):
   site,d=site_and_deploy_guard(draft)
   state=d.get('state')
   n=[len(d.get(x) or []) for x in ('required','required_edge_functions','required_functions','required_server')]
   results['state_history'].append({'state':state,'required_counts':n})
   if state=='ready' and not any(n):
    results['status']='PASS_NONPUBLISHED_ASYNC_FULL_DRAFT_READY'
    break
   if state in ('error','failed'):hold('Netlify marked Draft error')
   time.sleep(4)
  results['published_id_preserved']=True
  report('05_ASYNC_DRAFT_READY_AND_PRODUCTION_UNCHANGED.json',results)
  return results
 except Exception as e:
  results['status']='HOLD_AFTER_ASYNC_PUT'
  results['error']=str(e)[:450]
  report('05_ASYNC_DRAFT_READY_AND_PRODUCTION_UNCHANGED.json',results)
  raise

if __name__=='__main__':
 action=sys.argv[1] if len(sys.argv)>1 else ''
 try:
  if action=='preflight':
   preflight()
  elif action=='deploy':
   files,sha_to_path,edge_hashes=preflight()
   draft=post_one_new_async_draft(files,edge_hashes)
   x,reqfiles,reqedge=reconcile_only(draft)
   if x['status']=='PASS_REQUIRED_SHA_BOUNDED_UPLOAD_POSSIBLE':
    bounded_upload(draft,sha_to_path,reqfiles,reqedge,edge_hashes)
    check_ready(draft)
   elif x['status']=='PASS_NEW_DRAFT_READY_NO_UPLOAD_REQUIRED':
    check_ready(draft)
   else:
    print('SAFE_HOLD_NO_ASSET_UPLOAD',x['status'],flush=True)
  else:
   raise SystemExit("Expected preflight or deploy")
 except Exception as exc:
  print('ENPT_ASYNC_FAILURE_NO_PRODUCTION_RESTORATION',type(exc).__name__+': '+str(exc)[:550],flush=True)
  raise
