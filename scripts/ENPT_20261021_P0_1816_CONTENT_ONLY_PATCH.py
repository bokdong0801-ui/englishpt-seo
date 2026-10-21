#!/usr/bin/env python3
"""P0 content-only patch to locally extracted candidate. No network, no deploy, no geography guess."""
import collections,csv,gzip,hashlib,html,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1];SITE=ROOT/"thumb-21964-candidate"
SIGNED=ROOT/"signed-qa-map"/"NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
STATIONS=json.loads((ROOT/"data/stations.json").read_text("utf8"))["stations"]
TARGET_EXEMPT_HUB={"incheonairport-t1","busandaeyangsankaempeoseu","gukjegeumyungsenteo-busaneunhaeng","toseong","bokhammunhwayunghapdanji"}
TARGET_EXEMPT_ELEM={"gukjegeumyungsenteo-busaneunhaeng"}
SUSPECT_MERGED={"금곡역","중앙역","대공원역","양정역","용산역"}
OUT=ROOT/"p0-nonpublished-qa";OUT.mkdir(exist_ok=True)
assert len(STATIONS)==911 and len({s["slug"] for s in STATIONS})==911
with gzip.open(SIGNED,"rt",encoding="utf8") as f:manifest=json.load(f)
mapping=manifest["original_public_html_to_data_payload"]
assert len(mapping)==158571 and sum(not x["noindex"] for x in mapping.values())==21964
original_checks={rel:(SITE/rel).read_bytes() for rel in ("robots.txt","_headers","_redirects","netlify.toml","sitemap-index.xml","netlify/edge-functions/shard-router.js")}
for k,raw in original_checks.items():assert hashlib.sha1(raw).hexdigest()==manifest["target_SHA1_by_path"][k],k
def norm(x):return re.sub(r"\s+"," ",html.unescape(re.sub("<[^>]+>"," ",x))).strip()
def local_context(st):
 n=st["name"];lines=st.get("lines") or [];neighbors=st.get("nearby") or []
 other={x["slug"]:x["name"] for x in STATIONS}
 nearby=[other[s] for s in neighbors if s in other and other[s]!=n][:4]
 # No assertion about physical proximity, institute existence, specific schedules, area demographics.
 line_text=" · ".join(lines) if lines else "노선 정보 확인 필요"
 return n,line_text,nearby
def add_section(st,kind):
 name,lines,nearby=local_context(st)
 linked=", ".join(nearby) if nearby else "전국 역 찾기"
 esc=lambda x:html.escape(x,quote=False)
 if kind=="hub":
  target=f"/station-{st['slug']}-elem-tutor.html"
  exam=f"/station-{st['slug']}-toeic.html"
  intro="학생 영어, 회화, 시험영어 중 무엇을 선택해야 할지 헷갈릴 때는 실제로 평가받거나 사용해야 하는 영어부터 나눕니다."
  details=(
   f"{name} 안내에서 표시하는 노선은 {lines}입니다. 역명만으로 학습 기관의 위치나 수업 가능 범위를 추정하지 않고, 먼저 학생의 학년과 영어가 필요한 상황을 확인합니다.",
   f"이 역 안내에서 함께 찾아볼 수 있는 역 이름은 {linked}입니다. 이 이름은 다른 지역 안내 페이지를 비교하기 위한 탐색 정보이며, 해당 역마다 동일한 수업이 개설됐다는 뜻은 아닙니다.",
   f"학교 영어라면 학년·최근 시험지·수행평가 내용을 먼저 확인하고, 시험영어라면 목표 시험·시험일·현재 점수를 분리합니다. 영어회화라면 여행·생활·업무 중 바로 사용할 상황과 시작 가능한 문장 수준을 선택 기준으로 삼습니다."
  )
  cards=(
   f'<a href="{target}">초등 영어과외에서 읽기·기초 점검 보기</a>',
   f'<a href="{exam}">토익 시험 영어에서 LC·RC 학습 기준 보기</a>'
  )
 else:
  target=f"/station-{st['slug']}.html"
  intro="초등 영어과외를 선택할 때는 현재 읽을 수 있는 단어의 수보다 아이가 혼자 읽고 뜻을 설명할 수 있는 문장 범위를 먼저 확인하는 편이 좋습니다."
  details=(
   f"{name} 역 안내에는 {lines} 노선 정보가 연결돼 있습니다. 학생이 이동하는 역과 실제 수업 지역은 같다고 단정할 수 없으므로 상담 전 가능한 학습 방식과 위치를 따로 확인하세요.",
   f"같은 역 안내에서 비교할 수 있는 역 이름은 {linked}입니다. 지점이 실제로 운영되는지와 통학 가능성은 역 이름만으로 보장되지 않으므로 확인 항목으로 남겨둡니다.",
   f"학부모는 최근 읽기 과제 한 개, 틀린 문제 두 개, 아이가 스스로 질문한 내용 한 가지를 준비할 수 있습니다. 첫 상담에서는 읽기 이해·기본 문장·혼자 복습하는 시간으로 나누어 필요한 도움을 구체화합니다."
  )
  cards=(f'<a href="{target}">역별 23개 과정 비교 화면으로 이동</a>',)
 h=f'<section class="section station-p0-editorial" data-enpt-p0="20261021" aria-label="역별 학습 과정 선택 가이드"><div class="wrap">'
 h+=f'<p class="kicker">학습 선택 가이드</p><h2>{esc(name)}에서 현재 상황에 맞는 영어 과정을 고르는 법</h2><p>{esc(intro)}</p>'
 h+="".join("<p>"+esc(x)+"</p>" for x in details)
 h+=f'<div class="links">{" ".join(cards)}</div></div></section>'
 return h
def hmeta(b):
 h=re.search(rb"<head\b[^>]*>.*?</head>",b,re.I|re.S)
 assert h,"no head"
 return h.group(0)
def form_count(b):return b.count(b'name="englishpt-consultation"')
total=collections.Counter();rows=[]
for st in STATIONS:
 slug=st["slug"]
 for kind,exempt in (("hub",TARGET_EXEMPT_HUB),("elem-tutor",TARGET_EXEMPT_ELEM)):
  if slug in exempt:continue
  route="station-"+slug+("-"+kind if kind!="hub" else "")+".html"
  ref=mapping.get(route)
  assert ref and ref["noindex"] is False,route
  path=SITE/ref["to"];old=path.read_bytes()
  assert b'data-enpt-p0="20261021"' not in old,route
  assert b"<main" in old and b"</main>" in old,route
  section=add_section(st,kind).encode("utf8")
  # HTML only; all head elements, forms, canonical, robots, structured data unchanged.
  new=old.replace(b"</main>",section+b"</main>",1)
  assert hmeta(old)==hmeta(new) and form_count(old)==form_count(new),route
  assert old.count(b"</main>")==1 and new.count(b"</main>")==1,route
  path.write_bytes(new)
  total[kind]+=1
  rows.append({"route":route,"type":kind,"source":ref["to"],"previous_content_sha256":hashlib.sha256(old).hexdigest(),"patched_content_sha256":hashlib.sha256(new).hexdigest(),"added_bytes":len(section),"metadata_unchanged":True,"forms_unchanged":True})
assert total=={"hub":906,"elem-tutor":910},total
for rel,raw in original_checks.items():assert (SITE/rel).read_bytes()==raw,rel
assert len(list((SITE/"__pages").glob("*/*.page")))==158571
with (OUT/"P0_PATCHED_ROUTES.csv").open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
rep={"status":"PASS_1816_INDEXABLE_HTML_P0_CONTENT_ONLY","hub_patched":total["hub"],"elem_tutor_patched":total["elem-tutor"],"indexable_before_after":21964,"noindex_before_after":136607,"meta_header_immutable":True,"form_unchanged":True,"robots_sitemap_edge_redirects_immutable":True,"official_address_change_count":0,"explicit_no_invented_geography":True,"production_published":False}
(OUT/"P0_CONTENT_ONLY_REPORT.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2))
print("P0_PATCH_CONTENT_ONLY",json.dumps(rep,ensure_ascii=False),flush=True)
