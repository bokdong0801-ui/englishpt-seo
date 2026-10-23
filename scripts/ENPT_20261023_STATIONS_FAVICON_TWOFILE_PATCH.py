#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Precisely TWO changed production paths: existing 911 stations sharded page and root favicon.ico.
Requires previously reconstructed exact October 21 Production candidate. No publish/network.
Preserves station HTML original head, canonical, OG, robots, links, forms and every other file.
"""
import ast
import hashlib
import io
import json
import pathlib
import re
import gzip
import datetime as dt
from PIL import Image
import cairosvg

ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/'thumb-21964-candidate'
OLD=ROOT/'scripts/ENPT_20261021_P1_1815_OFFICIAL15_STATIONSUX_DRAFT_PATCH.py'
SIGNED=ROOT/'signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz'
OUT=ROOT/'enpt-twofile-qa';OUT.mkdir(exist_ok=True)
with gzip.open(SIGNED,'rt',encoding='utf8') as f:
    manifest=json.load(f)['original_public_html_to_data_payload']
assert len(manifest)==158571
entry=manifest['stations.html']
assert not entry['noindex']
route=SITE/entry['to']
assert route.exists() and not (SITE/'favicon.ico').exists()
station_old=route.read_bytes()
assert b'enpt-stations-ux-20261021' not in station_old
assert b'enpt-stations-ux-js-20261021' not in station_old
assert b'id="stationSearch"' in station_old
assert b'class="station-index-grid"' in station_old
# Trusted existing, offline-proven CSS and JS. Parse the four static string constants,
# do NOT run P1 mass modification (1815 pages, 360 station changes).
tree=ast.parse(OLD.read_text('utf8'))
parts={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        key=node.targets[0].id
        if key in ('CSS','TOOLS','NAV','JS'):
            parts[key]=ast.literal_eval(node.value)
assert set(parts)=={'CSS','TOOLS','NAV','JS'}
css,tools,nav,js=[parts[k] for k in ('CSS','TOOLS','NAV','JS')]
old=station_old.decode('utf8')
def head(html):
    x=re.search(r'<head\b[^>]*>.*?</head>',html,re.I|re.S)
    assert x
    return x.group(0)
# All head SEO bytes unchanged except an inline style addition
assert old.count('</head>')==1 and old.count('</body>')==1
assert old.count('<div id="stationLines">')==1
assert old.count('id="stationSearch"')==1
new=old.replace('</head>',css+'</head>',1).replace('</body>',js+'</body>',1)
m=re.search(r'<div class="station-search-box">.*?</div>',new,re.S)
assert m,"HOLD_STATION_SEARCH_CONTAINER_CHANGED"
new=new[:m.end()]+tools+new[m.end():]
new=new.replace('<div id="stationLines">',nav+'<div id="stationLines">',1)
assert head(new).replace(css,'')==head(old)
for attr in ('rel="canonical"','name="robots"','property="og:image"',
             'name="englishpt-consultation"','class="station-index-link"'):
    assert old.count(attr)==new.count(attr),(attr,old.count(attr),new.count(attr))
for marker in ('id="enptStationLine"','id="enptStationClear"',
               'id="enptStationResults"','id="enpt-stations-ux-js-20261021"',
               'id="enpt-stations-ux-20261021"'):
    assert marker in new,marker
assert new.count('id="stationSearch"')==1
assert old.count('href="/station-')==new.count('href="/station-')
route.write_text(new,'utf8')

# Render exactly the existing SVG/favicon design (green rounded square + cream PT).
svg=SITE/'assets/favicon.svg'
assert svg.is_file()
svgbytes=svg.read_bytes()
assert b'#2C5E49' in svgbytes and b'>PT<' in svgbytes, "HOLD_EXISTING_FAVICON_ART_DRIFT"
png=cairosvg.svg2png(bytestring=svgbytes,output_width=256,output_height=256)
im=Image.open(io.BytesIO(png)).convert('RGBA')
assert im.size==(256,256)
ico=SITE/'favicon.ico'
im.save(ico,format='ICO',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
assert ico.is_file() and ico.stat().st_size>300
with Image.open(ico) as verify:
    assert verify.format=='ICO'
    assert verify.size==(256,256)
proof={'status':'PASS_STATION_UI_ONLY_PLUS_FAVICON_ICO',
       'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
       'changed_existing':['stations.html'],
       'physical_station_file':entry['to'],
       'added':['favicon.ico'],
       'station_old_sha256':hashlib.sha256(station_old).hexdigest(),
       'station_new_sha256':hashlib.sha256(route.read_bytes()).hexdigest(),
       'favicon_svg_sha256':hashlib.sha256(svgbytes).hexdigest(),
       'favicon_ico_sha256':hashlib.sha256(ico.read_bytes()).hexdigest(),
       'favicon_ico_bytes':ico.stat().st_size,
       'new_station_search_controls':True,
       'station_route_links_unchanged':True,
       'SEO_head_except_inline_style_unchanged':True,
       'form_markup_unchanged':True,
       'production_published':False}
(OUT/'TWOFILE_PATCH_REPORT.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8')
print('ENPT_TWOFILE_PATCH_OFFLINE_PASS',json.dumps(proof,ensure_ascii=False),flush=True)
