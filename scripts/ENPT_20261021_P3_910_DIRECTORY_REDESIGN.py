#!/usr/bin/env python3
"""QA only. Turn 910 station elementary pages into truthful local-navigation pages.
Shared learning content lives on one separate national guide URL (created after signed manifest QA).
Never edits <head>, robots, canonical, forms, sitemaps, source station slugs or Production.
"""
import csv,gzip,hashlib,html,json,pathlib,re
root=pathlib.Path(__file__).resolve().parents[1]
site=root/"thumb-21964-candidate"
out=root/"p3-elementary-architecture-qa";out.mkdir(exist_ok=True)
stations=json.loads((root/"data/stations.json").read_text(encoding="utf8"))["stations"]
official={s["slug"]:s for s in json.loads((root/"data/stations-official15-verified-overrides-v1.json").read_text("utf8"))["rows"]}
with gzip.open(root/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz","rt",encoding="utf8") as f:
 source=json.load(f)["original_public_html_to_data_payload"]
assert len(stations)==911 and len(official)==15 and len(source)==158571
other={s["slug"]:s for s in stations}
exempt={"gukjegeumyungsenteo-busaneunhaeng"}
def e(s):return html.escape(str(s),quote=True)
def extract_head(s):
 m=re.search(r"<head\b[^>]*>.*?</head>",s,re.S|re.I)
 assert m
 return m.group()
def make_main(st):
 slug=st["slug"];name=e(st["name"])
 location=official.get(slug)
 neighbors=[other[x] for x in (st.get("nearby") or []) if x in other and x!=slug][:5]
 links=''.join(f'<a href="/station-{e(x["slug"])}-elem-tutor.html">{e(x["name"])}</a>' for x in neighbors if x["slug"] not in exempt)
 station_address=('<p class="elementary-station-address">철도역 공식 주소: '+e(location["verified_address"])+' <span>※ 학원 주소나 수업 장소가 아닙니다.</span></p>') if location else '<p class="elementary-station-address">이 역의 공식 주소 정보는 아직 검증되지 않았습니다. 실제 수업 가능 지역과 이동 시간은 개별 상담에서 확인해 주세요.</p>'
 line=e(" · ".join(st.get("lines") or [])) or "노선 정보 확인 필요"
 return f'''<main id="main-content" class="enpt-directory-main" data-enpt-directory-role="station-elementary-v1">
 <style>
 .enpt-directory-main{{background:#f3f9f5;color:#183c2e;padding:36px 0 65px}}
 .enpt-directory-main .directory-wrap{{max-width:1050px;margin:0 auto;padding:0 20px}}
 .enpt-directory-main h1{{font-size:clamp(28px,4vw,44px);line-height:1.3;letter-spacing:-.035em}}
 .enpt-directory-main .directory-card{{background:#fff;border:1px solid #d5e9da;border-radius:20px;padding:23px;margin:20px 0;box-shadow:0 8px 24px rgba(11,60,35,.06)}}
 .enpt-directory-main .directory-links{{display:flex;gap:11px;flex-wrap:wrap;margin-top:17px}}
 .enpt-directory-main .directory-links a,.enpt-directory-main .directory-guide{{display:inline-flex;align-items:center;min-height:46px;background:#e6f5eb;border:1px solid #a9d3b6;border-radius:11px;padding:10px 15px;color:#16583e;font-weight:750;text-decoration:none}}
 .enpt-directory-main .directory-guide{{background:#185c47;color:#fff;border-color:#185c47}}
 .enpt-directory-main .directory-intro{{color:#3a6250;line-height:1.75}}
 .enpt-directory-main .elementary-station-address{{padding:13px 15px;background:#f4f9fc;border-radius:12px}}
 .enpt-directory-main .elementary-station-address span{{font-size:13px}}
 @media(max-width:640px){{.enpt-directory-main{{padding:28px 0 45px}}.enpt-directory-main .directory-card{{padding:18px}}.enpt-directory-main .directory-links a{{width:100%}}}}
 </style>
 <div class="directory-wrap">
 <p class="directory-intro">역별 영어과외 과정 찾기 · 실제 수업 지역은 상담으로 확인</p>
 <h1>{name} 초등 영어과외 안내</h1>
 <p class="directory-intro">이 페이지는 {name}을 기준으로 학습 과정을 찾아보는 안내입니다. 역 주변에 특정 학원이나 선생님이 실제로 운영된다는 의미는 아닙니다.</p>
 <section class="directory-card">
 <h2>{name} 역 정보</h2><p>원본 노선 데이터: {line}</p>{station_address}
 <p>역 이름이 같아도 다른 지역의 역일 수 있습니다. 수업을 신청하기 전 주소와 노선을 한 번 더 확인해 주세요.</p>
 </section>
 <section class="directory-card">
 <h2>초등 영어는 공통 학습 가이드에서 확인하세요</h2>
 <p>초등 영어 시작 수준, 문장 읽기, 기본 어순, 단어 활용, 복습과 학부모 점검 항목은 모든 역에서 공통으로 활용할 수 있는 학습 정보입니다. 역마다 같은 공부 방법을 반복 게시하지 않고 하나의 안내로 정리했습니다.</p>
 <a class="directory-guide" href="/elementary-english-guide.html">초등 영어과외 학습 가이드 읽기 →</a>
 </section>
 <section class="directory-card">
 <h2>다른 과정이나 인접 역을 찾아보세요</h2>
 <p>학년·영어 목적에 맞춰 과정 안내를 비교하고, 역 탐색이 필요한 경우 연결된 다른 역도 확인할 수 있습니다.</p>
 <div class="directory-links">
 <a href="/station-{e(slug)}.html">{name} 전체 영어 과정</a>
 <a href="/stations.html">전국 911개 역 검색</a>
 {links}
 </div>
 </section>
 <section class="directory-card">
 <h2>상담하기 전 확인할 사항</h2>
 <p>학생 학년, 영어에서 가장 어려운 부분, 희망하는 수업 방식, 방문·화상 가능 여부와 실제 이동 지역을 미리 확인해 주세요. 이 페이지는 학습 정보를 제공할 뿐 특정 지역의 수업 운영 여부를 보증하지 않습니다.</p>
 <button type="button" data-open-form class="btn primary">영어 상담 신청하기</button>
 </section>
 </div></main>'''
count=0;rows=[]
for st in stations:
 if st["slug"] in exempt:continue
 route="station-"+st["slug"]+"-elem-tutor.html"
 entry=source[route];assert not entry["noindex"]
 p=site/entry["to"]
 old=p.read_text("utf8")
 head=extract_head(old)
 a=re.search(r"<main\b[^>]*>.*?</main>",old,re.S|re.I);assert a,(route,"MAIN")
 fresh=old[:a.start()]+make_main(st)+old[a.end():]
 assert extract_head(fresh)==head and old.count('name="englishpt-consultation"')==fresh.count('name="englishpt-consultation"'),route
 assert fresh.count('data-enpt-directory-role="station-elementary-v1"')==1
 assert old.count('name="robots"')==fresh.count('name="robots"')
 p.write_text(fresh,"utf8")
 rows.append({"route":route,"official_location":"verified" if st["slug"] in official else "unverified","before_bytes":len(old.encode()),"after_bytes":len(fresh.encode()),"source":entry["to"],"head_sha256":hashlib.sha256(head.encode()).hexdigest()})
 count+=1
assert count==910
with (out/"910_DIRECTORY_REWRITE_AUDIT.csv").open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
report={"status":"PASS_910_DIRECTORY_REDESIGN_INDEX_POLICY_IMMUTABLE","rewritten_station_elem_pages":count,"original_robots_canonical_all_unchanged":True,"form_markup_all_unchanged":True,"official_station_address_count":sum(r["official_location"]=="verified" for r in rows),"pending_station_locations":sum(r["official_location"]=="unverified" for r in rows),"national_guide_route":"/elementary-english-guide.html","guide_to_be_created_after_signed_full_site_QA":True,"sitemaps_unchanged":True,"production_published":False}
(out/"ARCHITECTURE_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
print("ENPT_910_DIRECTORY_P3",json.dumps(report,ensure_ascii=False),flush=True)
