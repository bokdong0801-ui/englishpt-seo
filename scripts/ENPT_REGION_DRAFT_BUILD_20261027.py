#!/usr/bin/env python3
# ENGLISH PT 2026-10-27 - NONPRODUCTION region review, generated from signed locality parts.
# This script writes ONLY to region-review-site/ and region-review-evidence/.
from __future__ import annotations
from collections import defaultdict
from html import escape
from pathlib import Path
import json,re,hashlib,shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"region-review-site"
PROOF=ROOT/"region-review-evidence"
EXPECTED_ROWS=5149
EXPECTED_SOURCE_SHA="3fe392df02bf76e0a6f84ef220433f0b901f97ae09a0a091269deeb2eaf8e9f0"
SRC=ROOT/"courses.html"
CSS=r"""
:root{--rg-green:#2c5e49;--rg-ink:#17231e}
.rg-hero{padding:66px 0;background:#f1eee7;color:var(--rg-ink)}
.rg-wrap{max-width:1180px;margin:auto;padding:0 24px}
.rg-hero-grid{display:grid;grid-template-columns:1.4fr .9fr;gap:38px;align-items:center}
.rg-label{color:#476b51;font-weight:800;font-size:12px;letter-spacing:.11em;margin-bottom:12px}
.rg-hero h1{font-size:clamp(34px,4.8vw,55px);line-height:1.23;letter-spacing:-.05em;margin:0 0 20px}
.rg-lead{color:#58675f;line-height:1.75;font-size:clamp(15px,1.7vw,18px);max-width:690px}
.rg-panel{border:1px solid #d7e1d9;border-radius:19px;background:#fff;padding:26px;box-shadow:0 14px 32px #162b1a0b}
.rg-panel strong{display:block;font-size:22px;line-height:1.45;color:#20352b}
.rg-panel p{line-height:1.7;color:#65766b}
.rg-stats{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
.rg-stats span{background:#eaf0ea;border-radius:999px;padding:9px 13px;font-size:12px;font-weight:700}
.rg-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:25px}
.rg-btn{display:inline-flex;align-items:center;justify-content:center;text-decoration:none!important;border:0;border-radius:999px;background:#2c5e49;color:#fff!important;padding:12px 19px;font-size:14px;font-weight:700;cursor:pointer}
.rg-btn--alt{background:#e1eae3;color:#244633!important}
.rg-section{padding:55px 0 78px}
.rg-section h2{font-size:clamp(25px,3.4vw,36px);letter-spacing:-.04em;margin:0 0 10px}
.rg-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:27px}
.rg-card{min-height:134px;border:1px solid #d7e2d8;background:#fff;border-radius:18px;padding:21px;display:flex;flex-direction:column;gap:9px;text-decoration:none!important;color:#21382c!important;transition:transform .2s,border-color .2s}
.rg-card:hover,.rg-card:focus-visible{border-color:#2c5e49;transform:translateY(-2px)}
.rg-card strong{font-size:18px}.rg-card small{color:#66786d}.rg-card b{color:#2c5e49;margin-top:auto}
.rg-search{width:min(100%,490px);border:1px solid #bfd0c4;border-radius:11px;padding:13px 15px;font:inherit;margin-top:9px}
.rg-districts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));align-items:start;gap:13px;margin-top:24px}
.rg-district{border:1px solid #dae3dc;border-radius:15px;overflow:hidden;background:#fff}
.rg-district summary{list-style:none;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:17px 19px;cursor:pointer;font-weight:700;color:#1d3a29}
.rg-district summary::-webkit-details-marker{display:none}
.rg-district summary:after{content:'+';font-size:22px;color:#38704b}
.rg-district[open] summary:after{content:'−'}
.rg-district summary small{margin-left:auto;color:#6a796e;font-size:12px;font-weight:500}
.rg-town-links{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;padding:6px 13px 16px}
.rg-town-links a{display:block;border-radius:9px;padding:9px 10px;background:#f1f5f0;color:#254a35!important;text-decoration:none!important;font-size:14px;overflow-wrap:anywhere}
.rg-town-links a:hover{background:#e4ede6}
.rg-town-links a[hidden],.rg-district[hidden]{display:none!important}
.rg-note{background:#eef2ec;border-radius:14px;padding:17px 19px;font-size:14px;color:#526458;line-height:1.75;margin-top:23px}
.rg-empty{display:none;color:#665f54}
@media(max-width:900px){.rg-hero-grid{grid-template-columns:1fr}.rg-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:640px){.rg-wrap{padding:0 16px}.rg-hero{padding:35px 0}.rg-panel{padding:21px}.rg-section{padding:37px 0 55px}.rg-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.rg-card{min-height:122px;padding:15px}.rg-card strong{font-size:16px}.rg-districts{grid-template-columns:1fr}.rg-town-links a{font-size:13px;padding:9px 7px}}
"""
FILTER_JS=r"""
(function(){
const box=document.getElementById('rgSearch');if(!box)return;
const all=Array.from(document.querySelectorAll('.rg-district'));
box.addEventListener('input',()=>{
 const q=box.value.trim().toLocaleLowerCase('ko');let shown=0;
 for(const district of all){
  const matchDistrict=(district.dataset.district||'').toLocaleLowerCase('ko').includes(q);
  let matches=0;
  for(const a of district.querySelectorAll('.rg-town-links a')){
   const visible=(!q||matchDistrict||a.textContent.toLocaleLowerCase('ko').includes(q));
   a.hidden=!visible;if(visible)matches++;
  }
  district.hidden=matches===0;
  if(matches){shown++;if(q)district.open=true;}
 }
 document.getElementById('rgEmpty').style.display=shown?'none':'block';
});
})();
"""
def load_rows():
 parts=[ROOT/"stage5-input"/f"production_locality_rows_5149_v1.part{i:03}.jsonl" for i in range(1,7)]
 raw=b"".join(p.read_bytes() for p in parts)
 assert hashlib.sha256(raw).hexdigest()==EXPECTED_SOURCE_SHA,"FROZEN_SOURCE_SHA_CHANGED"
 rows=[json.loads(line) for line in raw.decode("utf8").splitlines() if line.strip()]
 assert len(rows)==EXPECTED_ROWS
 assert len({r["region_slug"] for r in rows})==EXPECTED_ROWS
 assert len({r["locality_key"] for r in rows})==EXPECTED_ROWS
 assert all(r["hub_url"]=="/"+r["region_slug"]+".html" for r in rows)
 return rows
def render(base, path, title, description, body):
 html=re.sub(r"<main>[\s\S]*?</main>","<main>"+body+"</main>",base,count=1)
 html=re.sub(r"<title>[\s\S]*?</title>","<title>"+escape(title)+"</title>",html,count=1)
 html=re.sub(r'(<meta name="description" content=")[^"]*(")',lambda m:m.group(1)+escape(description,quote=True)+m.group(2),html,count=1)
 html=re.sub(r'<meta name="robots" content="[^"]*">','<meta name="robots" content="noindex,nofollow">',html,count=1)
 html=re.sub(r'(<link rel="canonical" href=")[^"]*(")',lambda m:m.group(1)+"https://englishpt.kr/"+path+m.group(2),html,count=1)
 for prop,value in [("og:title",title),("og:description",description),("og:url","https://englishpt.kr/"+path)]:
  html=re.sub(r'(<meta property="'+re.escape(prop)+r'" content=")[^"]*(")',lambda m:m.group(1)+escape(value,quote=True)+m.group(2),html,count=1)
 ld={"@context":"https://schema.org","@type":"WebPage","name":title,"url":"https://englishpt.kr/"+path,"description":description,"inLanguage":"ko-KR"}
 html=re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>','<script type="application/ld+json">'+json.dumps(ld,ensure_ascii=False)+'</script>',html,count=1)
 html=html.replace('href="assets/','href="/assets/').replace('src="assets/','src="/assets/')
 html=re.sub(r'href="(englishpt|courses|english-conversation|exam-english|student-english|stations)\.html"',lambda m:'href="https://englishpt.kr/'+m.group(1)+'.html"',html)
 html=html.replace('<nav class="desktop-nav" aria-label="주요 메뉴">','<nav class="desktop-nav" aria-label="주요 메뉴"><a href="/regions.html">지역별 찾기</a>',1)
 html=html.replace('<div id="mobileNav" class="mobile-nav" hidden><div class="wrap">','<div id="mobileNav" class="mobile-nav" hidden><div class="wrap"><a href="/regions.html">지역별 찾기</a>',1)
 html=html.replace("</head>",'<style id="enpt-region-draft-style">'+CSS+"</style></head>",1)
 html=html.replace("</body>",'<script id="enpt-region-filter">'+FILTER_JS+"</script></body>",1)
 assert 'name="englishpt-consultation"' in html and 'id="applyModal"' in html
 assert '<meta name="robots" content="noindex,nofollow">' in html
 return html
def main():
 rows=load_rows()
 original=SRC.read_text("utf8")
 assert '<form id="leadForm" name="englishpt-consultation"' in original
 if OUT.exists():raise SystemExit("HOLD_PREVIEW_OUT_ALREADY_EXISTS")
 (OUT/"regions").mkdir(parents=True)
 (OUT/"assets").mkdir()
 (OUT/"privacy").mkdir()
 PROOF.mkdir(exist_ok=True)
 for f in ("site.js","styles.css","favicon.svg"):
  shutil.copy2(ROOT/"assets"/f,OUT/"assets"/f)
 shutil.copytree(ROOT/"privacy",OUT/"privacy",dirs_exist_ok=True)
 (OUT/"_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-store\n","utf8")
 (OUT/"robots.txt").write_text("User-agent: *\nDisallow: /\n","utf8")
 grouped=defaultdict(lambda:defaultdict(list))
 subpaths={}
 all_hub_urls=set()
 for row in rows:
  province=row["sido"]; district=row["jurisdiction_full"].replace(province,"").strip() or province
  grouped[province][district].append(row)
  slug=row["region_slug"].split("-")[0]
  assert province not in subpaths or subpaths[province]==slug
  subpaths[province]=slug
  all_hub_urls.add(row["hub_url"])
 province_cards=[]
 stats=[]
 for province in sorted(grouped):
  g=grouped[province];slug=subpaths[province];num=sum(map(len,g.values()))
  province_cards.append(f'<a class="rg-card" href="/regions/{slug}.html"><small>지역별 학습 안내</small><strong>{escape(province)}</strong><small>{len(g)}개 시군구 · {num}개 동네</small><b>지역 살펴보기 →</b></a>')
  panels=[]
  for i,(district,area) in enumerate(sorted(g.items()),1):
   townlinks="".join(f'<a href="https://englishpt.kr{escape(r["hub_url"],quote=True)}" data-locality="{escape(r["region_slug"],quote=True)}" title="{escape(r["full_name_ko"],quote=True)} 지역 영어 안내">{escape(r["dong_name"])}</a>' for r in sorted(area,key=lambda x:x["dong_name"]))
   panels.append(f'<details class="rg-district" data-district="{escape(district,quote=True)}" id="district-{i}"><summary><span>{escape(district)}</span><small>{len(area)}개 동네</small></summary><div class="rg-town-links">{townlinks}</div></details>')
  body=f"""<div class="breadcrumb wrap" aria-label="현재 위치"><a href="https://englishpt.kr/englishpt.html">잉글리시PT</a><span>/</span><a href="/regions.html">전국 지역 찾기</a><span>/</span><strong>{escape(province)}</strong></div><section class="rg-hero"><div class="rg-wrap rg-hero-grid"><div><div class="rg-label">ENGLISH PT · 지역별 영어</div><h1>{escape(province)}<br>우리 동네 영어 안내</h1><p class="rg-lead">시군구를 선택하고 동네를 찾으면 기존 지역별 영어과외·영어회화 안내로 이어집니다. 어떤 과정이 적합한지 정하지 못했어도 괜찮습니다.</p><div class="rg-actions"><a href="#rgDistricts" class="rg-btn">시군구 선택하기 →</a><a href="/regions.html" class="rg-btn rg-btn--alt">전국 지역 목록</a></div></div><aside class="rg-panel"><div class="rg-label">REGION GUIDE</div><strong>{len(g)}개 시군구 · {num}개 동네</strong><p>같은 이름의 동네는 시군구까지 확인하세요. 실제 수업 과정은 상세페이지마다 다를 수 있습니다.</p><button class="rg-btn" type="button" data-open-form>체험수업 신청 →</button></aside></div></section><section class="rg-section" id="rgDistricts"><div class="rg-wrap"><div class="rg-label">시군구 · 읍면동</div><h2>우리 동네를 찾아보세요.</h2><p class="rg-lead">시군구를 펼치거나 검색창에 동네 이름을 입력하면 해당 지역 상세 안내로 이동할 수 있습니다.</p><div style="margin-top:22px"><label class="rg-label" for="rgSearch">시군구·동네 검색</label><input class="rg-search" id="rgSearch" type="search" placeholder="예: 사직동, 종로구" autocomplete="off"></div><div class="rg-districts">{''.join(panels)}</div><p class="rg-empty" id="rgEmpty">해당 지역이 없습니다. 다른 이름으로 검색해보세요.</p><div class="rg-note">지역 상세페이지는 기존 운영 URL을 연결합니다. 이번 Draft에서는 원래의 색인 정책·상담 수신 기능·사이트맵을 변경하지 않습니다.</div></div></section>"""
  path=f"regions/{slug}.html"
  (OUT/path).write_text(render(original,path,province+" 읍면동별 영어 안내 | ENGLISH PT",province+" 지역 시군구별 영어과외와 영어회화 학습 안내",body),"utf8")
  stats.append({"sido":province,"slug":slug,"districts":len(g),"localities":num,"page":path})
 main_body=f"""<div class="breadcrumb wrap" aria-label="현재 위치"><a href="https://englishpt.kr/englishpt.html">잉글리시PT</a><span>/</span><strong>전국 지역별 영어 찾기</strong></div><section class="rg-hero"><div class="rg-wrap rg-hero-grid"><div><div class="rg-label">ENGLISH PT · 전국 지역찾기</div><h1>우리 동네에서<br>필요한 영어를 찾아보세요.</h1><p class="rg-lead">어느 지역에서 공부하고 싶으신가요? 시도부터 읍면동까지 선택하고, 영어과외·영어회화·시험영어를 비교해 보세요.</p><div class="rg-actions"><a href="#rgProvinces" class="rg-btn">지역 선택하기 →</a><button class="rg-btn rg-btn--alt" type="button" data-open-form>체험수업 신청</button></div></div><aside class="rg-panel"><div class="rg-label">REGION FINDER</div><strong>시도 → 시군구 → 읍면동</strong><p>원하는 동네를 선택한 다음 지역 상세 안내를 확인하세요. 수업 선택이 어렵다면 목표와 희망 지역만 남겨도 됩니다.</p><div class="rg-stats"><span>{len(grouped)}개 시도</span><span>{sum(map(len,grouped.values()))}개 시군구 구분</span><span>{len(rows):,}개 동네</span></div></aside></div></section><section id="rgProvinces" class="rg-section"><div class="rg-wrap"><div class="rg-label">전국 지역 선택</div><h2>어느 지역을 찾으시나요?</h2><p class="rg-lead">시도를 선택하면 각 시군구와 동네 목록이 표시됩니다.</p><div class="rg-grid">{''.join(province_cards)}</div><div class="rg-note">해당 페이지는 검토용 Draft입니다. 기존 운영본의 검색 설정과 색인 허용 정책은 그대로 유지됩니다.</div></div></section><section class="final"><div class="wrap final-box"><div><div class="eyebrow">체험수업 상담</div><h2>동네를 선택하지 못하셨나요?</h2><p>현재 학습 목표와 희망 지역을 남겨주시면 안내드릴 수 있는 방향을 정리합니다.</p></div><button class="btn light" type="button" data-open-form>체험수업 신청 →</button></div></section>"""
 (OUT/"regions.html").write_text(render(original,"regions.html","전국 지역별 영어 찾기 | ENGLISH PT","전국 시도·시군구·읍면동별 영어과외·영어회화·시험영어 학습 안내를 찾아보세요.",main_body),"utf8")
 htmls=list(OUT.rglob("*.html"))
 assert len([p for p in htmls if p.name.endswith(".html") and ("regions" in p.parts or p.name=="regions.html")])==18
 assert sum(x["localities"] for x in stats)==5149
 links=[]
 for p in OUT.rglob("*.html"):
  if p.parent.name=="regions":
   links+=re.findall(r'href="https://englishpt.kr(/[a-z0-9-]+\.html)" data-locality=',p.read_text("utf8"))
 assert set(links)==all_hub_urls and len(links)==len(all_hub_urls)
 # Core site and original source may never be rewritten by this generator.
 result={"status":"PASS_DRAFT_STATIC_GENERATED","sidos":len(grouped),"localities":len(rows),"unique_public_locality_routes":len(links),"new_region_html":18,"preview_index_blocked":True,"original_core_files_changed":0,"production_deploys":0,"form_name":"englishpt-consultation","stats":stats}
 (PROOF/"STATIC_REGION_DRAFT_QA.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),"utf8")
 print("ENPT_REGION_DRAFT_STATIC_QA",json.dumps({k:v for k,v in result.items() if k!="stats"},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
