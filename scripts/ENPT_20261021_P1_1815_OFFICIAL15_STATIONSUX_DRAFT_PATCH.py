#!/usr/bin/env python3
"""QA-only P1: 1815 high-repeat page learning guides + official 15 station areas + stations UX.
Operates only on extracted local Draft candidate, never Production. Never touches 136607 noindex.
"""
import collections,csv,gzip,hashlib,html,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/"thumb-21964-candidate"
OUT=ROOT/"p1-20261021-qa";OUT.mkdir(exist_ok=True)
with gzip.open(ROOT/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz","rt",encoding="utf8") as f:
 manifest=json.load(f)["original_public_html_to_data_payload"]
DATA=json.loads((ROOT/"data/stations.json").read_text("utf8"))["stations"]
OFFICIAL=json.loads((ROOT/"data/stations-official15-verified-overrides-v1.json").read_text("utf8"))["rows"]
by_slug={x["slug"]:x for x in DATA}
assert len(by_slug)==911 and len(OFFICIAL)==15 and len(manifest)==158571
EXEMPT_HUB={"incheonairport-t1","busandaeyangsankaempeoseu","gukjegeumyungsenteo-busaneunhaeng","toseong","bokhammunhwayunghapdanji","ganeung"}  # The last is previous SCREEN_PASS
EXEMPT_ELEM={"gukjegeumyungsenteo-busaneunhaeng"}
# 906 hubs + 910 elementary were P0; exclude 1 already screened-pass hub, exactly 1815 high-repeat URLs.
target=[]
for st in DATA:
 if st["slug"] not in EXEMPT_HUB:target.append(("station-"+st["slug"]+".html",st,"hub"))
 if st["slug"] not in EXEMPT_ELEM:target.append(("station-"+st["slug"]+"-elem-tutor.html",st,"elem"))
assert len(target)==1815
READING=[
 ("문장 읽기","I see a red bag.","누가 무엇을 보는지 찾아보고 red가 설명하는 단어를 표시해보세요."),
 ("소리와 글자 연결","ship / sheep","모음 소리가 어떻게 다른지 듣고 읽어보세요."),
 ("질문에 한 문장 답하기","Where do you live?","장소를 넣어 I live in ... 형태로 답해보세요."),
 ("기초 어순","She likes music.","주어, 동사, 목적어를 한 번씩 가리켜보세요."),
 ("짧은 글 요약","A dog is under the table.","누가 어디에 있는지 우리말로 한 문장 요약해보세요."),
 ("듣고 다시 말하기","Can I have some water?","요청하는 대상과 요청 문장 시작을 각각 찾아보세요."),
 ("현재형과 과거형","I play / I played","행동이 일어난 시점을 문장에서 구분해보세요."),
 ("비교 표현","This book is bigger.","무엇을 무엇과 비교하는지 설명해보세요."),
 ("그림 설명","There are two chairs.","사물의 개수와 장소를 넣어 문장을 만들어보세요."),
 ("핵심 정보 찾기","The train leaves at nine.","언제 출발하는지 찾아 말해보세요."),
 ("문장 연결","I was tired, so I rested.","원인과 결과를 구분해 두 문장으로 다시 적어보세요."),
 ("기초 관사","a book / the book","처음 소개한 대상과 이미 알고 있는 대상을 나눠보세요."),
 ("의문문 만들기","You are ready. / Are you ready?","질문할 때 단어의 순서가 어떻게 달라지는지 확인하세요."),
 ("대명사","Minji is kind. She helps me.","She가 누구를 가리키는지 찾아보세요."),
 ("짧은 대화 이어가기","How was your day?","좋았던 일을 한 문장으로 답하고 이유를 더해보세요."),
 ("접속사로 연결","I stayed home because it rained.","왜 집에 있었는지 이유를 뽑아보세요."),
]
EXAMS=[
 ("목표 점수와 일정","최근 모의 결과에서 점수를 가장 많이 잃은 구간 하나를 표시하고, 다음 시험까지 복습할 날을 배분합니다."),
 ("듣기 이해","한 문장을 듣고 핵심 정보 하나를 기록한 뒤, 대본과 비교해 들리지 않은 소리를 확인합니다."),
 ("답변 시작","질문을 읽고 첫 문장까지 걸리는 시간을 재보고, 완벽한 답변보다 핵심 답부터 말해봅니다."),
 ("오답 분류","어휘 부족, 질문 오해, 시간 압박을 나누어 틀린 문제에 원인 표시를 해봅니다."),
 ("문제 유형별 우선순위","익숙한 파트와 반복해서 틀리는 파트를 분리해 다음 학습 시간을 조절합니다."),
 ("과제 수행","읽기·듣기·말하기·쓰기 중 지금 목표에 필수인 수행을 하나 선택하고 실제 결과물을 만듭니다."),
 ("문장 확장","짧은 답에 예시나 이유 한 문장을 더하고, 추가 문장이 질문과 연결되는지 확인합니다."),
 ("다시 확인","수정한 문장을 24시간 뒤 새로운 질문에서 재사용할 수 있는지 점검합니다."),
 ("자기진단","아는 표현인데 말이 늦는지, 낯선 표현이라 이해가 느린지 구분해봅니다."),
 ("복습 루틴","하루 목표량보다 한 주 동안 반복 가능한 분량을 정해 실행 여부를 표시합니다."),
 ("피드백 확인","수업에서 받은 수정이 다음 답변에서 다시 나타나는지 근거를 기록합니다."),
 ("실제 사용 목적","학교 시험, 공인점수 제출, 직장 회의 등 가장 가까운 사용 시점을 먼저 정합니다.")
]
PARENT=[
 "최근 학교 과제에서 혼자 읽은 문장과 설명이 필요한 문장을 색으로 구분합니다.",
 "어휘를 외웠는지보다 새로운 문장 안에서 그 뜻을 이해하는지 확인합니다.",
 "문장 순서를 스스로 고친 경우와 도움을 받은 경우를 따로 기록합니다.",
 "틀린 문제를 다시 풀 때 정답만 외우지 않고 이유를 설명하도록 도와줍니다.",
 "일주일에 세 번, 10분씩 읽기·말하기·쓰기 중 하나에 집중해 봅니다.",
 "새 단어가 등장할 때 그림·맥락·짧은 예문 중 어떤 방식이 편한지 살펴봅니다.",
 "읽기 속도가 느린지, 내용 이해가 부족한지 서로 다르게 확인합니다.",
 "짧은 문장을 소리 내어 읽고 주어와 동사를 표시해 이해를 확인합니다.",
 "단어 테스트보다 실제 과제의 한 문장을 설명하게 해봅니다.",
 "수행평가 자료가 있다면 제출 형식과 실제 답변 길이를 먼저 확인합니다.",
 "수업 직후 가능한 것과 이틀 뒤에도 가능한 것을 비교해 봅니다.",
 "학년보다 현재 풀 수 있는 문제와 버거워하는 부분을 기준으로 선택합니다."
]
def esc(s):return html.escape(str(s),quote=True)
def rank(seed,n):
 return int(hashlib.sha256(seed.encode()).hexdigest()[:12],16)%n
def render(st,kind):
 slug=st["slug"];name=esc(st["name"]);seed=slug+"|"+kind+"|evidence-v3"
 a=READING[rank(seed+"reading",len(READING))]
 b=EXAMS[rank(seed+"exam",len(EXAMS))]
 c=PARENT[rank(seed+"parent",len(PARENT))]
 r=READING[rank(seed+"second",len(READING))]
 if kind=="hub":
  first=(f'<h2>{name}에서 학습 목적별로 무엇을 먼저 확인할까요?</h2>'
       f'<p><strong>학교 영어</strong>를 찾는다면 {esc(a[0])}을 먼저 시험해 볼 수 있습니다. 예문은 <q>{esc(a[1])}</q>입니다. {esc(a[2])} '
       f'수행이 가능하면 {esc(r[0])}으로 넘어가며, 수업의 난도는 실제 학생 답안을 보고 결정합니다.</p>'
       f'<p><strong>시험 영어</strong>라면 {esc(b[0])}을 기준으로 시작합니다. {esc(b[1])} '
       f'시험별 시험 형식·점수·일정은 서로 다르므로, 학생 영어 또는 회화와 같은 과정으로 간주하지 않습니다.</p>'
       f'<p><strong>회화 영어</strong>라면 오늘 바로 사용할 문장을 하나 정한 뒤, {esc(r[2])} '
       f'학습자 수준에 맞게 질문을 바꾸고 같은 표현을 다른 대화에도 적용할 수 있는지 확인합니다.</p>')
 else:
  first=(f'<h2>{name} 초등 영어: 첫 학습 확인과 복습 방법</h2>'
       f'<p><strong>읽기 확인</strong>: <q>{esc(a[1])}</q>를 보여주고 학생이 혼자 읽고 이해한 부분을 표시합니다. {esc(a[2])} '
       f'모르는 단어를 먼저 알려주지 않고 문맥에서 추측할 수 있는지도 살펴봅니다.</p>'
       f'<p><strong>다음 연습</strong>: {esc(r[0])}을 골라 <q>{esc(r[1])}</q> 예문을 활용합니다. {esc(r[2])} '
       f'낯선 문장에서 같은 원리를 적용하는지를 숙제량보다 우선해 확인합니다.</p>'
       f'<p><strong>학부모 점검</strong>: {esc(c)} 학생이 스스로 한 부분과 도움을 요청한 부분을 나눠 기록하고, 다음 수업에서 다시 확인할 항목을 정합니다.</p>')
 return ('<section class="section enpt-learning-evidence" data-enpt-learning-evidence="20261021">'
         '<div class="wrap"><p class="kicker">공부 방법 예시 · 1:1 수업 선택 기준</p>'+first+
         '<p class="enpt-evidence-note">이 안내는 학습 방법 예시이며, 특정 역에 학원이나 강사가 상주한다는 의미가 아닙니다. 실제 수업 가능 지역과 방식은 상담 과정에서 확인해야 합니다.</p>'
         '</div></section>')
def head(raw):
 m=re.search(r'<head\b[^>]*>.*?</head>',raw,re.I|re.S);assert m;return m.group()
def basic_check(a,b,route):
 for marker in ('<link rel="canonical"','name="robots"','property="og:image"','name="englishpt-consultation"'):
  assert a.count(marker)==b.count(marker),(route,marker)
 assert a.count('name="englishpt-consultation"')>=1,route
 assert 'noindex' not in re.search(r'<meta name="robots"[^>]+>',b).group(0).lower()
 assert len(b)>len(a)
metrics=[]
for route,st,kind in target:
 entry=manifest.get(route);assert entry and not entry["noindex"],route
 path=SITE/entry["to"];old=path.read_text("utf8")
 assert 'data-enpt-p0="20261021"' in old,route
 assert 'data-enpt-learning-evidence="20261021"' not in old,route
 new=old.replace('</main>',render(st,kind)+'</main>',1)
 assert head(new)==head(old),(route,"head_changed")
 basic_check(old,new,route)
 path.write_text(new,"utf8")
 metrics.append({"route":route,"kind":kind,"before_bytes":len(old.encode()),"after_bytes":len(new.encode()),"metadata_preserved":True})
assert len(metrics)==1815
# Official sources are municipal railway stations, NOT tuition centers. Keep stable slugs, links, canonical, sitemap, forms, and structured data.
official_pages=[]
for info in OFFICIAL:
 slug=info["slug"];st=by_slug[slug];assert st["name"]==info["name"] and info["city"]=="경기도" and info["area"]=="남양주시"
 assert "남양주시" in info["verified_address"]
 # 24 existing station routes: hub+23 intents; conservative patch only when route exists.
 routes=[r for r,v in manifest.items() if r.startswith("station-"+slug+"-") or r=="station-"+slug+".html"]
 # Exclude collisions where station slug is prefix of another station route via expected 23 valid suffixes.
 intents=["elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv","biz-business-conv","housewife-conv","toeic","toeic-speaking","opic","ielts","duolingo","toefl","toeic-academy","toeic-speaking-academy","opic-academy","ielts-academy","duolingo-academy","toefl-academy","english-conv-academy","adult-english-conv-academy","worker-english-conv-academy","beginner-english-conv"]
 routes=["station-"+slug+".html"]+["station-"+slug+"-"+i+".html" for i in intents]
 assert len(routes)==24 and all(r in manifest and not manifest[r]["noindex"] for r in routes)
 for route in routes:
  path=SITE/manifest[route]["to"];old=path.read_text("utf8");oldhead=head(old)
  # Correct only visible prose; changing title, canonical, OG, schema requires separately reviewed SEO migration.
  body_start=old.lower().find("<body");assert body_start>=0
  prefix,body=old[:body_start],old[body_start:]
  if st.get("city")=="서울" and (st.get("areas") or [None])[0]=="남양주시":
   body=body.replace("서울 남양주시","경기도 남양주시")
  label=('<section class="enpt-official-station-address" aria-label="역 위치 출처">'
         '<div class="wrap"><p><strong>역 위치 참고</strong> '+esc(info["verified_address"])+
         ' · 이 주소는 철도역 주소이며, 학원 또는 수업 장소가 아닙니다.</p></div></section>')
  if 'enpt-official-station-address' not in body:body=body.replace('</main>',label+'</main>',1)
  new=prefix+body;assert head(new)==oldhead and 'name="englishpt-consultation"' in new
  path.write_text(new,"utf8");official_pages.append(route)
assert len(official_pages)==360
# Improved 911 station index page - visual enhancement without altering any station links, SEO or form.
station_route=manifest["stations.html"];assert not station_route["noindex"]
station_path=SITE/station_route["to"];old=station_path.read_text("utf8")
assert 'id="stationSearch"' in old and 'class="station-index-grid"' in old
CSS=r"""
<style id="enpt-stations-ux-20261021">
body.station-index-page{background:#f0f8f4;color:#17382f}
.station-index-page .station-index-hero{background:linear-gradient(125deg,#113d34 0%,#185b49 63%,#22715b 100%);color:#f9fff9;border-radius:0 0 32px 32px;padding:64px 0 44px}
.station-index-page .station-index-hero .eyebrow{color:#c5f0d7}
.station-index-page .station-index-hero h1{color:#fff;letter-spacing:-.045em;line-height:1.24}
.station-index-page .station-index-hero .hero-copy{color:#e6f6ed;max-width:760px}
.station-index-page .station-search-box{display:block;background:#fff;padding:18px 20px 21px;border-radius:22px;max-width:820px;margin-top:30px;border:2px solid #a5d3ba;box-shadow:0 16px 38px rgba(0,0,0,.2)}
.station-index-page .station-search-box label{display:block;color:#164936;font-size:16px;font-weight:800;margin-bottom:9px}
.station-index-page #stationSearch{display:block;box-sizing:border-box;width:100%;height:58px;background:#f6fbf8!important;border:2px solid #6caa8a!important;border-radius:13px!important;color:#193a2b!important;font-size:18px!important;padding:10px 18px!important;outline:none!important;box-shadow:none!important;-webkit-appearance:none;appearance:none}
.station-index-page #stationSearch::placeholder{color:#526c5f!important;opacity:1}
.station-index-page #stationSearch:focus{border-color:#177f58!important;box-shadow:0 0 0 4px rgba(38,142,103,.19)!important;background:#fff!important}
.station-index-page .enpt-find-tools{max-width:820px;margin-top:14px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.station-index-page .enpt-find-tools p{margin:0;color:#f0fff3;font-size:14px}
.station-index-page .enpt-find-tools button{background:#f2fff5;color:#125138;border:1px solid #b7e2c4;border-radius:999px;padding:9px 16px;font-weight:750;cursor:pointer}
.station-index-page .enpt-find-tools button:focus-visible,.station-index-page #enptStationLine:focus-visible{outline:3px solid #f7db81;outline-offset:2px}
.station-index-page .enpt-line-navigator{background:#fff;max-width:1100px;margin:20px auto 0;padding:20px;border:1px solid #d4e8db;border-radius:20px;box-shadow:0 8px 28px rgba(14,65,44,.07)}
.station-index-page .enpt-line-navigator label{display:block;font-weight:750;color:#17442f;margin-bottom:8px}
.station-index-page #enptStationLine{width:min(100%,420px);font-size:16px;min-height:48px;padding:10px 14px;border:2px solid #74ab8c;border-radius:12px;background:#fff;color:#133c29}
.station-index-page #stationLines{display:grid;gap:18px;margin-top:22px}
.station-index-page .station-line-block:not([hidden]){background:#fff;display:block;border:1px solid #d1e7d7;border-radius:20px;padding:22px;box-shadow:0 7px 20px rgba(11,53,35,.06)}
.station-index-page .station-line-block h2{color:#173e2f;font-size:clamp(21px,2.2vw,29px);margin-bottom:18px}
.station-index-page .station-index-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(145px,1fr));gap:10px}
.station-index-page .station-index-link:not([hidden]){display:flex;align-items:center;justify-content:center;min-height:47px;padding:10px 12px;border:1px solid #bfdbca;background:#f4faf5;border-radius:12px;color:#214f39;font-weight:650;text-align:center;text-decoration:none;transition:background .12s,border-color .12s}
.station-index-page .station-index-link:hover,.station-index-page .station-index-link:focus-visible{background:#dff3e6;border-color:#338767;outline-offset:2px}
.station-index-page .station-empty:not([hidden]){padding:26px;color:#713b20;background:#fff4e9;border:1px solid #e5c9aa;border-radius:16px}
.station-index-page main>.section{background:#f0f8f4}
.station-index-page .enpt-results-caption{font-size:14px;color:#244e39;font-weight:700;margin:14px 0}
@media(max-width:640px){.station-index-page .station-index-hero{padding:39px 0 29px;border-radius:0 0 22px 22px}.station-index-page .station-search-box{padding:16px;margin-top:22px;border-radius:17px}.station-index-page #stationSearch{font-size:16px!important;height:54px}.station-index-page .station-line-block:not([hidden]){padding:15px}.station-index-page .station-index-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.station-index-page .station-index-link:not([hidden]){min-height:48px;font-size:14px}.station-index-page .enpt-line-navigator{padding:16px}}
@media(prefers-reduced-motion:reduce){.station-index-page .station-index-link{transition:none}}
</style>
"""
TOOLS=r"""
<div class="enpt-find-tools" aria-label="빠른 역 검색">
<p>역 이름 두 글자만 입력해도 찾을 수 있어요.</p>
<button type="button" data-station-quick="강남역">강남역 찾기</button>
<button type="button" data-station-quick="도봉산역">도봉산역 찾기</button>
<button type="button" id="enptStationClear">검색 초기화</button>
</div>
"""
NAV=r"""
<div class="enpt-line-navigator">
<label for="enptStationLine">노선으로 빠르게 이동</label>
<select id="enptStationLine" aria-label="철도 노선 선택"><option value="">노선을 선택하세요</option></select>
<p id="enptStationResults" class="enpt-results-caption" role="status" aria-live="polite">전국 역 목록에서 역을 검색하거나 노선을 선택하세요.</p>
</div>
"""
JS=r"""
<script id="enpt-stations-ux-js-20261021">(function(){
const input=document.getElementById('stationSearch'),jump=document.getElementById('enptStationLine'),blocks=Array.from(document.querySelectorAll('.station-line-block'));
const count=document.getElementById('enptStationResults');if(!input||!jump||!count)return;
blocks.forEach((block,i)=>{block.id='enpt-line-'+i;const opt=document.createElement('option');opt.value=block.id;opt.textContent=block.querySelector('h2')?.textContent.trim()||('노선 '+(i+1));jump.append(opt)});
function update(){const visible=Array.from(document.querySelectorAll('.station-index-link:not([hidden])')).filter(a=>!a.closest('.station-line-block[hidden]'));const unique=new Set(visible.map(a=>a.getAttribute('href')));count.textContent=input.value.trim()?('검색 결과 '+unique.size+'개 역 · 검색어: '+input.value.trim()):('911개 역 · 37개 노선 · 환승역은 여러 노선에 표시될 수 있습니다.');}
input.addEventListener('input',()=>requestAnimationFrame(update));
jump.addEventListener('change',()=>{const block=document.getElementById(jump.value);if(!block)return;input.value='';input.dispatchEvent(new Event('input',{bubbles:true}));requestAnimationFrame(()=>block.scrollIntoView({behavior:'smooth',block:'start'}));});
document.getElementById('enptStationClear')?.addEventListener('click',()=>{input.value='';input.dispatchEvent(new Event('input',{bubbles:true}));jump.value='';input.focus()});
document.querySelectorAll('[data-station-quick]').forEach(btn=>btn.addEventListener('click',()=>{input.value=btn.dataset.stationQuick;input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();}));
update();
})();</script>
"""
assert "</head>" in old and "</body>" in old and '<div class="station-search-box">' in old and '<div id="stationLines">' in old
new=old.replace("</head>",CSS+"</head>",1).replace("</body>",JS+"</body>",1)
new=new.replace('</div></div></section><section class="section">','</div>'+TOOLS+'</div></section><section class="section">',1) if False else new
# Insert tools immediately after the whole small search input box, keeping old listener and input id.
m=re.search(r'(<div class="station-search-box">.*?</div>)',new,re.S);assert m
new=new[:m.end()]+TOOLS+new[m.end():]
new=new.replace('<div id="stationLines">',NAV+'<div id="stationLines">',1)
assert head(old)==head(new).replace(CSS,"") and new.count('id="stationSearch"')==1
assert old.count('class="station-index-link"')==new.count('class="station-index-link"')
assert old.count('name="englishpt-consultation"')==new.count('name="englishpt-consultation"')
station_path.write_text(new,"utf8")
with (OUT/"P1_1815_TARGETS.csv").open("w",newline="",encoding="utf-8-sig") as f:
 w=csv.DictWriter(f,fieldnames=metrics[0]);w.writeheader();w.writerows(metrics)
(OUT/"P1_PATCH_REPORT.json").write_text(json.dumps({"status":"PASS_OFFLINE_1815_HIGHREPEAT_15_STATION_ADDRESS_911_SEARCH_UX","new_learning_guides":len(metrics),"official_station_records":15,"official_html_routes":len(official_pages),"stations_page_link_count_unchanged":True,"seo_meta_all_1815_unchanged":True,"form_all_1815_unchanged":True,"domain_or_brand_rename_done":False,"production_published":False},ensure_ascii=False,indent=2),"utf8")
print("P1_OFFLINE_APPLIED_1815_15_911UX",len(metrics),len(official_pages),flush=True)
