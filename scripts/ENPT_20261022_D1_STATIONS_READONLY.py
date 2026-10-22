#!/usr/bin/env python3
import os, json, pathlib, re, datetime, urllib.request, xml.etree.ElementTree as ET
out=pathlib.Path('enpt-d1-readonly');out.mkdir(exist_ok=True)
base='https://englishpt.kr'
def get(url,private=False):
    headers={'User-Agent':'Mozilla/5.0 (ENPT D1 read-only check)'}
    if private:headers['Authorization']='Bearer '+os.environ['NETLIFY_AUTH_TOKEN']
    req=urllib.request.Request(url,headers=headers,method='GET')
    with urllib.request.urlopen(req,timeout=35) as f:return f.status,f.read().decode('utf-8','replace')
_,raw=get('https://api.netlify.com/api/v1/sites/98d96cc5-f0b7-4d3d-8072-6476d93e55a3',True)
production=json.loads(raw)['published_deploy']['id']
assert production=='6ad87e6bd3bc041359320392',production
code,body=get(base+'/stations.html')
markers={x:x in body for x in ['enpt-stations-ux-20261021','enpt-stations-ux-js-20261021','id="enptStationLine"','id="enptStationClear"','id="stationSearch"','class="station-index-grid"']}
_,text=get(base+'/sitemap-index.xml')
child=[x.text for x in ET.fromstring(text).iter() if x.tag.endswith('loc')]
assert len(child)==44,len(child)
indexed=set()
for url in child:
    status,xml=get(url);assert status==200,url
    indexed.update(x.text for x in ET.fromstring(xml).iter() if x.tag.endswith('loc'))
assert len(indexed)==21964,len(indexed)
entries=json.loads(pathlib.Path('data/stations.json').read_text('utf8'))['stations']
byname={v['name']:v for v in entries}
names=['강남역','홍대입구역','잠실역','서울역','부산역','대구역','대전역','수원역','건대입구역','고속터미널역','신촌역','왕십리역','선릉역','신도림역','합정역','노원역','도봉산역','구로디지털단지역','판교역','정자역']
rows=[]
for i,name in enumerate(names,1):
    url=base+'/station-'+byname[name]['slug']+'.html'
    http,html=get(url)
    meta=re.search(r'<meta[^>]*name="robots"[^>]*>',html,re.I)
    canon=re.search(r'<link[^>]*rel="canonical"[^>]*href="([^"]+)"',html,re.I)
    rows.append(dict(rank=i,name=name,url=url,http=http,sitemap=url in indexed,
      noindex='noindex' in meta.group().lower() if meta else None,
      canonical=canon.group(1) if canon else None,form='englishpt-consultation' in html))
status='PASS' if all(x['http']==200 and x['sitemap'] and x['noindex'] is False and x['canonical']==x['url'] for x in rows) else 'HOLD'
report=dict(status=status,at=datetime.datetime.now(datetime.timezone.utc).isoformat(),production=production,
 station_index_http=code,markers=markers,station_count=len(entries),sitemap_count=len(child),
 indexed_count=len(indexed),naver_admin_data_available=False,
 priority_note='Editorial high-importance rail hubs, not a measured keyword-search-volume ranking',next20=rows)
(out/'ENPT_D1_STATIONS_NEXT20.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print('D1_STATION_READONLY_VERDICT',json.dumps(report,ensure_ascii=False),flush=True)
if status!='PASS':raise SystemExit('HOLD_UNVERIFIED_CANDIDATES')
