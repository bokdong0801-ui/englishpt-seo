#!/usr/bin/env python3
"""V3 complete 36043 real course links: indexability, route, response and region checks.
GET only, ten requests max concurrently, pause on 429; does not submit forms.
"""
import csv,json,collections,concurrent.futures,urllib.request,urllib.error,hashlib,pathlib,re,time,threading,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=pathlib.Path('v3-final-36043-live-qa');OUT.mkdir(exist_ok=True)
PARTS=[ROOT/'stage5-input'/f'production_locality_rows_5149_v1.part{i:03d}.jsonl' for i in range(1,7)]
blob=b''.join(p.read_bytes() for p in PARTS)
assert hashlib.sha256(blob).hexdigest()=='3fe392df02bf76e0a6f84ef220433f0b901f97ae09a0a091269deeb2eaf8e9f0'
rows=[json.loads(line) for line in blob.decode().splitlines() if line.strip()]
assert len(rows)==5149
courses=('elem-tutor','elem-conv','mid-tutor','mid-conv','high-tutor','high-conv','worker-english-conv-academy')
entries=[{'route':r['region_slug']+'-'+course+'.html','dong':r['dong_name'],'sido':r['sido'],'course':course,'district':r['jurisdiction_full']} for r in rows for course in courses]
assert len(entries)==36043 and len({r['route'] for r in entries})==36043
BASE='https://review-enpt-v3-fullsite-20261027--englishpt-seo.netlify.app/'
stop=threading.Event()
def check(entry):
  uri=BASE+entry['route']
  row={**entry,'http':None,'final_url':'','canonical':'','canonical_expected':'https://englishpt.kr/'+entry['route'],'robots':'','town_text_present':False,'district_text_present':False,'result':'UNKNOWN','error':''}
  if stop.is_set():row['result']='SKIPPED_RATE_LIMIT';return row
  for attempt in range(2):
    try:
      request=urllib.request.Request(uri,method='GET',headers={'User-Agent':'ENPT-V3-Owner-36043-Pages-GetOnly','Accept':'text/html'})
      with urllib.request.urlopen(request,timeout=19) as response:
        body=response.read(85000).decode('utf8','replace')
        row['http']=response.status;row['final_url']=response.geturl()
        row['canonical']=(re.findall(r'<link\s+rel=["\x27]canonical["\x27]\s+href=["\x27]([^"\x27]+)',body,re.I) or [''])[0]
        row['robots']=(re.findall(r'<meta\s+name=["\x27]robots["\x27]\s+content=["\x27]([^"\x27]+)',body,re.I) or [''])[0]
        row['town_text_present']=entry['dong'] in body
        row['district_text_present']=entry['district'].split()[-1] in body
        row['x_robots']=response.headers.get('X-Robots-Tag','')
        if response.status!=200:row['result']='HTTP_NON200'
        elif row['final_url']!=uri:row['result']='REDIRECT'
        elif row['canonical']!=row['canonical_expected']:row['result']='CANONICAL_MISMATCH'
        elif not row['town_text_present']:row['result']='TOWN_REVIEW'
        else:row['result']='PASS'
        return row
    except urllib.error.HTTPError as e:
      row.update(http=e.code,error='HTTP_'+str(e.code),result='HTTP_'+str(e.code))
      if e.code==429:stop.set()
      return row
    except Exception as e:
      row['error']=type(e).__name__+':'+str(e)[:130]
      if attempt==0:time.sleep(.3);continue
      row['result']='NETWORK_ERROR'
      return row
  return row
t=time.monotonic()
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
  fs=[pool.submit(check,r) for r in entries]
  for n,f in enumerate(concurrent.futures.as_completed(fs),1):
    results.append(f.result())
    if n%4000==0:print('ENPT_V3_36043_LIVE_PROGRESS',n,collections.Counter(r['result'] for r in results).most_common(8),'seconds',round(time.monotonic()-t),flush=True)
results.sort(key=lambda r:r['route'])
assert len(results)==36043
fields=list(results[0])
with (OUT/'ALL_36043_V3_LIVE_HTTP_CANONICAL_REGION.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(results)
issues=[r for r in results if r['result']!='PASS']
with (OUT/'V3_36043_ISSUES_ONLY.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(issues)
counts=dict(collections.Counter(r['result'] for r in results))
status='PASS_ALL_36043_HTTP_CANONICAL_TOWN' if not issues else 'HOLD_REVIEW_ERRORS_OR_NETWORK'
summary={'status':status,'expected':36043,'checked':len(results),'counts':counts,'http_status':dict(collections.Counter(str(r['http']) for r in results)),
 'canonicals_correct':sum(r['canonical']==r['canonical_expected'] for r in results),'town_correct':sum(r['town_text_present'] for r in results),
 'district_text_correct':sum(r['district_text_present'] for r in results),'issue_count':len(issues),'examples':issues[:25],
 'elapsed_seconds':round(time.monotonic()-t,1),'form_posted':0,'production_mutation':0}
(OUT/'V3_36043_LIVE_AUDIT_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf8')
print('ENPT_V3_36043_LIVE_FINAL',json.dumps({k:v for k,v in summary.items() if k!='examples'},ensure_ascii=False),flush=True)
