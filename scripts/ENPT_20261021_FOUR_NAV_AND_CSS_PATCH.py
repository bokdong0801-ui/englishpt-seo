#!/usr/bin/env python3
# coding: utf-8
"""Correct shared navigation contracts in staged Netlify Candidate; NO publish, no URL rewrites.
- 6 local student course intents already generated in signed release, never fabricate destination.
- International school & senior get their own real noindex course information pages.
- Center ONLY course-comparison content via shared CSS.
- All existing canonical, robots, OG, sitemap and form markup outside these hub pages preserved.
"""
import csv,gzip,hashlib,html,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/"thumb-21964-candidate"
OUT=ROOT/"four-route-qa";OUT.mkdir(exist_ok=True)
MAP=ROOT/"signed-qa-map"/"NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
assert SITE.is_dir() and MAP.is_file()
with gzip.open(MAP,"rt",encoding="utf-8") as fp:signed=json.load(fp)
source=signed["original_public_html_to_data_payload"]
assert len(source)==158571 and sum(not r["noindex"] for r in source.values())==21964
for intent in ["elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv"]:
 # A genuine generated regional route for the same area in the user's example.
 route="ulsan-buk-nongso2dong-"+intent+".html"
 assert route in source and (SITE/source[route]["to"]).is_file(),("MISSING_REAL_STUDENT_DESTINATION",route)
def read_route(route):
 if route in source:return SITE/source[route]["to"]
 return SITE/route
def keep_meta(old,new,route):
 for pat in [r'<link\s+rel="canonical"[^>]*>',r'<meta\s+name="robots"[^>]*>',r'<meta\s+property="og:image"[^>]*>']:
  assert re.findall(pat,old,re.I)==re.findall(pat,new,re.I),(route,pat)
 assert old.count('name="englishpt-consultation"')==new.count('name="englishpt-consultation"'),route
def patch_hub(route,method):
 p=read_route(route);old=p.read_text("utf8");new=method(old)
 assert new!=old,route
 keep_meta(old,new,route)
 p.write_text(new,"utf8")
 return {"route":route,"before_sha256":hashlib.sha256(old.encode()).hexdigest(),"after_sha256":hashlib.sha256(new.encode()).hexdigest(),"file":str(p.relative_to(SITE))}
STUDENT=[
 ("elem-tutor","초등학생 영어과외"),("elem-conv","초등학생 영어회화"),
 ("mid-tutor","중학생 영어과외"),("mid-conv","중학생 영어회화"),
 ("high-tutor","고등학생 영어과외"),("high-conv","고등학생 영어회화")
]
def student(s):
 a=re.search(r'<select data-region-intent>.*?</select>',s,re.S)
 assert a and a.group().count('<option value=')==4,"student_3_current_choices_mismatch"
 select='<select data-region-intent><option value="">과정 선택</option>'+''.join('<option value="'+v+'">'+t+'</option>' for v,t in STUDENT)+'</select>'
 s=s[:a.start()]+select+s[a.end():]
 for who,code,label in [("중학생","mid-tutor","중학생 영어과외"),("고등학생","high-tutor","고등학생 영어과외")]:
  pat=r'<button class="route-cta" type="button" data-open-form data-course="'+label+r'">.*?</button>'
  s,n=re.subn(pat,'<a class="route-cta" href="#region" data-region-preset="'+code+'">지역별 '+label+' 상세페이지 보기 →</a>',s,count=1)
  assert n==1,("tutor_action",code)
 s=s.replace("중등 지역별 과외 상세페이지는 준비 중입니다.","지역별 중학생 영어과외 상세페이지에서 내용을 먼저 살펴보세요.")
 s=s.replace("고등 지역별 과외 상세페이지는 준비 중입니다.","지역별 고등학생 영어과외 상세페이지에서 내용을 먼저 살펴보세요.")
 pat=r'<button class="route-cta" type="button" data-open-form data-course="국제학교 영어">.*?</button>'
 s,n=re.subn(pat,'<a class="route-cta" href="/international-school-english.html">국제학교 영어 자세히 보기 →</a>',s,count=1);assert n==1
 assert all('value="'+x+'"' in s for x,_ in STUDENT)
 assert 'data-course="국제학교 영어"' not in s
 return s
def homepage(s):
 assert 'href="english-conversation.html#senior"' in s
 return s.replace('href="english-conversation.html#senior"','href="/senior-english.html"')
def conversation(s):
 pat=r'<button class="route-cta" type="button" data-open-form data-course="시니어 영어">.*?</button>'
 new,n=re.subn(pat,'<a class="route-cta" href="/senior-english.html">시니어 영어 과정 자세히 보기 →</a>',s,count=1)
 assert n==1
 return new
changes=[patch_hub("student-english.html",student),patch_hub("englishpt.html",homepage),patch_hub("english-conversation.html",conversation)]
# Clone existing, working branded shell + consultation form from a real hub.
def write_guide(sourcehub,slug,title,desc,h1,parts):
 path=SITE/slug
 assert not path.exists(),("NEW_GUIDE_COLLIDES_EXISTING",slug)
 src=read_route(sourcehub).read_text("utf8")
 assert src.count('name="englishpt-consultation"')==1
 assert src.count('<main>')==1 and src.count('</main>')==1
 canon="https://englishpt.kr/"+slug
 # Named head tokens and structured data correctly reflect new PAGE (brand/organization unchanged).
 oldcanon=re.search(r'<link rel="canonical" href="([^"]+)"',src).group(1)
 src,nrobots=re.subn(r'<meta\s+name="robots"\s+content="[^"]*"\s*/?>','<meta name="robots" content="noindex,follow">',src,count=1,flags=re.I)
 assert nrobots==1,("COPY_HUB_ROBOTS_MISSING",sourcehub)
 src=re.sub(r'<title>.*?</title>',"<title>"+html.escape(title)+"</title>",src,count=1)
 src=re.sub(r'<meta name="description" content="[^"]*">','<meta name="description" content="'+html.escape(desc,quote=True)+'">',src,count=1)
 src=src.replace(oldcanon,canon)
 src=re.sub(r'(<meta property="og:title" content=")[^"]*(")',lambda m:m.group(1)+html.escape(title,quote=True)+m.group(2),src,count=1)
 src=re.sub(r'(<meta property="og:description" content=")[^"]*(")',lambda m:m.group(1)+html.escape(desc,quote=True)+m.group(2),src,count=1)
 # Replace JSON-LD page identifiers and title by parsing embedded JSON, leaving existing publisher/organization IDs intact.
 m=re.search(r'<script type="application/ld\+json">(.*?)</script>',src,re.S)
 if m:
  data=json.loads(m.group(1))
  for obj in data.get("@graph",[]):
   if obj.get("@type") in ("WebPage","CollectionPage"):
    obj["@id"]=canon+"#webpage";obj["url"]=canon;obj["name"]=title;obj["description"]=desc
  replacement='<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(",",":"))+'</script>'
  src=src[:m.start()]+replacement+src[m.end():]
 menu='<div class="breadcrumb wrap"><a href="/englishpt.html">홈</a><span> / </span><strong>'+html.escape(h1)+'</strong></div>'
 sections=''.join('<section class="section'+(' soft' if i%2 else '')+'"><div class="wrap narrow"><h2>'+html.escape(heading)+'</h2><p>'+html.escape(body)+'</p></div></section>' for i,(heading,body) in enumerate(parts))
 body='<main>'+menu+'<section class="hero"><div class="wrap"><div class="eyebrow">교육 과정 안내</div><h1>'+html.escape(h1)+'</h1><p class="hero-copy">'+html.escape(desc)+'</p><div class="hero-choice-actions"><button type="button" class="btn light" data-open-form data-course="'+html.escape(h1,quote=True)+'">이 과정 상담하기 →</button><a class="btn hero-secondary" href="/student-english.html"'+("" if "국제" in h1 else ' style="display:none"')+'>학생영어 과정 보기</a></div></div></section>'+sections+'<section class="section soft"><div class="wrap narrow"><h2>상담 전에 확인할 내용</h2><p>현재 수준, 목표, 희망하는 수업 방식과 지역을 정리해 두면 상담에 도움이 됩니다. 실제 수업 제공 여부와 일정은 별도로 확인해야 합니다.</p><button type="button" class="btn dark" data-open-form data-course="'+html.escape(h1,quote=True)+'">체험수업 상담 신청 →</button></div></section></main>'
 src,n=re.subn(r'<main>.*?</main>',lambda _:body,src,count=1,flags=re.S)
 assert n==1 and src.count('name="englishpt-consultation"')==1
 assert 'name="robots" content="noindex,follow"' in src
 path.write_text(src,"utf8")
 return {"route":slug,"sha256":hashlib.sha256(src.encode()).hexdigest(),"robots":"noindex,follow","has_form":True}
new_pages=[
 write_guide("student-english.html","international-school-english.html","국제학교 영어 | 발표·에세이·수업 이해","국제학교에서 필요한 수업 참여, 영어 발표, 읽기·쓰기 과정을 현재 수준에 맞춰 살펴보세요.","국제학교 영어",[
  ("국제학교 영어에서 먼저 확인할 기준","수업 언어에 익숙한지, 교과 내용을 읽고 이해하는지, 자신의 의견을 말과 글로 표현하는지 구분해 살펴봅니다. 해외 학교 경험이 없어도 현재 수준을 확인하면서 시작할 수 있습니다."),
  ("영어로 발표하고 토론하기","발표문을 외우는 것과 질문에 자기 생각을 답하는 것은 다릅니다. 짧은 의견 제시와 근거 문장 만들기를 단계적으로 연습할 수 있습니다."),
  ("에세이와 읽기","글을 읽고 중요한 정보 찾기, 주장·예시 구분, 간단한 단락 쓰기를 차례로 확인합니다. 실제 학교 과제 형식과 마감 일정에 맞춰 우선순위를 정합니다."),
  ("학부모 확인 사항","입학 준비, 학교 수업 적응, 교과영어 중 무엇이 필요한지 확인하고 재학 학교와 학년, 실제 과제 샘플을 상담에 준비하세요.")
 ]),
 write_guide("english-conversation.html","senior-english.html","시니어 영어회화 | 왕초보·여행·일상영어","시니어 학습자를 위한 영어 시작 기준, 여행·일상회화와 부담 없는 복습 방법을 안내합니다.","시니어 영어",[
  ("기초부터 시작하는 시니어 영어","영어를 오랫동안 사용하지 않았다면 친숙한 인사, 자기소개, 이름과 숫자 읽기처럼 실제 사용할 수 있는 표현부터 시작합니다."),
  ("여행과 일상에서 쓰는 영어","공항, 숙소, 길 찾기, 주문 등 필요한 상황을 먼저 골라 짧은 문장을 듣고 말하는 연습을 해봅니다. 모든 주제를 한꺼번에 학습할 필요는 없습니다."),
  ("속도와 반복 조절하기","한 번에 외울 표현 수보다 이해하고 직접 써보는 횟수를 중요하게 살펴봅니다. 발음·듣기 어려움과 문장 만들기 어려움을 별도로 확인합니다."),
  ("수업 방식 선택","대면 또는 화상 등 학습 환경과 이동 가능 범위, 선호하는 수업 시간·복습 방법을 확인한 후 실제 운영 가능한 방식은 상담으로 확인합니다.")
 ])
]
css_path=SITE/"assets/styles.css"
assert css_path.exists()
style="""
/* ENPT 20261021 / course comparison alignment; all intents, all responsive breakpoints */
.mass-context .wrap,.mass-context .wrap.narrow{display:flex;flex-direction:column;align-items:center;text-align:center;}
.mass-context .kicker,.mass-context h2{max-width:900px;margin-left:auto;margin-right:auto;text-align:center;}
.mass-context .context-block,.mass-context article.context-block{box-sizing:border-box;width:100%;max-width:940px;text-align:center;margin-left:auto;margin-right:auto;}
.mass-context .context-block h3,.mass-context .context-block p{text-align:center!important;margin-left:auto;margin-right:auto;}
.mass-context .context-block p{max-width:74ch;line-height:1.8;}
@media(max-width:760px){.mass-context .wrap,.mass-context .wrap.narrow{align-items:stretch;text-align:center}.mass-context .context-block{max-width:100%;padding-left:12px;padding-right:12px}}
"""
raw=css_path.read_text("utf8")
assert "ENPT 20261021 / course comparison alignment" not in raw
css_path.write_text(raw+"\n"+style,"utf8")
# Fallback for templates shipped with another shared stylesheet.
extra=[]
for rel in ["pilot.css","assets/pilot.css","styles.css"]:
 p=SITE/rel
 if p.exists():
  x=p.read_text("utf8")
  if "ENPT 20261021 / course comparison alignment" not in x:p.write_text(x+"\n"+style,"utf8");extra.append(rel)
evidence={"status":"PASS_FOUR_INTENTS_CORRECTED_AND_SENIOR_INTERNATIONAL_PAGES_CREATED","hub_modified":changes,"new_guides":new_pages,"student_option_count":6,"real_six_local_routes_verified":True,"one_CSS_rule_applied_to":"assets/styles.css","other_css_updated":extra,"all_existing_page_index_policy_unchanged":True,"new_guides_noindex":True,"old_forms_unchanged":True,"new_pages_have_form":True,"production_mutations":0}
(OUT/"PATCH_SUMMARY.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2),"utf8")
print("ENPT_FOUR_PATH_FIX",json.dumps(evidence,ensure_ascii=False),flush=True)
