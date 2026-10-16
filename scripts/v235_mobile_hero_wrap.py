#!/usr/bin/env python3
"""v23.5: adapt long region/station Hero H1 to mobile widths; offline and text-preserving.
The only HTML change is a data attribute on the existing H1.
"""
import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

H1 = re.compile(r'(<h1\b)([^>]*)(>)(.*?)(</h1>)', flags=re.I|re.S)
ATTR = re.compile(r'\sdata-v235-hero-wrap="[^"]*"')
BR = re.compile(r'<br\s*/?>', flags=re.I)
TAG = re.compile(r'<[^>]+>')
TOKEN = re.compile(r'[가-힣A-Za-z0-9]+')
FLAG = '/* V23.5 RESPONSIVE LONG HERO TITLES — MOBILE ONLY */'
CSS = '''
/* V23.5 RESPONSIVE LONG HERO TITLES — MOBILE ONLY */
@media(max-width:760px){
  .hero h1[data-v235-hero-wrap]{
    min-width:0;
    max-width:100%;
    line-height:1.22;
    letter-spacing:-.035em;
    text-wrap:balance;
    word-break:keep-all;
    overflow-wrap:anywhere;
    hyphens:none;
  }
  .hero h1[data-v235-hero-wrap="long"]{
    font-size:clamp(25px,7.3vw,32px)!important;
    line-height:1.24;
  }
  .hero h1[data-v235-hero-wrap="xlong"]{
    font-size:clamp(22px,6.7vw,28px)!important;
    line-height:1.27;
  }
}
@media(max-width:390px){
  .hero h1[data-v235-hero-wrap="long"]{
    font-size:clamp(23px,7vw,28px)!important;
  }
  .hero h1[data-v235-hero-wrap="xlong"]{
    font-size:clamp(20px,6.2vw,24px)!important;
  }
}
@media(max-width:340px){
  .hero h1[data-v235-hero-wrap="long"]{font-size:23px!important}
  .hero h1[data-v235-hero-wrap="xlong"]{font-size:20px!important}
}
'''

def classify(markup, filename):
    # Keep H1 text exactly intact; selection is independent from locality name.
    normalized = BR.sub(' ', markup)
    text = html.unescape(TAG.sub(' ', normalized))
    text = ' '.join(text.split())
    words = TOKEN.findall(text)
    longest = max((len(w) for w in words), default=0)
    total = len(text.replace(' ', ''))
    # Long station names before a deliberate <br> should be more conservative.
    station_word = 0
    if filename.startswith('station-'):
        first_line = BR.split(markup, maxsplit=1)[0]
        station_word = max((len(w) for w in TOKEN.findall(html.unescape(TAG.sub('',first_line)))),default=0)
    if longest >= 13 or total >= 26 or station_word >= 13:
        mode = 'xlong'
    elif longest >= 9 or total >= 18 or station_word >= 9:
        mode = 'long'
    else:
        mode = 'regular'
    return mode, text, longest, total

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--expected',type=int,default=140391)
    a=p.parse_args()
    root=a.root.resolve()
    pages=sorted(root.glob('*.html'))
    generated=[x for x in pages if x.name not in ('index.html','404.html')]
    report={'version':'v23.5','status':'RUNNING',
       'source_run':'38689660290','source_sha':'a18b8901ecda7d37f65e35b15f03d579ec63c70f',
       'corrected_nav_run':'38771578401',
       'generated_expected':a.expected,'generated_found':len(generated),
       'html_scanned':len(pages),'h1_processed':0,'h1_updated':0,
       'modes':{},'css_updated':[],'errors':[],'error_count':0,
       'og_metadata_unchanged':True,'hero_text_unchanged':True,
       'production_deployed':False,'netlify_deployed':False}
    errors=[]; modes=Counter()
    try:
        assert len(generated)==a.expected,(len(generated),a.expected)
        assert len(pages)==a.expected+2,(len(pages),a.expected+2)
        for cssname in ('pilot.css','assets/styles.css'):
            path=root/cssname
            if not path.is_file():
                raise RuntimeError('Missing required stylesheet '+cssname)
            css=path.read_text(encoding='utf-8')
            if FLAG not in css:
                path.write_text(css+'\n'+CSS,encoding='utf-8')
                report['css_updated'].append(cssname)
        # Never modify OG metadata, canonicals, links, content, or H1 words.
        for i, page in enumerate(pages):
            try:
                content=page.read_text(encoding='utf-8')
                matches=list(H1.finditer(content))
                if len(matches)!=1:
                    raise RuntimeError(f'expected exactly one H1, got {len(matches)}')
                m=matches[0]
                mode,text,longest,total=classify(m.group(4),page.name)
                attrs=ATTR.sub('',m.group(2))
                newhead=m.group(1)+attrs+f' data-v235-hero-wrap="{mode}"'+m.group(3)+m.group(4)+m.group(5)
                updated=content[:m.start()]+newhead+content[m.end():]
                if updated!=content:
                    page.write_text(updated,encoding='utf-8')
                    report['h1_updated']+=1
                modes[mode]+=1
                report['h1_processed']+=1
                if (i+1)%25000==0:
                    print('V235_HERO_WRAP_PROGRESS',i+1,len(pages),dict(modes),flush=True)
            except Exception as exc:
                if len(errors)<100: errors.append({'file':page.name,'reason':str(exc)})
                report['error_count']+=1
        if report['h1_processed']!=len(pages):
            report['error_count']+=1
            errors.append({'file':'(all)','reason':'missing_h1_coverage'})
    except Exception as exc:
        report['error_count']+=1
        errors.append({'file':'(runner)','reason':repr(exc)})
    finally:
        report['modes']=dict(modes)
        report['errors']=errors
        report['status']='PASS_V235_HERO_ALL' if report['error_count']==0 else 'FAIL_V235_HERO_ALL'
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(report['status'],'processed',report['h1_processed'],'modes',dict(modes),'errors',report['error_count'],flush=True)
    return 0 if report['status'].startswith('PASS') else 1

if __name__=='__main__':
    sys.exit(main())
