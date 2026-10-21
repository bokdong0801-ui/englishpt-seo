#!/usr/bin/env python3
"""Consolidate 910 elementary station course pages into navigation + one educational guide.
Only changes a LOCAL extracted full-site Draft candidate. No Production or network.
Existing 910 URL/robots/canonical/OG/form/sitemap/Edge remain unchanged.
New guide is intentionally noindex,follow until separately approved for indexing.
"""
import csv,gzip,hashlib,html,json,pathlib,re
from collections import Counter,defaultdict
ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/"thumb-21964-candidate"
OUT=ROOT/"p3-guide-nav-qa";OUT.mkdir(exist_ok=True)
DATA=json.loads((ROOT/"data/stations.json").read_text(encoding="utf-8"))["stations"]
OFFICIAL=json.loads((ROOT/"data/stations-official15-verified-overrides-v1.json").read_text(encoding="utf-8"))["rows"]
with gzip.open(ROOT/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz","rt",encoding="utf8") as f:
 signed=json.load(f)
MP=signed["original_public_html_to_data_payload"]
assert len(DATA)==911 and len(MP)==158571 and len(OFFICIAL)==15
VERIFIED={x["slug"]:x for x in OFFICIAL}
STATION={x["slug"]:x for x in DATA}
assert len(STATION)==911 and len(VERIFIED)==15
KEEP=["hero","consult","related","nearby-localities","final","enpt-official-station-address"]
SECTIONS=re.compile(r'<section\b[^>]*>.*?</section\s*>',re.I|re.S)
SECTION_OPEN=re.compile(r'<section\b[^>]*>',re.I)
CLASS=re.compile(r'\bclass\s*=\s*"([^"]*)"',re.I)
HEAD=re.compile(r'<head\b[^>]*>.*?</head\s*>',re.I|re.S)
FORM=re.compile(r'<form\b[^>]*name=["\']englishpt-consultation["\']',re.I)
def esc(s):return html.escape(str(s),quote=True)
def sha(s):return hashlib.sha256(s.encode("utf8")).hexdigest()
def loc_links(st):
 nearby=[]
 for slug in st.get("nearby") or []:
  other=STATION.get(slug)
  if other and other["slug"]!=st["slug"] and other["slug"]!=slug:continue
  if other and other["slug"]!=st["slug"] and other["slug"] not in {x["slug"] for x in nearby}:nearby.append(other)
 return nearby[:5]
def menu(st):
 slug=st["slug"];name=esc(st["name"])
 first=f'/station-{slug}.html'
 nearby=loc_links(st)
 if st["slug"] in VERIFIED:
  official=VERIFIED[st["slug"]]
  status=f'<p class="enpt-region-proof"><strong>공식 확인된 역 주소:</strong> {esc(official["verified_address"])}'
  status+=' · 학원 위치 또는 수업 장소를 뜻하지 않습니다.</p>'
 else:
  status='<p class="enpt-region-proof">이 역의 실제 수업 위치와 교습 가능 여부는 확인되지 않았습니다. 위치·방식은 상담 전에 확인하세요.</p>'
 routes=[("중학생 영어",f'/station-{slug}-mid-conv.html'),("고등학생 영어",f'/station-{slug}-high-conv.html'),("왕초보 회화",f'/station-{slug}-beginner-english-conv.html'),("성인 회화",f'/station-{slug}-adult-english-conv-academy.html'),("토익",f'/station-{slug}-toeic.html')]
 for _,u in routes:assert u.lstrip("/") in MP
 chips="".join(f'<a class="enpt-route-chip" href="{u}">{esc(label)}</a>' for label,u in routes)
 near="".join(f'<a class="enpt-route-chip" href="/station-{esc(s["slug"])}.html">{esc(s["name"])}</a>' for s in nearby)
 return (
 '<section class="section enpt-elementary-station-directory" data-enpt-elemdir="20261021" id="detail" aria-label="역별 영어과외 과정 탐색">'
 '<div class="wrap">'
 '<p class="kicker">초등 영어과외 · 역별 과정 찾기</p>'
 f'<h2>{name}에서 초등 영어 수업을 찾으시나요?</h2>'
 '<p>역 이름과 영어과외 수업 가능 지역은 같다고 단정할 수 없습니다. 위치를 먼저 확인하고, 공부 방법은 공통 가이드에서 자세히 살펴보세요.</p>'
 f'{status}'
 '<div class="enpt-dir-panel"><h3>학부모를 위한 초등 영어 학습 가이드</h3>'
 '<p>읽기·어휘·문장 이해·복습 점검까지, 필요한 기준을 한 페이지에서 확인할 수 있습니다.</p>'
 '<a class="btn" href="/elementary-english-guide.html">초등 영어 학습 가이드 자세히 보기 →</a></div>'
 f'<div class="enpt-dir-panel"><h3>{name} 다른 영어 과정</h3><nav aria-label="역별 다른 영어 과정">{chips}<a class="enpt-route-chip" href="{first}">이 역의 전체 과정 보기</a></nav></div>'
 f'<div class="enpt-dir-panel"><h3>다른 역으로 찾아보기</h3><nav aria-label="같은 노선의 다른 역">{near}'
 '<a class="enpt-route-chip" href="/stations.html">911개 역 전체 검색하기</a></nav></div>'
 '</div></section>')
def check_head(old,new,route):
 assert HEAD.search(old) and HEAD.search(new)
 assert HEAD.search(old).group()==HEAD.search(new).group(),route+":head"
 assert len(FORM.findall(old))==len(FORM.findall(new))==1,route+":forms"
 for marker in ('name="robots"','rel="canonical"','property="og:image"','name="google-site-verification"','name="naver-site-verification"'):
  assert old.count(marker)==new.count(marker),route+":"+marker
 assert '<meta name="robots" content="index,follow' in new,route+":index"
 assert new.count('data-enpt-elemdir="20261021"')==1,route+":navigation"
 assert "elementary-english-guide.html" in new,route+":guide-link"
 assert len(re.findall(r'<section\b',new,re.I))==len(re.findall(r'</section\s*>',new,re.I)),route+":unbalanced-sections"
def simplify(old,st):
 removed=[]
 def change(m):
  seg=m.group(0)
  opening=SECTION_OPEN.match(seg).group(0)
  cls=CLASS.search(opening)
  parts=cls.group(1).split() if cls else []
  if any(k in parts for k in KEEP):return seg
  # Main-page generic content consolidated into the shared, more complete guide.
  removed.append(" ".join(parts) if parts else "(plain-section)")
  return ""
 # Scope only main; preserve header/footer scripts/consultation dialog untouched.
 hit=re.search(r'(<main\b[^>]*>)(.*?)(</main\s*>)',old,re.S|re.I)
 assert hit,st["slug"]+":main"
 body=SECTIONS.sub(change,hit.group(2))
 assert len(removed)>=7,(st["slug"],removed)
 # Anchor formerly "detail" now points to new navigation section.
 body=menu(st)+body
 new=old[:hit.start(2)]+body+old[hit.end(2):]
 return new,removed
oldcrit={}
for x in ("robots.txt","sitemap-index.xml","_redirects","_headers","netlify.toml","netlify/edge-functions/shard-router.js"):
 p=SITE/x;oldcrit[x]=p.read_bytes()
 assert hashlib.sha1(oldcrit[x]).hexdigest()==signed["target_SHA1_by_path"][x]
rows=[]
for st in DATA:
 if st["slug"]=="gukjegeumyungsenteo-busaneunhaeng":continue
 route=f'station-{st["slug"]}-elem-tutor.html'
 v=MP[route];assert v["noindex"] is False
 page=SITE/v["to"]];old=page.read_text("utf8")
 assert 'data-enpt-p0="20261021"' in old and 'data-enpt-learning-evidence="20261021"' in old
 new,removed=simplify(old,st)
 check_head(old,new,route)
 page.write_text(new,"utf8")
 rows.append({"route":route,"old_chars":len(old),"new_chars":len(new),"removed_sections":"|".join(removed),"validated_official_station":st["slug"] in VERIFIED,"old_sha256":sha(old),"new_sha256":sha(new),"new_guide_link":"/elementary-english-guide.html"})
assert len(rows)==910
GUIDE=r'''<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>초등 영어과외 학습 가이드 | 읽기·문장·복습 단계별 안내</title>
<meta name="description" content="초등 영어과외를 알아보는 학부모를 위한 읽기·문장 이해·쓰기·복습 점검과 상담 준비 가이드입니다.">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="https://englishpt.kr/elementary-english-guide.html">
<link rel="stylesheet" href="/assets/styles.css">
<style>
body{background:#f2faf6;color:#183c2c} .eg-wrap{max-width:920px;margin:auto;padding:24px}
.eg-hero{padding:60px 0;background:#164738;color:#fff}.eg-hero h1{font-size:clamp(28px,5vw,44px);color:#fff;line-height:1.3}.eg-hero p{color:#e1f5e9}
.eg-card{margin:20px 0;padding:clamp(22px,4vw,36px);background:#fff;border:1px solid #d8eadd;border-radius:19px}
.eg-card h2{color:#164738;line-height:1.4}.eg-card p,.eg-card li{line-height:1.9}
.eg-lesson{padding:14px 18px;background:#eef8f0;border-left:4px solid #28936b;border-radius:10px}
.eg-menu a{display:inline-flex;margin:6px;padding:10px 16px;background:#e1f2e8;color:#15563b;border:1px solid #bcdcc8;border-radius:30px;text-decoration:none;font-weight:650}
.eg-note{border:1px solid #e0d5be;background:#fff9ea;padding:17px;border-radius:13px}
@media(max-width:640px){.eg-wrap{padding:16px}.eg-hero{padding:38px 0}.eg-card{margin:14px 0}}
</style>
</head><body>
<header class="eg-wrap"><a href="/englishpt.html">홈으로</a> · <a href="/stations.html">역으로 찾기</a></header>
<main>
<section class="eg-hero"><div class="eg-wrap"><p>초등 영어 학습 가이드</p><h1>우리 아이 영어, 무엇부터 확인해야 할까요?</h1><p>파닉스만으로 판단하지 않고, 읽기·이해·문장 사용·복습을 나누어 확인하는 학부모용 실전 가이드입니다.</p></div></section>
<div class="eg-wrap">
<nav class="eg-menu" aria-label="가이드 목차"><a href="#reading">읽기 점검</a><a href="#grammar">문장 이해</a><a href="#routine">복습 습관</a><a href="#consult">상담 준비</a></nav>
<section class="eg-card" id="reading"><h2>1. 단어를 읽는 것과 문장을 이해하는 것은 다릅니다</h2>
<p>아이가 단어를 또박또박 소리 내어 읽더라도 문장의 핵심을 설명하지 못할 수 있습니다. 이때는 암기할 단어를 늘리기보다 누가 무엇을 하는지, 장소와 시점이 어디인지부터 구분하는 편이 좋습니다.</p>
<div class="eg-lesson"><strong>확인 예문</strong><p>The rabbit is behind the tree.</p><p>단순히 문장을 따라 읽는 것을 넘어, 토끼가 나무의 어느 쪽에 있는지 그림으로 표현하게 해보세요. 익숙해지면 behind 대신 next to를 넣어 의미가 어떻게 달라지는지도 확인합니다.</p></div>
<p>아이가 이해하지 못했다면 바로 답을 알려주기보다 문장의 짧은 구간을 나누어 설명하게 합니다. 반대로 의미를 정확히 설명한다면 같은 문제를 반복하기보다 새로운 문장으로 옮겨가도 됩니다.</p></section>
<section class="eg-card" id="grammar"><h2>2. 학년에 맞추기 전에 문장 이해 수준을 확인하세요</h2>
<p>초4·초5·초6이라는 학년 정보는 학습 계획의 출발점일 뿐입니다. 영어학습 경험, 독립적으로 읽는 수준, 학교 숙제의 어려움이 다를 수 있으므로 실제 문장을 근거로 확인해야 합니다.</p>
<div class="eg-lesson"><strong>확인 예문</strong><p>Jisu met Hana, and she smiled.</p><p>she가 누구를 가리키는지 분명하지 않을 수 있음을 발견하도록 질문합니다. 문장을 무조건 외우는 것보다 정보가 애매할 때 이를 알아차리고 분명한 문장으로 고치는 능력을 살펴볼 수 있습니다.</p></div>
<p>기본 문장을 쓸 수 있다면 시간 표현을 바꾸거나 의문문으로 고쳐봅니다. 틀린 부분을 지적할 때는 어순·단어 뜻·시제 중 어느 점이 어려웠는지 나누어 기록합니다.</p></section>
<section class="eg-card" id="routine"><h2>3. 복습은 같은 문제의 반복만을 의미하지 않습니다</h2>
<p>한 번 푼 문제를 다시 맞히는 것만으로 학습 내용이 남았다고 판단하기 어렵습니다. 하루 뒤에는 단어를 바꾸고, 이틀 뒤에는 상황을 바꾼 문제를 풀며 배운 내용을 적용할 수 있는지 확인합니다.</p>
<div class="eg-lesson"><strong>간단한 복습 기록 예시</strong><p>① 오늘 이해한 문장 1개 ② 혼자 해결하지 못한 부분 1개 ③ 이틀 뒤 다시 풀 문제 1개를 적습니다.</p></div>
<p>짧더라도 기록한 어려움이 다음 공부로 이어지면 도움이 됩니다. 읽기·듣기·쓰기 가운데 무엇을 우선해야 할지는 실제 어려움을 본 뒤 정해야 합니다.</p></section>
<section class="eg-card" id="consult"><h2>4. 과외·학원·화상수업을 비교할 때 준비할 것</h2>
<p>수업 방식을 먼저 정하기보다 아이가 어려워하는 실제 문제를 준비하면 상담을 더 구체적으로 진행할 수 있습니다.</p>
<ul><li>최근 영어 과제 또는 틀린 문제 1~2개</li><li>혼자 공부할 때 도움을 요청하는 상황</li><li>일주일에 실제로 복습할 수 있는 시간</li><li>수업 후 어떤 방식으로 변화 여부를 확인할지</li><li>방문·화상·학원 중 실제 가능한 시간대와 위치</li></ul>
<p>상담에서는 지도 가능 학년, 담당 강사의 수업 방식, 실제 가능한 수업 시간과 비용을 확인하는 것이 좋습니다. 특정 지역에서 수업이 가능하다고 확정하지 않은 상태에서는 역 이름만 보고 학습 기관의 위치를 추측하지 마세요.</p>
<p class="eg-note"><strong>안내:</strong> 본 페이지는 일반적인 학습 정보입니다. 학생의 실제 상태를 진단하거나 특정 수업의 성과를 보장하지 않습니다.</p>
<a class="btn" href="/stations.html">역 목록으로 돌아가서 과정 비교하기 →</a></section>
</div></main><footer class="eg-wrap"><a href="/englishpt.html">홈페이지</a> · <a href="/stations.html">전국 역 찾기</a></footer></body></html>'''
GUIDEFILE=SITE/"elementary-english-guide.html"
assert not GUIDEFILE.exists()
GUIDEFILE.write_text(GUIDE,encoding="utf8")
assert 'name="robots" content="noindex,follow"' in GUIDE
for file,contents in oldcrit.items():
 assert (SITE/file).read_bytes()==contents,file
assert len(list((SITE/"__pages").glob("*/*.page")))==158571
# All excluded SEO originals still byte-identical; noindex set deliberately unchanged.
for route,record in MP.items():
 if record["noindex"]:
  raw=(SITE/record["to"]).read_bytes()
  assert hashlib.sha1(raw).hexdigest()==record["sha1"],route
with (OUT/"ALL_910_NAVIGATION_PATCH.csv").open("w",newline="",encoding="utf-8-sig") as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
c=Counter()
for r in rows:
 for x in r["removed_sections"].split("|"):c[x]+=1
summary={"status":"PASS_P3_910_CONTENT_CONSOLIDATION_GUIDE_AND_NAV","station_pages":910,"shared_guide_path":"/elementary-english-guide.html","shared_guide_robots":"noindex,follow","guide_added_to_sitemap":False,"station_index_policy_changed":False,"canonical_and_form_unchanged":True,"136607_noindex_source_unchanged":True,"158571_edge_page_count_preserved":True,"removed_sections":dict(c),"production_published":False}
(OUT/"P3_GUIDE_NAV_QA.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
print("P3_910_GUIDE_NAV_FINAL",json.dumps(summary,ensure_ascii=False),flush=True)
