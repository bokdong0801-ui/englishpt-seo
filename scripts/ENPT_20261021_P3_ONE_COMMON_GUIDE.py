#!/usr/bin/env python3
"""Create exactly one common elementary English learning guide inside staged unpublished site.
Keep guide noindex until separately approved; do not add sitemap entries.
"""
from pathlib import Path
import hashlib,json,re
root=Path(__file__).resolve().parents[1];site=root/"thumb-21964-candidate";out=root/"p3-elementary-architecture-qa"
guide=site/"elementary-english-guide.html"
assert not guide.exists()
content='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>초등 영어과외 학습 가이드 | 영어 읽기·말하기·복습</title>
<meta name="description" content="초등 영어를 시작하는 학생을 위한 읽기 진단, 문장 이해, 복습, 학부모 점검 안내">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="https://englishpt.kr/elementary-english-guide.html">
<link rel="stylesheet" href="/assets/styles.css"></head><body>
<header><nav aria-label="주요 메뉴"><a href="/englishpt.html">잉글리시PT</a> · <a href="/stations.html">역 찾기</a> · <a href="/courses.html">영어 과정 찾기</a></nav></header>
<main style="max-width:900px;margin:30px auto;padding:12px 22px;line-height:1.85">
<p>초등 영어과외 공통 학습 가이드</p><h1>초등 영어, 무엇을 먼저 살펴봐야 할까요?</h1>
<p>이 가이드는 전국 어느 지역에서든 참고할 수 있는 학습 정보입니다. 특정 역 주변의 수업 운영 여부, 강사 배치, 상담 가능 시간을 뜻하지 않습니다. 학년을 기준으로 학습을 결정하기보다 현재 읽기·듣기·말하기·쓰기에서 가능한 수준을 살펴보세요.</p>
<section><h2>1. 읽기의 시작점을 확인합니다</h2>
<p>짧은 문장을 아이가 혼자 읽게 하고 누가 무엇을 하는지 설명하게 해보세요. 예를 들어 “The bird is near the window.”라는 문장에서 bird, near, window의 뜻을 각각 알아도 위치 관계를 한 문장으로 말하지 못할 수 있습니다. 이때는 단어 시험만 늘리기보다 문장 안에서 단어가 연결되는 모습을 보여주는 것이 먼저입니다.</p>
<p>읽을 수 있는 단어 수와 문장 전체의 이해도를 분리해 기록하면, 파닉스부터 다시 시작할지 문장 독해로 넘어갈지 결정하는 데 도움이 됩니다.</p></section>
<section><h2>2. 듣기와 말하기는 답변 수준을 따로 봅니다</h2>
<p>“What do you like to do after school?”처럼 친숙한 질문을 짧게 들려주세요. 질문 내용을 알아들은 것과 즉시 영어로 말할 수 있는 것은 별개의 능력입니다. 첫 답변이 한 단어라면 완성된 문장을 바로 요구하기보다 “I like to read.”처럼 짧은 문장으로 넓혀볼 수 있습니다.</p>
<p>한 번 따라 말할 수 있는 문장보다 다른 질문에서도 스스로 사용할 수 있는 표현이 얼마나 되는지를 확인합니다.</p></section>
<section><h2>3. 문법은 설명보다 적용 여부로 점검합니다</h2>
<p>“She plays soccer.”와 “They play soccer.”를 비교해 주어가 달라질 때 동사가 어떻게 달라지는지 살펴보세요. 규칙을 외워서 말하는 능력과 새 문장에서 정확하게 사용하는 능력을 구별하는 것이 중요합니다.</p>
<p>이미 알고 있는 규칙을 반복해서 가르치기보다는 실제로 틀리는 문장을 모아 왜 틀렸는지 설명하게 해보세요.</p></section>
<section><h2>4. 오답과 복습을 연결합니다</h2>
<p>오답은 단어 뜻, 문장 구조, 문제 읽기, 시간 부족 중 어떤 이유인지 나눠 기록합니다. 틀린 답을 바로 고친 뒤 비슷한 문제 한 개를 다시 풀고, 며칠 뒤 새로운 문장에서 같은 원리를 적용하는지 확인해 보세요.</p>
<p>학부모는 한 번에 공부한 양보다 혼자 해결하는 문제가 늘어나는지, 도움을 요청하는 장면이 어떻게 달라지는지를 기록할 수 있습니다.</p></section>
<section><h2>5. 과외 방식과 수업 환경을 결정합니다</h2>
<p>학생이 어려워하는 활동이 읽기인지 말하기인지, 혼자 과제를 끝낼 수 있는지, 교사의 피드백이 어느 단계에서 필요한지 확인한 뒤 수업 방식을 비교합니다. 대면과 화상 수업의 적합성은 이동 시간, 집중 환경, 가정에서의 학습 지원 가능 여부 등에 따라 달라질 수 있습니다.</p>
<p>상담 때에는 최근 과제 한 개, 어려웠던 문장 두 개, 학생이 스스로 설명할 수 있는 문장 하나를 준비하면 현재 수준에 대한 대화를 구체적으로 시작할 수 있습니다.</p></section>
<section><h2>부모님이 확인할 질문</h2>
<ul><li>아이가 혼자 읽을 수 있는 문장과 설명을 들어야 하는 문장은 무엇인가요?</li>
<li>틀린 문제의 원인을 이해하고 다시 설명할 수 있나요?</li>
<li>학습 시간과 복습 시간을 무리 없이 유지할 수 있나요?</li>
<li>학년별 진도보다 실제 수준과 목표에 맞춰 수업을 조정할 수 있나요?</li>
<li>실제 수업 지역, 방식, 운영 여부는 확인됐나요?</li></ul>
</section><p><a href="/stations.html">역별 안내로 돌아가기</a> · <a href="/courses.html">과정별 안내 보기</a></p>
</main><footer style="max-width:900px;margin:10px auto;padding:20px"><a href="/privacy/">개인정보처리방침</a></footer></body></html>'''
assert '<meta name="robots" content="noindex,follow">' in content
guide.write_text(content,"utf8")
assert sum(1 for x in (site/"__pages").glob("*/*.page"))==158571
manifest={"status":"PASS_SINGLE_SHARED_ELEMENTARY_GUIDE_CREATED","new_static_guides":1,"guide_noindex":True,"preserved_indexable_count":21964,"preserved_noindex_generated_count":136607,"existing_canonicals_untouched":True,"existing_sitemaps_untouched":True,"sha256":hashlib.sha256(content.encode()).hexdigest(),"production_published":False}
(out/"NATIONAL_GUIDE_QA.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),"utf8")
print("P3_COMMON_GUIDE",json.dumps(manifest,ensure_ascii=False),flush=True)
