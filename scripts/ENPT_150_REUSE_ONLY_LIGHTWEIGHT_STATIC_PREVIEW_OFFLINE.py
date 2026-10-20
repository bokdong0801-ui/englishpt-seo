#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate static, noindex sample-only website from exact 150 verified images.
No network, Netlify or Production write. This is not the original full site HTML.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from html import escape
import csv, hashlib, json, shutil, os
ROOT=Path.cwd()
SRC=ROOT/"sample-artifact"
OUT=ROOT/"lite-150-preview-site"
CHECK=ROOT/"lite-150-evidence"
OUT.mkdir(exist_ok=True);CHECK.mkdir(exist_ok=True)
DRAFT="https://enptog150reviewonce20--englishpt-seo.netlify.app"
ORIGIN="https://englishpt.kr"
qa=json.loads((SRC/"PILOT_150_IMAGE_QA_REPORT.json").read_text("utf8"))
if qa["status"]!="PASS_150_JPEG_SQUARE_PILOT_QA" or qa["rendered"]!=150 or qa["issues"]:
 raise SystemExit("HOLD SOURCE 150 PILOT QA NOT PASS")
with (SRC/"ALL_21964_INDEXABLE_THUMBNAIL_MAP.csv").open(encoding="utf-8-sig",newline="") as f:
 mapping={x["route"]:x for x in csv.DictReader(f)}
if len(mapping)!=21964:raise SystemExit("HOLD ORIGINAL 21964 MAP")
samples=json.loads((SRC/"PILOT_150_IMAGE_ROWS.json").read_text("utf8"))
if len(samples)!=150:raise SystemExit("HOLD SOURCE PILOT COUNT")
CSS="""*{box-sizing:border-box}body{margin:0;background:#f7f8f5;color:#283830;font-family:system-ui,'Malgun Gothic',sans-serif}header{background:white;padding:22px max(18px,calc((100vw - 1080px)/2));border-bottom:1px solid #e1e8e0}h1{font-size:24px;margin:4px 0}.small{font-size:13px;color:#637168;line-height:1.6}.wrap{max-width:1130px;margin:0 auto;padding:20px 16px 60px}.notice{padding:12px;border-radius:9px;background:#fdf6e9;font-size:13px;margin-bottom:16px}.filter{display:flex;gap:9px;flex-wrap:wrap;margin:20px 0 15px}input,select{border:1px solid #cfdbd1;padding:12px;border-radius:9px;font-size:15px;max-width:100%}input{flex:1;min-width:205px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}.item{border:1px solid #e5e9e5;background:white;border-radius:12px;overflow:hidden}.item a{color:inherit;text-decoration:none}.photo{width:100%;aspect-ratio:1;object-fit:contain}.info{padding:10px}.info strong{display:block;font-size:14px}.path{font-size:10px;overflow-wrap:anywhere;color:#7c877e;margin:7px 0}.sm{display:flex;align-items:center;gap:10px}.sm img{width:102px;height:102px}.sm span{font-size:12px;color:#66716b}.detail{display:grid;grid-template-columns:minmax(0,550px) 1fr;gap:22px}.detail>.photo{border-radius:13px;border:1px solid #ddd}.panel{background:white;border-radius:12px;padding:20px;overflow-wrap:anywhere}.sizes{display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap}.sizes figure{margin:0}.sizes figcaption{font-size:12px;margin-top:4px}.sizes img{border:1px solid #e1e7e2}.back{display:block;margin:10px 0;color:#327755}.badge{display:inline-block;background:#eaf2ec;padding:4px 8px;border-radius:6px;font-size:12px}@media(max-width:900px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:680px){.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.detail{grid-template-columns:1fr}.info{padding:8px}.info strong{font-size:12px}.path{font-size:9px}.sm img{width:75px;height:75px}.sm span{font-size:10px}header{padding:16px}h1{font-size:20px}.wrap{padding:14px 12px}}"""
(OUT/"style.css").write_text(CSS,"utf8")
(OUT/"_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n","utf8")
(OUT/"robots.txt").write_text("User-agent: *\nDisallow: /\n","utf8")
HEAD='<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><link rel="stylesheet" href="/style.css">'
gallery=[];metrics=[];seen=set()
for sample in samples:
 route=sample["route"]
 m=mapping.get(route)
 if not m or route in seen or m["mapping_status"]!="READY_METADATA_ONLY" or m["indexable"]!="TRUE":
  raise SystemExit("HOLD PILOT IS NOT ON EXACT INDEXED ROUTE "+route)
 seen.add(route)
 if sample["keyword"]!=m["search_keyword"] or sample["header"]!=m["header_label"]:
  raise SystemExit("HOLD LABEL MISMATCH "+route)
 if sample["errors"]:raise SystemExit("HOLD PILOT SAFEAREA FAIL "+route)
 file=SRC/sample["image"]
 key=m["image_key"]
 if file.name!=key+".jpg":raise SystemExit("HOLD INCORRECT IMAGE KEY "+route)
 if not file.is_file():raise SystemExit("HOLD IMAGE NOT FOUND "+route)
 img=Image.open(file)
 if img.size!=(1200,1200) or img.format!="JPEG" or file.stat().st_size>350000:
  raise SystemExit("HOLD IMAGE FORMAT SIZE "+route)
 image_path=m["planned_image_path"]
 if image_path!="assets/images/seo-square/v1/"+key+".jpg":
  raise SystemExit("HOLD IMAGE PATH MAP "+route)
 dst=OUT/image_path;dst.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(file,dst)
 image_url=DRAFT+"/"+image_path
 label=m["header_label"]+" · "+m["search_keyword"]
 sha=hashlib.sha256(file.read_bytes()).hexdigest()
 title=escape(label,quote=True)
 view=f'''<!doctype html><html lang="ko"><head>{HEAD}<title>{title} | 150 Preview</title><meta property="og:title" content="{title}"><meta property="og:image" content="{image_url}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="1200"><meta property="og:image:type" content="image/jpeg"><meta name="twitter:image" content="{image_url}"></head><body><header><h1>ENGLISH PT 썸네일 검수</h1><p class="small">색인차단 비게시 Draft · 실제 홈페이지 UI가 아닌 썸네일 검토 화면</p></header><main class="wrap"><a class="back" href="/">← 전체 썸네일 150개</a><p class="notice">이 페이지는 시험용 메타태그와 이미지만 표시합니다. 운영 페이지의 콘텐츠나 상담폼은 포함하지 않습니다.</p><div class="detail"><img class="photo" src="/{image_path}" alt="{title}"><section class="panel"><h2>{title}</h2><p class="small">기존 운영 URL: <a href="{ORIGIN}/{route}" rel="noopener noreferrer" target="_blank">{route}</a></p><p class="small">실제 JPEG 파일: {key}.jpg</p><p>모바일 정사각형 표시 크기</p><div class="sizes"><figure><img width="102" height="102" src="/{image_path}"><figcaption>102px</figcaption></figure><figure><img width="156" height="156" src="/{image_path}"><figcaption>156px</figcaption></figure><figure><img width="200" height="200" src="/{image_path}"><figcaption>200px</figcaption></figure></div><p class="small">SHA256: {sha}</p><p class="small">컬러: {m["accent_hex"]}</p></section></div></main></body></html>'''
 (OUT/route).write_text(view,encoding="utf8")
 gallery.append(f'''<article class="item" data-key="{escape((label+' '+route).lower(),quote=True)}" data-cat="{escape(m["category"],quote=True)}"><a href="/{route}"><img class="photo" loading="lazy" src="/{image_path}" alt="{title}"><div class="info"><strong>{title}</strong><div class="path">{route}</div><div class="sm"><img loading="lazy" src="/{image_path}" alt=""><span>102px 검색 썸네일<br>선택하면 156px 확대</span></div><span class="badge">{escape(m["category"])}</span></div></a></article>''')
 metrics.append({"route":route,"image_path":image_path,"size_bytes":file.stat().st_size,"sha256":sha,"keyword":m["search_keyword"],"header":m["header_label"],"accent":m["accent_hex"]})
assert len(metrics)==150 and len({x["image_path"] for x in metrics})==150
cats=sorted({m["category"] for m in (mapping[r["route"]] for r in samples)})
opts="".join(f'<option value="{escape(c)}">{escape(c)}</option>' for c in cats)
body=f'''<!doctype html><html lang="ko"><head>{HEAD}<title>ENGLISH PT 150종 썸네일 비게시 검수</title></head><body><header><h1>ENGLISH PT · 지역별 썸네일 150종</h1><p class="small">확정된 크림 질감·지역명·중앙 키워드·파스텔 포인트 디자인을 모바일 크기에서 비교하는 검수 페이지입니다.</p></header><main class="wrap"><div class="notice">실제 Netlify Draft 미리보기입니다. 이 샘플은 전체 21,964개 중 검증된 150개이며 Production 콘텐츠는 포함하지 않습니다.</div><div class="filter"><input id="keyword" type="search" placeholder="역명 · 지역명 · TOEIC · IELTS · OPIc"><select id="category"><option value="">전체 유형</option>{opts}</select></div><p class="small" id="count">150개 표시</p><div class="grid">{''.join(gallery)}</div></main><script>const a=[...document.querySelectorAll(".item")],k=document.querySelector("#keyword"),c=document.querySelector("#category"),o=document.querySelector("#count");function update(){{let n=0,t=k.value.trim().toLowerCase(),v=c.value;for(const e of a){{const ok=(!t||e.dataset.key.includes(t))&&(!v||e.dataset.cat===v);e.hidden=!ok;if(ok)n++}}o.textContent=n+" / 150개 표시"}}k.addEventListener("input",update);c.addEventListener("change",update);</script></body></html>'''
(OUT/"index.html").write_text(body,"utf8")
report={"status":"PASS_150_REUSED_JPEG_STATIC_PREVIEW_QA","checked_routes":len(metrics),"source_indexable_routes":len(mapping),"image_dimensions":[1200,1200],"total_image_bytes":sum(x["size_bytes"] for x in metrics),"max_image_bytes":max(x["size_bytes"] for x in metrics),"preview_files":sum(f.is_file() for f in OUT.rglob("*")),"test_mobile_sizes":[102,156,200],"netlify_prod_modified":False,"netlify_draft_created":False,"sample_pages_are_metadata_only":True,"source_jpeg_images_reused_without_regeneration":True,"gallery_url":DRAFT+"/","items":metrics}
(CHECK/"STATIC_PREVIEW_150_SOURCE_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
print("ENPT_150_REUSED_IMAGES_STATIC_QA",json.dumps({k:v for k,v in report.items() if k!="items"},ensure_ascii=False),flush=True)
