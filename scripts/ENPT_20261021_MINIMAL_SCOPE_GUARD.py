#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed delta audit: only four navigation/UX fixes above approved OG Production candidate.
Usage: python scripts/ENPT_20261021_MINIMAL_SCOPE_GUARD.py before|after
Never deploys or changes any HTML.
"""
import gzip, hashlib, json, pathlib, sys, datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/'thumb-21964-candidate'
OUT=ROOT/'minimal-20261021-qa'
OUT.mkdir(exist_ok=True)
STATE=OUT/'BASELINE_FILE_SHA256.json'
SIGNED=ROOT/'signed-qa-map'/'NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz'
ROUTES=['student-english.html','englishpt.html','english-conversation.html']
NEW={'guides/international-school-english.html','guides/senior-english.html'}
STYLE={'assets/styles.css','pilot.css','assets/pilot.css','styles.css'}
with gzip.open(SIGNED,'rt',encoding='utf8') as f:
    signed=json.load(f)['original_public_html_to_data_payload']
assert len(signed)==158571
assert sum(not rec['noindex'] for rec in signed.values())==21964
ALLOWED={signed[route]['to'].lstrip('/') for route in ROUTES}|STYLE
EXPECTED_CHANGED={signed[route]['to'].lstrip('/') for route in ROUTES}|{'assets/styles.css'}
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            data=f.read(1024*1024)
            if not data:break
            h.update(data)
    return h.hexdigest()
def manifest():
    return {p.relative_to(SITE).as_posix():digest(p) for p in SITE.rglob('*') if p.is_file()}
mode=sys.argv[1]
if mode=='before':
    assert SITE.is_dir() and not any((SITE/p).exists() for p in NEW)
    d=manifest()
    assert len(d)>200000,('BASELINE_TOO_SMALL',len(d))
    for r in ROUTES:assert signed[r]['to'].lstrip('/') in d
    for critical in ['robots.txt','_headers','_redirects','netlify.toml','sitemap-index.xml','netlify/edge-functions/shard-router.js']:
        assert critical in d,('CRITICAL_MISSING',critical)
    STATE.write_text(json.dumps(d,sort_keys=True),encoding='utf8')
    print('PASS_BASELINE_OG_PRODUCTION_SCOPE_SNAPSHOT',len(d),flush=True)
elif mode=='after':
    old=json.loads(STATE.read_text('utf8'))
    now=manifest()
    removed=set(old)-set(now)
    added=set(now)-set(old)
    changed={p for p in (set(old)&set(now)) if old[p]!=now[p]}
    assert not removed,('UNEXPECTED_REMOVALS',list(sorted(removed))[:25])
    assert added==NEW,('ADDED_NOT_TWO_GUIDES',sorted(added))
    assert EXPECTED_CHANGED.issubset(changed),('MISSING_REQUIRED_CHANGES',sorted(EXPECTED_CHANGED-changed))
    assert changed<=ALLOWED,('UNEXPECTED_CHANGED_FILES',sorted(changed-ALLOWED)[:25])
    assert all(now[p]==old[p] for p in ['robots.txt','_headers','_redirects','netlify.toml','sitemap-index.xml','netlify/edge-functions/shard-router.js'])
    for route in ROUTES:
        t=(SITE/signed[route]['to'].lstrip('/')).read_text('utf8')
        assert 'ENGLISH PT' in t or '잉글리시PT' in t,route
        assert 'ENGLISH GO' not in t and '잉글리시GO' not in t,route
        assert t.count('name="englishpt-consultation"')==1,route
    for name in NEW:
        body=(SITE/name).read_text('utf8')
        assert 'name="robots" content="noindex,follow"' in body,name
        assert 'name="englishpt-consultation"' in body,name
        assert 'https://englishpt.kr/'+name in body,name
    report={'status':'PASS_ONLY_MINIMAL_NAV_AND_CSS_CHANGES_FROM_APPROVED_OG_CANDIDATE',
        'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'baseline_file_count':len(old),'candidate_file_count':len(now),
        'modified_paths':sorted(changed),'added_paths':sorted(added),
        'removed_count':0,'all_other_file_sha256_unchanged':True,
        'signed_route_count':158571,'indexable_count':21964,'noindex_count':136607,
        'production_published':False,'brand_changed':False,
        'p0_p1_p3_content_patches_run':False,'new_images_generated':0}
    (OUT/'MINIMAL_DIFF_SCOPE_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    STATE.unlink(missing_ok=True)
    print('ENPT_MINIMAL_SCOPE_FINAL_PASS',json.dumps(report,ensure_ascii=False),flush=True)
else:raise ValueError('before|after')
