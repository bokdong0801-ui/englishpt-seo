#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed SHA256 diff for exactly ONE existing station page and ONE new root favicon ICO."""
import datetime,json,pathlib,gzip,hashlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/'thumb-21964-candidate'
OUT=ROOT/'enpt-twofile-qa';OUT.mkdir(exist_ok=True)
BASE=OUT/'BASELINE_ALL_FILES.json'
with gzip.open(ROOT/'signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz','rt',encoding='utf8') as f:
    source=json.load(f)['original_public_html_to_data_payload']
station=source['stations.html']['to'].lstrip('/')
assert station.startswith('__pages/') and station.endswith('.page'),station
def hashfile(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def allfiles():
    return {p.relative_to(SITE).as_posix():hashfile(p) for p in SITE.rglob('*') if p.is_file()}
phase=sys.argv[1]
if phase=='before':
    assert not (SITE/'favicon.ico').exists(),"ICON_ALREADY_IN_BASE"
    d=allfiles();assert len(d)==202766,('RECONSTRUCTED_PROD_FILE_COUNT',len(d))
    assert station in d
    BASE.write_text(json.dumps(d,sort_keys=True),encoding='utf8')
    print('ENPT_TWOFILE_BASELINE_PASS',len(d),station,flush=True)
elif phase=='after':
    before=json.loads(BASE.read_text('utf8'));now=allfiles()
    changed={k for k in set(now)&set(before) if now[k]!=before[k]}
    added=set(now)-set(before)
    removed=set(before)-set(now)
    assert len(before)==202766 and len(now)==202767
    assert changed=={station},('HOLD_UNEXPECTED_MODIFICATIONS',sorted(changed))
    assert added=={'favicon.ico'},('HOLD_UNEXPECTED_ADDITIONS',sorted(added))
    assert not removed,('HOLD_UNEXPECTED_DELETIONS',sorted(removed))
    for critical in ['robots.txt','_headers','_redirects','netlify.toml','sitemap-index.xml','netlify/edge-functions/shard-router.js','assets/favicon.svg','assets/styles.css','pilot.css']:
        assert now[critical]==before[critical],('CRITICAL_FILE_DRIFT',critical)
    proof={'status':'PASS_EXACTLY_ONE_EXISTING_STATIONS_PAGE_AND_ONE_NEW_FAVICON_FILE',
      'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'before_count':len(before),'after_count':len(now),
      'modified_paths':sorted(changed),'added_paths':sorted(added),'removed_paths':[],
      'unchanged_file_count':len(before)-len(changed),
      'production_published':False,
      'SEO_robots_sitemap_headers_edge_original_hashes':True}
    (OUT/'TWOFILE_SCOPE_DIFF.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    BASE.unlink()
    print('ENPT_TWOFILE_SHA_SCOPE_PASS',json.dumps(proof,ensure_ascii=False),flush=True)
else:raise ValueError('Expected before or after')
