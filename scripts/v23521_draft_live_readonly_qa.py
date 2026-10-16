#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v23.5.2.1 immutable isolated Draft additional editorial + real-click audit.

Do not POST; do not submit forms; do not touch production. Acts on previous
full 158,571 HTML source and live six tutor representative pages only.
"""
import json,os,sys,traceback
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

BASE=(os.getenv('REVIEW_DEPLOY_URL') or '').rstrip('/')
OUT=Path('v23521-live-report')
OUT.mkdir(parents=True,exist_ok=True)
AREAS={'gyeongnam-milyang-naeidong':'내이동','seoul-jongno-sajikdong':'사직동'}
GRADES={'elem-tutor':'초등학생영어과외','mid-tutor':'중학생영어과외','high-tutor':'고등학생영어과외'}
LINKS={
 'elem-tutor':'초등학생영어과외','mid-tutor':'중학생영어과외','high-tutor':'고등학생영어과외',
 'elem-conv':'초등학생영어회화','mid-conv':'중학생영어회화','high-conv':'고등학생영어회화'}
EXPECTED_HOST='englishpt-final-ia-review-bokdong.netlify.app'
if not BASE.startswith('https://') or not urlsplit(BASE).hostname.endswith('--'+EXPECTED_HOST):
    raise SystemExit('Safe unique Netlify Draft host required')
if len(urlsplit(BASE).hostname.split('--')[0])!=24:
    raise SystemExit('Expected immutable Netlify deploy ID; mutable alias is not accepted')

def emit(filename,data):
 (OUT/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(filename,data.get('status'),flush=True)

def html_phase():
 r={'status':'RUNNING','unique_draft':BASE,'checks':[],'errors':[],'production_deployed':False,'submitted_forms':0}
 for slug,locality in AREAS.items():
  for mode,label in GRADES.items():
   name=slug+'-'+mode+'.html'
   try:
    req=Request(BASE+'/'+name,headers={'User-Agent':'EnglishPT-v23521-GET-read-only'})
    with urlopen(req,timeout=60) as res:
     status=res.status;content=res.read().decode('utf8','replace');headers=dict(res.headers.items())
    if status!=200:raise ValueError('HTML HTTP not 200')
    if 'noindex' not in headers.get('X-Robots-Tag','').lower():
     raise ValueError('Review Draft global noindex protection is missing')
    if '<title>' not in content or 'rel="canonical"' not in content:
     raise ValueError('title/canonical missing')
    if content.count('data-v2352-section=')!=5:
     raise ValueError('five new tutor sections missing')
    if content.count('class="faq-item"')!=6:raise ValueError('6 FAQ items missing')
    if '체험수업 신청' in content:raise ValueError('old trial request wording remains')
    if '영어과외 상담 신청' not in content:raise ValueError('revised tutoring CTA wording missing')
    if 'class="section mass-context"' in content or '수업에서 확인하는 예시' in content:
     raise ValueError('duplicated old tutoring instructions remain')
    if content.count('class="v2352-note"')!=1:
     raise ValueError('required single example disclaimer changed')
    if 'id="leadRequestType" name="requestType" value="영어과외 상담 신청"' not in content:
     raise ValueError('tutor requestType not aligned to consultation')
    if 'name="englishpt-consultation" method="POST" data-netlify="true"' not in content:
     raise ValueError('Netlify consultation form missing')
    if 'name="consent"' not in content:raise ValueError('consent field missing')
    # CDN-served HTML can serialize attributes differently from frozen source.
    # HTMLParser also accepts unquoted / single-quoted / reordered attrs.
    from html.parser import HTMLParser
    class CardLinks(HTMLParser):
     def __init__(self):
      super().__init__(convert_charrefs=True)
      self.links=[]
     def handle_starttag(self,tag,attrs):
      if tag!='a':return
      a=dict(attrs);classes=set((a.get('class') or '').split())
      for candidate in ('related-course-tutor','related-course-conversation'):
       if candidate in classes:self.links.append((candidate,a.get('href') or ''))
    cards=CardLinks();cards.feed(content)
    modes=('elem-tutor','mid-tutor','high-tutor','elem-conv','mid-conv','high-conv')
    if len(cards.links)!=6:
     raise ValueError('Expected six parsed regional course anchors, got '+str(cards.links))
    for intended in modes:
     path='/'+slug+'-'+intended
     if not any(h.rstrip('/') in (path,path+'.html') for _,h in cards.links):
      raise ValueError('Missing course link: '+path)
    if mode=='elem-tutor' and '학교 영어가 어렵다면 읽기·문법 중 무엇부터 살펴봐야 하나요?' not in content:
     raise ValueError('elementary parent FAQ improvement missing')
    if mode=='high-tutor' and '고2에서 고3으로 올라가기 전 무엇을 먼저 점검해야 하나요?' not in content:
     raise ValueError('high-school parent FAQ improvement missing')
    r['checks'].append({'file':name,'http_status':status,'content_sections':5,'faqs':6,'consultation_copy':'PASS','region':locality})
    print('V23521_EDITED_LIVE_TUTOR_HTML_PASS',name,flush=True)
   except Exception as e:
    r['errors'].append({'file':name,'error':repr(e)})
    print('::error::V23521_LIVE_HTML '+name+': '+repr(e),flush=True)
 r['status']='PASS_V23521_LIVE_COPY_AND_FORM_HTML' if len(r['checks'])==6 and not r['errors'] else 'HOLD_V23521_LIVE_COPY_AND_FORM_HTML'
 emit('V23521_LIVE_COPY_HTML_QA.json',r)
 return r['status'].startswith('PASS')

def clicks_phase():
 r={'status':'RUNNING','unique_draft':BASE,'clicks':[],'errors':[],'post_requests_blocked':0,
   'form_submitted':False,'production_deployed':False,'screenshot_count':0}
 shots=OUT/'click_screenshots';shots.mkdir(exist_ok=True)
 import shutil
 with sync_playwright() as pw:
  binary=shutil.which('google-chrome') or shutil.which('google-chrome-stable') or shutil.which('chromium')
  opt={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
  if binary:opt['executable_path']=binary
  browser=pw.chromium.launch(**opt)
  try:
   for width in (390,1440):
    ctx=browser.new_context(viewport={'width':width,'height':900})
    def guard(route):
     if route.request.method not in ('GET','HEAD'):
      r['post_requests_blocked']+=1;route.abort()
     else:route.continue_()
    ctx.route('**/*',guard)
    page=ctx.new_page()
    page.add_init_script("""document.addEventListener('submit',event=>{
      event.preventDefault(); event.stopImmediatePropagation();
      window.__REQUEST_SUBMISSION_BLOCKED__=true;},true);""")
    try:
     for slug in AREAS:
      url=BASE+'/'+slug+'-elem-tutor.html'
      for mode,label in LINKS.items():
       try:
        response=page.goto(url,wait_until='domcontentloaded',timeout=65000)
        if not response or response.status!=200:raise ValueError('source not HTTP 200')
        link=page.locator('article.related-group').filter(has=page.locator('h3',has_text='학생 영어')).locator('a').filter(has_text=label)
        if link.count()!=1:raise ValueError('missing or duplicated '+label)
        href=link.get_attribute('href') or ''
        expected='/'+slug+'-'+mode
        if href.rstrip('/') not in (expected,expected+'.html'):
         raise ValueError('incorrect link target '+repr(href))
        link.scroll_into_view_if_needed()
        link.click(timeout=15000)
        page.wait_for_load_state('domcontentloaded',timeout=30000)
        landed=urlsplit(page.url).path.rstrip('/')
        if landed not in (expected,expected+'.html'):
         raise ValueError('clicked URL went to wrong page: '+landed)
        if label not in page.locator('h1').first.inner_text():
         raise ValueError('clicked page has wrong H1')
        if page.locator('#consultation-preview form').count()!=1:
         raise ValueError('consultation form missing after navigation')
        r['clicks'].append({'slug':slug,'width':width,'course':mode,'landed':landed})
        print('V23521_LIVE_NAV_REAL_CLICK_PASS',width,slug,mode,flush=True)
       except Exception as e:
        r['errors'].append({'slug':slug,'width':width,'course':mode,'error':repr(e)})
        print('::error::V23521_NAV_CLICK '+repr(e),flush=True)
      for mode,label in GRADES.items():
       name=slug+'-'+mode+'.html'
       try:
        rr=page.goto(BASE+'/'+name,wait_until='domcontentloaded',timeout=60000)
        if not rr or rr.status!=200:raise ValueError('tutor destination not HTTP 200')
        hero=page.locator('.hero-actions a[href="#consultation-preview"]').first
        new=page.locator('a.v2352-small-cta[href="#consultation-preview"]')
        if hero.count()!=1 or new.count()!=1:raise ValueError('CTA missing')
        for selector,button in (('hero',hero),('parent',new)):
         button.scroll_into_view_if_needed()
         button.click(timeout=12000)
         form=page.locator('#consultation-preview form')
         if form.count()!=1:raise ValueError('form missing after CTA')
         # Input[type=hidden].value does NOT appear in innerText.
         # The revised wording is visible on the actual submit button.
         submit=form.locator('button[type="submit"]').first
         if submit.count()!=1 or '영어과외 상담 신청' not in submit.inner_text():
          raise ValueError('visible submit button has wrong tutoring copy')
         request_type=form.locator('input[name="requestType"]').first
         if request_type.count()!=1 or request_type.input_value()!='영어과외 상담 신청':
          raise ValueError('hidden requestType does not match revised tutoring copy')
         subject=form.locator('input[name="subject"]').first
         if subject.count()!=1 or '영어과외 상담 신청' not in subject.input_value():
          raise ValueError('hidden subject is inconsistent with submit label')
         p=shots/(name[:-5]+'-'+str(width)+'-'+selector+'.png')
         form.scroll_into_view_if_needed()
         page.screenshot(path=str(p),full_page=False,timeout=21000)
         r['screenshot_count']+=1
         r['clicks'].append({'slug':slug,'width':width,'course':mode,'cta':selector,'form_reached':True})
        print('V23521_LIVE_REVISED_FORM_CTA_PASS',width,slug,mode,flush=True)
       except Exception as e:
        r['errors'].append({'slug':slug,'width':width,'course':mode,'form_cta_error':repr(e)})
        print('::error::V23521_FORM_CTA '+repr(e),flush=True)
    finally:ctx.close()
  finally:browser.close()
 nav=[x for x in r['clicks'] if 'landed' in x]
 ctas=[x for x in r['clicks'] if x.get('form_reached')]
 r['navigation_clicks']=len(nav)
 r['new_copy_cta_checks']=len(ctas)
 r['status']='PASS_V23521_LIVE_COURSE_LINKS_AND_REVISED_FORM' if not r['errors'] and len(nav)==24 and len(ctas)==24 else 'HOLD_V23521_LIVE_COURSE_LINKS_AND_REVISED_FORM'
 emit('V23521_LIVE_CLICKS_CTA_QA.json',r)
 return r['status'].startswith('PASS')
if __name__=='__main__':
 phase=sys.argv[1] if len(sys.argv)>1 else 'html'
 success=html_phase() if phase=='html' else clicks_phase()
 sys.exit(0 if success else 1)
