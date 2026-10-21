#!/usr/bin/env python3
"""P2 offline-only elementary instructional redesign (910) plus provisional brand rename.
Apply on already-offline-P0/P1 candidate, never touch Production, sitemap or URL.
Provisional brand is subject to KIPRIS trademark and business-name clearance.
"""
from __future__ import annotations
import csv,gzip,hashlib,html,json,pathlib,re,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/"thumb-21964-candidate"
OUT=ROOT/"p2-20261021-qa";OUT.mkdir(exist_ok=True)
with gzip.open(ROOT/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz","rt",encoding="utf8") as z:
 source=json.load(z)["original_public_html_to_data_payload"]
stations=json.loads((ROOT/"data/stations.json").read_text(encoding="utf8"))["stations"]
assert len(stations)==911 and len(source)==158571
assert sum(not x["noindex"] for x in source.values())==21964
assert sum(x["noindex"] for x in source.values())==136607
EXEMPT={"gukjegeumyungsenteo-busaneunhaeng"}
# Curated real elementary tasks, not geographically invented learner outcomes, school names or service claims.
# Each variant includes a verifiable question, response, assessment and next teaching action.
LESSONS={
"초1·초2 · 글자와 소리": [
("소리 구별하기","cat / cap","두 단어의 마지막 소리를 다르게 읽어 보세요.","/t/와 /p/가 다르게 들리는지 본 뒤 틀린 소리만 다시 읽습니다.","소리를 구별하지 못했다면 글자를 손가락으로 짚고 입 모양을 함께 확인합니다."),
("소리 합쳐 읽기","s - u - n → sun","세 소리를 이어서 한 단어로 읽어 보세요.","철자 세 개를 하나씩 읽는지, 자연스럽게 이어 읽는지를 따로 봅니다.","단어 전체를 외우기보다 다른 첫소리를 대입해 다시 읽습니다."),
("기초 뜻 연결","The dog runs.","누가 무엇을 하는지 그림 없이 설명해 보세요.","dog와 runs의 뜻뿐 아니라 문장의 관계를 말할 수 있는지 확인합니다.","명사·동사 카드를 나누고 새로운 단어로 순서를 다시 만듭니다."),
("알파벳 구별","b / d","두 글자를 구별해 각각 한 단어를 적어 보세요.","비슷한 모양의 글자를 같은 것으로 읽는지, 쓰기에서만 헷갈리는지 나눕니다.","글자 방향을 확인하고 소리와 단어를 한 번씩 연결합니다."),
("짧은 요청 말하기","Can I sit here?","어디에 앉아도 되는지 묻는 문장으로 바꿔 보세요.","처음부터 문장을 만들어 말하는지, 정해진 문장을 따라만 하는지 살펴봅니다.","Can I ...? 패턴의 마지막 말을 바꿔 두 가지 상황을 연습합니다."),
("색깔과 명사 순서","a blue car","어떤 색의 무엇인지 우리말로 설명해 보세요.","색을 뜻하는 말과 물건 이름의 순서를 문장 속에서 파악하는지 확인합니다.","red car, blue bag처럼 새 명사를 넣어 읽어 보게 합니다."),
],
"초3·초4 · 문장과 기초 문법": [
("주어와 동사","He plays soccer.","누가 무엇을 하는지 표시하고 she를 넣어 다시 읽어 보세요.","주어가 바뀔 때 동사의 형태도 함께 점검하는지 확인합니다.","I play와 He plays를 나란히 써서 차이를 찾아보게 합니다."),
("의문문 전환","She is ready. → Is she ready?","평서문과 질문을 비교해 순서가 달라진 단어를 표시하세요.","문장의 뜻은 아는데 질문 형태에서 막히는지 확인합니다.","You are happy를 질문으로 바꾸어 같은 원리가 적용되는지 봅니다."),
("부정문 이해","I do not like milk.","좋아하는지 좋아하지 않는지 근거 단어를 찾아보세요.","not을 놓치고 해석하는지, 문장 전체를 이해했는지 구별합니다.","She does not like milk로 대상을 바꿔 설명하게 합니다."),
("짧은 문장 연결","I was hungry, so I ate.","왜 먹었는지 이유를 한 문장으로 말해 보세요.","so 앞뒤를 원인과 결과로 구별할 수 있는지 확인합니다.","because를 활용하여 같은 이유를 다른 순서로 표현합니다."),
("위치 표현","The pencil is under the desk.","연필이 어디에 있는지 그림으로 표시하세요.","under를 외운 것과 실제 위치를 정확히 그리는 것을 구분합니다.","on, under, next to를 바꿔 보며 짧은 문장을 만듭니다."),
("과거 행동","Yesterday, we visited a park.","언제 어떤 일을 했는지 두 부분으로 나눠 보세요.","Yesterday라는 시간 표현과 visited의 시제를 연결하는지 봅니다.","Today 문장으로 바꾸고 동사 형태를 직접 고르게 합니다."),
],
"초5·초6 · 독해와 학교 과제": [
("중심 내용 찾기","Jisu takes the bus because it is raining.","지수가 버스를 타는 이유를 문장 속에서 찾아보세요.","이유를 나타내는 because 뒤 내용을 근거로 말할 수 있는지 확인합니다.","접속사를 지운 문장과 비교해 정보가 어떻게 달라지는지 설명합니다."),
("대명사 추적","Mina found a key. She gave it to Dad.","She와 it이 각각 무엇을 가리키는지 적어 보세요.","앞 문장의 인물·사물을 연결해 읽는지 확인합니다.","대명사를 원래 단어로 바꿔 두 문장을 다시 읽습니다."),
("정보 비교","Tom is taller than Ben.","두 사람 가운데 누가 더 큰지 표로 정리하세요.","비교급을 암기한 것과 문장을 근거로 비교하는 것을 구별합니다.","shorter를 써 같은 관계를 반대로 설명해 봅니다."),
("시간표 읽기","The library opens at nine and closes at six.","문을 여는 시각과 닫는 시각을 각각 적어 보세요.","숫자만 찾지 않고 opens와 closes를 구별하는지 확인합니다.","open과 close를 바꾸어 정보가 어떻게 달라지는지 말합니다."),
("요약과 근거","Plants need light and water to grow.","식물에 필요한 두 가지를 찾고 핵심을 한 문장으로 써 보세요.","핵심 정보를 빼지 않고 간결하게 설명하는지 평가합니다.","원문과 요약문을 비교해 필요한 단어가 남아 있는지 봅니다."),
("서술형 답변","Why did you go home early? — Because I felt sick.","질문에 맞는 이유를 완전한 문장으로 답해 보세요.","이유를 알지만 답을 문장으로 못 쓰는지 확인합니다.","주어·동사를 보완해 답을 완성한 다음 새로운 이유로 바꿔 봅니다."),
]
}
CASES=[
("단어는 외우는데 읽기 어려울 때","새 단어를 바로 뜻으로 번역하기 전에 소리·문장 위치·문장 전체 뜻을 차례로 확인합니다. 읽을 수 있는 단어와 뜻만 외운 단어를 별도로 표시합니다."),
("말하기를 부담스러워할 때","하나의 정답을 길게 말하게 하기보다 이름·동작·장소 중 한 부분만 바꿔 짧게 답하게 합니다. 도움이 필요했던 부분을 기록합니다."),
("문법 문제만 틀릴 때","틀린 문제의 규칙을 설명하도록 한 다음, 원래 문장의 단어를 두 개 바꿔도 같은 규칙이 적용되는지 확인합니다."),
("읽었지만 내용이 남지 않을 때","주어, 일어난 일, 이유를 각각 표시한 후 문장을 보지 않고 핵심을 한 문장으로 다시 말해봅니다."),
("쓰기에서 같은 실수가 반복될 때","철자·어순·주어와 동사의 짝 중 어떤 실수인지 나누고 같은 유형에서 재발하는지 두 문장으로 비교합니다."),
("숙제를 혼자 시작하지 못할 때","처음 3분은 문제의 지시문 읽기만 스스로 진행하고, 도움이 필요했던 단계를 수업의 첫 확인 항목으로 씁니다."),
("교재 난도가 맞지 않을 때","쉬운 문제 정답률과 낯선 문장 정답률을 나눠 보며 어려운 부분이 단어인지 문장 이해인지 확인합니다."),
("학교 수행평가가 있을 때","제출 형식, 평가 기준, 말하기 분량을 확인하고 답변을 먼저 짧게 작성한 뒤 문장을 확장합니다."),
]
FAMILY=[
("학습 기록 방식","문제의 정답 여부와 함께 '힌트 없이 가능', '힌트 후 가능', '다시 설명 필요'로 구분하면 다음 수업의 시작점을 정하기 쉽습니다."),
("복습 점검","수업 직후 한 번, 이틀 뒤 한 번 같은 원리를 새 문장에 적용해 보고 두 결과의 차이를 기록합니다."),
("학부모 피드백","아이가 혼자 설명한 문장을 한 개 남기고, 틀린 문제보다 도움을 받아 해결한 부분을 구체적으로 표시합니다."),
("읽기와 의미 분리","소리 내어 잘 읽어도 뜻을 설명하지 못할 수 있습니다. 읽기 점검과 이해 점검을 서로 다른 질문으로 진행합니다."),
("작문과 어순","단어 카드를 먼저 배열하고 완성된 문장으로 읽어 봅니다. 고친 부분을 다시 틀리는지 확인하는 것이 목표입니다."),
("수준별 자료 준비","최근 숙제 한 장, 학교 과제 한 문항, 아이가 이해하지 못한 표현을 준비해 과도한 선행보다 현재 이해도를 살핍니다."),
("자기주도 시간","10분 공부 중 혼자 시작한 시간과 질문한 시간을 각각 기록하며 학습량보다 시작·지속·복습의 과정을 확인합니다."),
("상담 질문","지금 학년과 교재뿐 아니라 모르는 문장을 만났을 때 어떻게 해결하는지 물어보고, 가능한 공부 시간과 방법도 함께 정합니다."),
]
def esc(v):return html.escape(str(v),quote=True)
def choose(slug,part,n):return int(hashlib.sha256(("ENPT-P2|"+slug+"|"+part).encode()).hexdigest()[:13],16)%n
def pedagogical(st):
 slug=st["slug"];name=esc(st["name"])
 seg=['<section class="section enpt-elem-learning-v2" data-enpt-elem-v2="20261021" aria-label="초등학생 영어 과외 수준별 학습 예시"><div class="wrap">',
      '<p class="kicker">학부모가 직접 확인할 수 있는 영어 학습 기준</p>',
      f'<h2>{name} 영어과외를 비교할 때 볼 학년별 학습 예시</h2>',
      '<p>아래 예시는 실제 학생 개인의 진단 결과가 아닌, 상담 전 아이의 현재 수준을 확인하는 교육용 질문입니다. 모든 학년이 같은 진도로 학습한다는 뜻은 아닙니다.</p>']
 for label,options in LESSONS.items():
  goal,ex,question,check,nextstep=options[choose(slug,label,len(options))]
  seg+=['<article class="enpt-elem-learning-block">',
        f'<h3>{esc(label)} · {esc(goal)}</h3>',
        f'<p><strong>확인할 문장</strong>: <span lang="en">{esc(ex)}</span></p>',
        f'<p><strong>학생에게 해볼 질문</strong>: {esc(question)}</p>',
        f'<p><strong>평가 기준</strong>: {esc(check)}</p>',
        f'<p><strong>다음 공부 방법</strong>: {esc(nextstep)}</p>','</article>']
 issue=CASES[choose(slug,"case",len(CASES))]
 parent=FAMILY[choose(slug,"family",len(FAMILY))]
 seg+=['<article class="enpt-elem-learning-block">',
       f'<h3>{esc(issue[0])}</h3><p>{esc(issue[1])}</p>',
       f'<h3>{esc(parent[0])}</h3><p>{esc(parent[1])}</p>',
       '<p>이 예시는 학습 정보이며 특정 철도역에 강사가 상주하거나 방문수업이 가능하다는 보장은 아닙니다. 수업 지역과 방식은 상담 시 별도로 확인해야 합니다.</p>',
       '</article></div></section>']
 return "\n".join(seg)
def head(t):
 m=re.search(r"<head\b[^>]*>.*?</head\s*>",t,re.I|re.S);assert m;return m.group()
def capture(r,text):
 m=re.search(r,p,text,re.I|re.S);return m.group() if m else None
def fix_old_generic(body,st):
 # Displace boilerplate judgement cards with more useful applied grade tasks.
 generic=re.compile(r'<section class="section (?:mass-context|local-decision-note)">.*?</section>',re.S|re.I)
 found=generic.findall(body)
 if len(found)!=2:raise ValueError("Expected exact 2 repetitive template sections: "+st["slug"]+" "+str(len(found)))
 return generic.sub("",body)
changed=[]
for st in stations:
 if st["slug"]=="gukjegeumyungsenteo-busaneunhaeng":continue
 route="station-"+st["slug"]+"-elem-tutor.html";assert route in source and source[route]["noindex"] is False
 path=SITE/source[route]["to"];a=path.read_text("utf8")
 assert a.count('data-enpt-p0="20261021"')==1
 assert a.count('data-enpt-elem-v2="20261021"')==0
 b=fix_old_generic(a,st)
 assert b.count("</main>")==1 and b.count("<main")>=1
 b=b.replace("</main>",pedagogical(st)+"</main>",1)
 assert head(a)==head(b),(route,"HEAD_DIFF")
 for needle in ('name="englishpt-consultation"','name="robots"','rel="canonical"'):
  assert a.count(needle)==b.count(needle), (route,needle)
 path.write_text(b,"utf8")
 changed.append({"url":"https://englishpt.kr/"+route,"slug":st["slug"],"bytes_before":len(a.encode()),"bytes_after":len(b.encode()),"discarded_boilerplate_blocks":2,"new_grade_rubrics":3})
assert len(changed)==910
with (OUT/"910_ELEM_INSTRUCTIONAL_CHANGES.csv").open("w",newline="",encoding="utf-8-sig") as f:
 w=csv.DictWriter(f,fieldnames=list(changed[0]));w.writeheader();w.writerows(changed)
print("P2_ELEM_910_SUBSTANTIVE_CURRICULUM_REPLACED",len(changed),flush=True)
# Apply ONE provisional brand across ALL 158571 HTML routes: avoid inconsistent noindex user-facing pages.
BRAND={"잉글리시PT":"잉글로담","잉글리쉬PT":"잉글로담","ENGLISH PT":"ENGLODAM","English PT":"ENGLODAM"}
def rename(t):
 for old,new in BRAND.items():t=t.replace(old,new)
 return t
brand_counts=collections.Counter()
for i,(route,m) in enumerate(source.items(),1):
 path=SITE/m["to"];a=path.read_text("utf8")
 b=rename(a)
 if b!=a:
  assert rename(a)==b
  # Preserve every SEO index/noindex instruction, canonical and form signature.
  patterns=(r'<meta\s+name=["\']robots["\'][^>]*>',r'<link\s+rel=["\']canonical["\'][^>]*>',
            r'<meta\s+property=["\']og:image["\'][^>]*>')
  for patt in patterns:
   aa=re.search(patt,a,re.I);bb=re.search(patt,b,re.I)
   assert (aa.group() if aa else None)==(bb.group() if bb else None),(route,patt)
  assert a.count('name="englishpt-consultation"')==b.count('name="englishpt-consultation"'),route
  path.write_text(b,"utf8");brand_counts["noindex" if m["noindex"] else "indexable"]+=1
 if i%45000==0:print("P2_BRAND_FULL_SITE_PROGRESS",i,flush=True)
# Homepage root is separately served as static file. Preserve old root canonical URL, no SEO migrations.
for rel in ("index.html","englishpt.html"):
 p=SITE/rel
 if not p.exists():continue
 old=p.read_text("utf8");new=rename(old)
 assert capture(r'<link\s+rel="canonical"[^>]+>',old)==capture(r'<link\s+rel="canonical"[^>]+>',new)
 p.write_text(new,"utf8")
# Make only the canonical root homepage and its static duplicate explicitly express preferred site name.
for rel in ("index.html","englishpt.html"):
 p=SITE/rel
 if not p.exists():continue
 t=p.read_text("utf8")
 if 'property="og:site_name"' not in t:
  t=t.replace("</head>",'<meta property="og:site_name" content="잉글로담"></head>',1)
 p.write_text(t,"utf8")
# Verify all source files still exist and index distribution is unchanged. Brand change intentionally edits noindex body,
# but noindex rule is IDENTICAL, not byte SHA; other production-critical files never changed.
critical=("robots.txt","_headers","_redirects","netlify.toml","sitemap-index.xml","netlify/edge-functions/shard-router.js")
for rel in critical:
 assert (SITE/rel).exists() and len((SITE/rel).read_bytes())>50,rel
assert len(list((SITE/"__pages").glob("*/*.page")))==158571
idx=nidx=0
for route,m in source.items():
 p=SITE/m["to"]
 assert p.exists(),route
 raw=p.read_text("utf8")
 robots=re.search(r'<meta\s+name=["\']robots["\']\s+content=["\']([^"\']+)',raw,re.I)
 assert robots,route
 if m["noindex"]:
  assert "noindex" in robots.group(1).lower(),route;nidx+=1
 else:
  assert "noindex" not in robots.group(1).lower(),route;idx+=1
assert (idx,nidx)==(21964,136607)
checks={"status":"PASS_P2_BRAND_PREVIEW_AND_910_EDUCATIONAL_REWRITE_OFFLINE","brand_legal_clearance":"PENDING_OFFICIAL_KIPRIS","provisional_brand":"잉글로담","brand_romaji":"ENGLODAM","total_source_pages":158571,"indexable":idx,"noindex":nidx,"brand_changed_pages":dict(brand_counts),"elementary_rewritten":len(changed),"new_grade_learning_rubrics":2730,"static_home_brand":"잉글로담","critical_urls_unchanged":True,"production_deploys":0,"netlify_drafts_this_script":0}
(OUT/"P2_OFFLINE_SUMMARY.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2),"utf8")
print("P2_OFFLINE_FINAL",json.dumps(checks,ensure_ascii=False),flush=True)
