#!/usr/bin/env python3
"""Integrate three EXACT immutable Production HTML pages with isolated 18-page national region review.
This script modifies ONLY region-review-site/, never Netlify Production or GitHub source HTML.
Production files are fetched from pinned deploy and compared before/after form, canonical, SEO.
"""
from __future__ import annotations
import hashlib,json,pathlib,re,urllib.request
from html import escape

ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/"region-review-site"
EVIDENCE=ROOT/"region-review-evidence"
PINNED="https://6adafef5f2c6d196833683db--englishpt-seo.netlify.app"
PROD="https://englishpt.kr"
FILES=["englishpt.html","courses.html","student-english.html"]
STATIC=["assets/styles.css","assets/site.js","assets/favicon.svg","assets/locality-index.json"]
def get(path):
    req=urllib.request.Request(PINNED+"/"+path,method="GET",headers={"User-Agent":"ENPT-Protected-Region-Preview-Source-20261027","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=50) as r:
        assert r.status==200,(path,r.status)
        raw=r.read(2_500_000)
        return raw,r.headers.get("Content-Type","")
def form(html):
    result=re.search(r'<form\b[^>]*name="englishpt-consultation"[^>]*>[\s\S]*?</form>',html,re.I)
    assert result,"MISSING_EXACT_EXISTING_NETLIFY_CONSULTATION_FORM"
    return result.group(0)
def canonical(html):
    return re.findall(r'<link\s+rel="canonical"\s+href="([^"]+)"',html,re.I)
def robots(html):
    return re.findall(r'<meta\s+name="robots"\s+content="([^"]+)"',html,re.I)
INTEGRATION_CSS=r"""
.enpt-r-entry{background:#f1eee7!important;border-block:1px solid #dce5db;padding:54px 0!important}
.enpt-r-entry .wrap{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(230px,.85fr);gap:24px;align-items:center}
.enpt-r-entry .eyebrow{color:#3c7958!important}
.enpt-r-entry h2{font-size:clamp(24px,3.1vw,34px);line-height:1.3;margin:9px 0 13px;color:#1c3529}
.enpt-r-entry p{font-size:15px;line-height:1.75;color:#485e51;max-width:680px;margin:0}
.enpt-r-entry .enpt-r-buttons{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.enpt-r-entry .enpt-r-btn{border:0;background:#2c5e49;color:white!important;display:inline-flex;justify-content:center;align-items:center;min-height:45px;padding:11px 19px;border-radius:50px;text-decoration:none;font-weight:750;cursor:pointer}
.enpt-r-entry .enpt-r-btn.secondary{background:#dde9de;color:#254b37!important}
.enpt-r-entry .enpt-r-side{background:#fff;border:1px solid #dbe5dc;border-radius:18px;padding:23px}
.enpt-r-entry .enpt-r-side strong{display:block;color:#244a32;font-size:19px;margin-bottom:10px}
.enpt-r-entry .enpt-r-side span{display:block;color:#657369;font-size:14px;line-height:1.75}
.rg-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:15px!important}
.rg-card{min-height:148px!important;padding:24px!important;border-color:#cbdacf!important}
.rg-card small{font-size:13px!important;color:#53685a!important}
.rg-card strong{font-size:20px!important;line-height:1.4}
.rg-card b{font-size:14px!important}
.rg-lead{color:#40564a!important}
.rg-town-links a{color:#1d5234!important;font-weight:600}
.rg-search:focus-visible,.rg-card:focus-visible,.rg-town-links a:focus-visible{outline:3px solid #3e8060;outline-offset:2px}
@media(max-width:760px){.enpt-r-entry .wrap{grid-template-columns:1fr}.enpt-r-entry{padding:35px 0!important}}
@media(max-width:640px){.rg-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:10px!important}
.rg-card{padding:16px!important;min-height:136px!important}
.rg-card strong{font-size:16px!important}
.rg-card small{font-size:12px!important}
.enpt-r-entry .enpt-r-side{padding:17px}
.enpt-r-entry .enpt-r-btn{font-size:14px;flex:1}
}
"""
CONTENT={
"englishpt.html":("전국 지역별 영어 안내","동네에서 어떤 영어를 시작할지 살펴보세요.","서울부터 제주까지 지역별 영어과외·영어회화·시험영어 안내를 모았습니다. 시도와 시군구를 고르면 기존 동네별 상세페이지를 확인할 수 있습니다."),
"courses.html":("지역별 과정 찾기","원하는 동네에서 영어 과정을 찾아보세요.","대상과 목표를 선택했다면, 다음에는 지역을 살펴보세요. 시도 → 시군구 → 읍면동별 안내와 연결됩니다."),
"student-english.html":("학생영어 · 지역별 안내","우리 동네 초·중·고 영어를 살펴보세요.","학생의 학년과 목표에 맞는 영어과외·회화 안내를 지역별로 확인할 수 있습니다. 상담 신청 방식과 기존 학습 안내는 그대로 유지됩니다.")
}
def entry(page):
    eyebrow,title,desc=CONTENT[page]
    return f'<section class="section soft enpt-r-entry" aria-label="지역별 영어 안내" id="enpt-regions-entry-20261027"><div class="wrap"><div><div class="eyebrow">{escape(eyebrow)}</div><h2>{escape(title)}</h2><p>{escape(desc)}</p><div class="enpt-r-buttons"><a class="enpt-r-btn" href="/regions.html">전국 지역별 영어 찾기 →</a><button class="enpt-r-btn secondary" type="button" data-open-form>체험수업 신청</button></div></div><aside class="enpt-r-side"><strong>시도 → 시군구 → 읍면동</strong><span>기존 지역별 학습 안내와 연결됩니다. 원하는 지역이나 과정을 아직 정하지 못했다면 상담 신청을 통해 안내받을 수 있습니다.</span></aside></div></section>'
def integrate(page,raw):
    html=raw.decode("utf8","strict")
    original_form=form(html)
    original_can=canonical(html)
    original_robot=robots(html)
    assert original_can==[PROD+"/"+page],("CANONICAL_MISMATCH",page,original_can)
    assert len(original_robot)==1,("ROBOTS_MISSING_OR_DUPLICATE",page,original_robot)
    assert html.count('<nav class="desktop-nav" aria-label="주요 메뉴">')==1
    assert html.count('<div id="mobileNav" class="mobile-nav" hidden>')==1
    html=html.replace('<nav class="desktop-nav" aria-label="주요 메뉴">','<nav class="desktop-nav" aria-label="주요 메뉴"><a href="/regions.html" class="enpt-region-nav-link">지역별 찾기</a>',1)
    html=html.replace('<div id="mobileNav" class="mobile-nav" hidden>','<div id="mobileNav" class="mobile-nav" hidden>',1)
    # Insert after mobile nav inner wrapper, not beside it
    marker='<div id="mobileNav" class="mobile-nav" hidden><div class="wrap">'
    assert html.count(marker)==1
    html=html.replace(marker,marker+'<a href="/regions.html" class="enpt-region-nav-link">지역별 찾기</a>',1)
    assert html.count('<section class="final"')==1,(page,"FINAL_SECTION_MISSING")
    html=html.replace('<section class="final"',entry(page)+'<section class="final"',1)
    html=html.replace("</head>",'<style id="enpt-region-integration-css">'+INTEGRATION_CSS+"</style></head>",1)
    assert form(html)==original_form,("FORM_MARKUP_CHANGED",page)
    assert canonical(html)==original_can,("CANONICAL_CHANGED",page)
    assert robots(html)==original_robot,("ROBOTS_CHANGED",page)
    assert html.count("enpt-region-nav-link")==2
    assert html.count('id="enpt-regions-entry-20261027"')==1
    return html,{"path":page,"bytes_original":len(raw),"sha256_original":hashlib.sha256(raw).hexdigest(),"form_html_sha256_unchanged":hashlib.sha256(original_form.encode()).hexdigest(),"canonical_unchanged":original_can[0],"robots_unchanged":original_robot[0],"region_entry_count":1,"nav_links":2}
def main():
    assert SITE.joinpath("regions.html").exists()
    assert len(list(SITE.glob("regions/*.html")))==17
    summary={"status":"PASS_PINNED_PRODUCTION_CORE_PRESERVATION","immutable_source":PINNED,"added_region_pages":18,"patched_preview_core_pages":[],"existing_source_written":0,"production_published":False}
    # Preserve originals of region HTML in isolated copy. Only add CSS for review-specific QA.
    for p in [SITE/"regions.html",*SITE.glob("regions/*.html")]:
        s=p.read_text("utf8")
        assert 'name="englishpt-consultation"' in s and '<meta name="robots" content="noindex,nofollow">' in s
        s=s.replace("</head>",'<style id="enpt-region-polish-css">'+INTEGRATION_CSS+"</style></head>",1)
        p.write_text(s,"utf8")
    for file in FILES:
        raw,kind=get(file)
        assert "text/html" in kind.lower(),(file,"NONHTML",kind)
        mod,row=integrate(file,raw)
        (SITE/file).write_text(mod,"utf8")
        summary["patched_preview_core_pages"].append(row)
    # Current immutable Production assets; avoid mixing previously stored source version with newer HTML.
    for file in STATIC:
        raw,kind=get(file)
        if file.endswith(".json"):
            index=json.loads(raw.decode("utf8"))
            assert len(index)==5149,("LOCALITY_INDEX_WRONG",len(index))
        out=SITE/file
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(raw)
    assert SITE.joinpath("robots.txt").read_text("utf8").strip().endswith("Disallow: /")
    assert "X-Robots-Tag: noindex, nofollow" in SITE.joinpath("_headers").read_text("utf8")
    summary["html_page_total"]=len(list(SITE.rglob("*.html")))
    assert summary["html_page_total"]==22,summary  # 18 region + 3 protected core + privacy/index.html
    summary["netlify_forms_submitted"]=0
    EVIDENCE.mkdir(exist_ok=True)
    (EVIDENCE/"INTEGRATION_SOURCE_QA.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),"utf8")
    print("ENPT_REGION_INTEGRATION_QA",json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
