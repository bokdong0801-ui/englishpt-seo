#!/usr/bin/env python3
"""P2: replace repetitive generic elementary sections with age/skill-led, usable examples.
Only exact 910 station elementary pages in extracted unpublished candidate.
No names/domains/meta/forms/other URLs changed.
"""
import collections,gzip,hashlib,html,json,pathlib,re,csv
ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/"thumb-21964-candidate"
OUT=ROOT/"p2-elementary-originality-qa";OUT.mkdir(exist_ok=True)
DATA=json.loads((ROOT/"data/stations.json").read_text("utf8"))["stations"]
with gzip.open(ROOT/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz","rt",encoding="utf8") as f: mp=json.load(f)["original_public_html_to_data_payload"]
assert len(DATA)==911 and len(mp)==158571
SKILLS=[
 ("낱말 뜻보다 문장 관계","The rabbit is behind the tree.","behind가 알려주는 위치를 그림으로 나타내고 다른 사물에 적용하기"),
 ("짧은 글 이해","Mina lost her key. She looked under the desk.","잃어버린 물건과 다음 행동을 구분하고 새 제목 붙이기"),
 ("의문문 이해","Why did Tom bring an umbrella?","why 질문의 답에 이유가 포함되는지 확인하기"),
 ("시제 이해","We visited the museum yesterday.","어제·오늘·내일 표현을 바꿔 말해보고 동사 형태 표시하기"),
 ("기본 어순","My sister usually reads books.","누가·얼마나 자주·무엇을 하는지 세 칸으로 나누기"),
 ("추론 읽기","The ground was wet, but the sky was clear.","글에 직접 나오지 않은 가능성을 근거와 구분하기"),
 ("전치사","The pencil is between two notebooks.","between을 그림으로 표시하고 beside와 차이 말하기"),
 ("단어 재사용","The light bag is easy to carry.","light가 뜻하는 바를 문맥으로 확인하고 다른 예문 만들기"),
 ("문장 연결","It was cold, so we closed the window.","원인·결과 두 부분을 나누고 연결어가 바뀌면 뜻 비교하기"),
 ("인물·대명사","Jisu met Hana, and she smiled.","she의 대상이 모호함을 발견하고 분명하게 다시 쓰기"),
 ("순서 파악","First, wash the fruit. Then, cut it.","순서 낱말 없이도 행동 순서를 설명해보기"),
 ("비교","A bicycle is slower than a train.","비교 대상과 기준을 찾아 다른 이동수단으로 문장 바꾸기"),
 ("동사 선택","The children built a small bridge.","행동을 나타내는 동사를 찾고 만든 물건을 한 문장 더 묘사하기"),
 ("간단한 대화","Could you help me find the library?","도움을 요청하는 부분을 찾고 다른 장소로 바꿔 질문하기"),
 ("수량 표현","There is a little water left.","셀 수 있는 것과 없는 것을 비교하고 적합한 수량어 고르기"),
 ("독해 근거","Amy took a coat because it was windy.","인물이 코트를 가져간 이유를 문장의 어느 부분이 뒷받침하는지 표시하기"),
]
CHECKS=[
 ("읽기 속도","아는 단어를 읽어도 문장 끝까지 의미를 연결하는지 확인","문장 속 핵심 낱말 표시","다른 문장에서 같은 의미 파악"),
 ("문장 어순","단어 뜻을 알아도 주어와 동사의 위치를 구분하는지 확인","문장 조각 배열","새 인물로 문장 다시 쓰기"),
 ("듣기 이해","소리를 따라 하는 것과 듣고 뜻을 파악하는 일을 구분","짧은 문장 듣고 선택지 고르기","표현을 바꾼 질문에 답하기"),
 ("문장 쓰기","한글 생각을 그대로 옮기기보다 영어 어순으로 전달하는지 확인","두 문장 바르게 쓰기","오류 원인을 설명하고 재작성"),
 ("독해 근거","내용을 추측했는지 글 속 근거를 찾았는지 구분","근거 문장에 밑줄","근거가 다른 새 문항 해결"),
 ("질문 응답","질문 핵심어를 듣고 필요한 정보를 한 문장으로 답하는지 확인","의문사별 한 문장 답하기","의문사를 바꿔 답해보기"),
 ("복습 유지","수업 당일과 며칠 뒤의 독립 해결 정도 비교","틀린 예문 카드 만들기","이틀 뒤 비슷한 문제 풀기"),
 ("단어 활용","단어를 외운 상태와 문장에 정확히 넣는 상태 구분","새 어휘로 빈칸 채우기","다른 문맥에서 뜻 추론하기"),
 ("연결어","문장 두 개를 읽으며 원인·순서·대조를 이해하는지 확인","연결어 선택","새 예문 직접 만들기"),
 ("문단 요약","한 문장의 뜻보다 단락의 중심 내용을 추려내는지 확인","세 문장을 한 문장으로 요약","다른 글의 중심 생각 찾기"),
 ("발음·철자","말할 때 아는 소리를 읽기와 철자로 연결하는지 확인","짧은 낱말 짝짓기","낯선 낱말에서 소리 규칙 사용"),
 ("실수 유형","무작정 반복하기보다 자주 틀리는 이유를 분류","최근 오답을 뜻·어순·시제로 묶기","같은 실수 예방 체크리스트 작성"),
]
def choice(key,seq):return seq[int(hashlib.sha256(key.encode()).hexdigest()[:12],16)%len(seq)]
def esc(t):return html.escape(str(t),quote=True)
def section(st):
 slug=st["slug"]
 skill=choice(slug+"|reading",SKILLS)
 follow=choice(slug+"|followup",SKILLS)
 ck=choice(slug+"|check",CHECKS)
 grade=choice(slug+"|grade",["초4","초5","초6"])
 # Illustrative grade pathway, not a claim that pupils attending this station were assessed.
 return (f'<section class="section enpt-elem-practical" data-enpt-elem-originality="20261021"><div class="wrap">'
 '<p class="kicker">초등 영어과외 학습 예시</p>'
 f'<h2>{esc(grade)} 기준으로 살펴보는 {esc(skill[0])}</h2>'
 f'<p><strong>먼저 확인할 문장</strong> <q>{esc(skill[1])}</q>. '
 f'{esc(skill[2])}. 아이가 혼자 이해한 부분과 도움이 필요한 부분을 나누어 보세요.</p>'
 f'<p><strong>한 단계 확장</strong> <q>{esc(follow[1])}</q>. '
 f'이번에는 {esc(follow[2])}. 처음 문장과 다른 표현으로 옮겨갈 수 있는지 보는 활동입니다.</p>'
 f'<h3>{esc(ck[0])}을 어떻게 확인할까요?</h3>'
 f'<p>시작할 때는 {esc(ck[1])}합니다. '
 f'수업 중에는 {esc(ck[2])}, 다음 복습 때는 {esc(ck[3])}로 비교합니다.</p>'
 '<p>학생 수준을 실제로 확인하기 전에는 학년만으로 수업 난도를 확정할 수 없습니다. '
 '위 예시는 수업 방식 판단을 돕는 참고 자료이며 특정 역에서 수업이 제공된다는 의미가 아닙니다.</p>'
 '</div></section>')
rows=[];seen=set()
for st in DATA:
 if st["slug"]=="gukjegeumyungsenteo-busaneunhaeng":continue
 route="station-"+st["slug"]+"-elem-tutor.html"
 rec=mp[route];assert not rec["noindex"]
 p=SITE/rec["to"];old=p.read_text("utf8")
 assert old.count('data-enpt-learning-evidence="20261021"')==1
 head=re.search(r"<head\b.*?</head>",old,re.S|re.I).group()
 # remove several generic boilerplate blocks, keep site functional/commercial sections intact
 new=old
 dropped=[]
 for cls in ["mass-context","local-decision-note","enpt-learning-evidence","station-p0-editorial"]:
  pat=r'<section(?=[^>]*class="[^"]*\b'+re.escape(cls)+r'\b)[^>]*>.*?</section>'
  new,n=re.subn(pat,"",new,count=1,flags=re.S)
  if n:dropped.append(cls)
 assert "enpt-learning-evidence" in dropped and "station-p0-editorial" in dropped,(route,dropped)
 new=new.replace("</main>",section(st)+"</main>",1)
 assert re.search(r"<head\b.*?</head>",new,re.S|re.I).group()==head
 assert old.count('name="englishpt-consultation"')==new.count('name="englishpt-consultation"')
 assert old.count('<link rel="canonical"')==new.count('<link rel="canonical"')
 assert new.count('data-enpt-elem-originality="20261021"')==1
 p.write_text(new,"utf8")
 rows.append({"route":route,"removed_sections":"|".join(dropped),"old_bytes":len(old.encode()),"new_bytes":len(new.encode())})
assert len(rows)==910
with (OUT/"ALL_910_CHANGED.csv").open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
report={"status":"PASS_910_ELEMENTARY_SUBSTANTIVE_RESTRUCTURE","pages":910,"content_modules":len(SKILLS),"skill_check_modules":len(CHECKS),"all_head_and_form_meta_preserved":True,"station_ids_changed":0,"brand_changed":False,"production_published":False}
(OUT/"REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
print("P2_910_RESTRUCTURE_RESULT",json.dumps(report,ensure_ascii=False),flush=True)
