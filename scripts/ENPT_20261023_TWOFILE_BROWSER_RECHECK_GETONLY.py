#!/usr/bin/env python3
# coding: utf-8
"""Read-only production-safe 390/768/1440 screenshot + 911 station UI navigation + ICO health."""
import datetime,json,os,pathlib,re,urllib.request,urllib.error
from playwright.sync_api import sync_playwright
from shutil import which
BASE="https://enptstationfaviconfix20261023--englishpt-seo.netlify.app"
SID="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
OLD="6ad87e6bd3bc041359320392"
OUT=pathlib.Path("enpt-twofile-browser-qa");OUT.mkdir(exist_ok=True)
def api(path):
    req=urllib.request.Request('https://api.netlify.com/api/v1/'+path,
       headers={'Authorization':'Bearer '+os.environ['NETLIFY_AUTH_TOKEN']},method='GET')
    with urllib.request.urlopen(req,timeout=35) as f:return json.load(f)
assert api('sites/'+SID)['published_deploy']['id']==OLD,'BASE_PRODUCTION_CHANGED'
rows=[];errors=[];non_get=[]
with sync_playwright() as pw:
    chrome=which('google-chrome') or which('chromium') or which('chromium-browser')
    assert chrome
    browser=pw.chromium.launch(executable_path=chrome,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    for width in (390,768,1440):
        ctx=browser.new_context(viewport={'width':width,'height':900},locale='ko-KR')
        def protect(route):
            if route.request.method not in ('GET','HEAD'):
                non_get.append({'method':route.request.method,'url':route.request.url})
                route.abort()
            else:route.continue_()
        ctx.route('**/*',protect)
        p=ctx.new_page();p.set_default_timeout(18000)
        row={'width':width,'checks':[],'errors':[]}
        try:
            resp=p.goto(BASE+'/stations.html',wait_until='networkidle',timeout=65000)
            assert resp and resp.status==200
            assert p.locator('#stationSearch').count()==1
            assert p.locator('#enptStationLine').count()==1
            assert p.locator('#enptStationClear').count()==1
            assert p.locator('#enptStationResults').count()==1
            assert p.locator('#enptStationLine option').count()==38, '37_LINES_PLUS_PROMPT'
            assert p.locator('link[rel="canonical"]').get_attribute('href')=='https://englishpt.kr/stations.html'
            assert p.locator('meta[name="robots"]').get_attribute('content').startswith('index,follow')
            assert p.locator('form[name="englishpt-consultation"]').count()==1
            assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+12'),"STATION_HORIZONTAL_OVERFLOW"
            row['checks'].append('37_line_selector_canonical_form_mobile_no_overflow')
            p.screenshot(path=str(OUT/('stations_'+str(width)+'.png')),full_page=False)
            search=p.locator('#stationSearch')
            search.fill('강남역')
            p.wait_for_timeout(280)
            text=p.locator('#enptStationResults').inner_text()
            assert '검색 결과' in text,text
            assert p.locator('.station-index-link:visible').count()>=1,'SEARCH_EMPTY'
            assert any('강남역' in t for t in p.locator('.station-index-link:visible').all_inner_texts()),"GANGNAM_NO_RESULT"
            row['checks'].append('search_gangnam_finds_link')
            p.locator('#enptStationClear').click()
            p.wait_for_timeout(250)
            assert p.locator('#stationSearch').input_value()==''
            assert '911개 역' in p.locator('#enptStationResults').inner_text()
            row['checks'].append('reset_clears_and_shows_all_911')
            # Existing heading may be "2호선 (N개 역)", not exactly "2호선".
            opt=p.locator('#enptStationLine option').evaluate_all(
                "(opts)=>opts.find(x=>(x.textContent||'').includes('2호선'))?.value || ''")
            assert opt,"TWO_LINE_OPTION_NOT_PRESENT"
            p.locator('#enptStationLine').select_option(value=opt)
            p.wait_for_timeout(150)
            assert p.locator('#enptStationLine').input_value()
            row['checks'].append('2line_jump_selection')
            result=p.request.get(BASE+'/favicon.ico',timeout=25000)
            assert result.status==200,result.status
            assert 'image/' in result.headers.get('content-type',''),result.headers
            icondata=result.body()
            assert icondata[:4]==bytes([0,0,1,0]), 'NOT_ICO_MAGIC'
            row['checks'].append('root_favicon_200_real_ico')
            asset=p.request.get(BASE+'/assets/favicon.svg',timeout=25000)
            assert asset.status==200
            row['checks'].append('original_svg_still_200')
        except Exception as e:row['errors'].append(type(e).__name__+':'+str(e).splitlines()[0][:260])
        rows.append(row)
        if row['errors']:errors.append(row)
        p.close();ctx.close()
    browser.close()
assert api('sites/'+SID)['published_deploy']['id']==OLD
result={'status':'PASS_TWOFILE_PREVIEW_CHROME_RESPONSIVE_STATIONS_AND_FAVICON' if not errors and not non_get else 'HOLD_TWOFILE_PREVIEW_BROWSER',
        'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'viewports':[390,768,1440],'tests':rows,'errors':errors,'unexpected_non_get_requests':non_get,
        'forms_submitted':0,'production_still_original':OLD}
(OUT/'TWOFILE_BROWSER_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print('ENPT_TWOFILE_BROWSER_VERDICT',json.dumps({k:v for k,v in result.items() if k!='tests'},ensure_ascii=False),flush=True)
if errors or non_get:raise SystemExit('HOLD_NO_PROD_PUBLISH')
