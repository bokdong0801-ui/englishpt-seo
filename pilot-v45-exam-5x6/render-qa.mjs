import { chromium } from 'playwright';
import fs from 'node:fs';

const manifestPath='pilot-v45-exam-5x6/PILOT_EXAM_5X6_MANIFEST_V1.json';
const outPath='pilot-v45-exam-5x6/PILOT_EXAM_5X6_RENDER_QA_V1.json';
const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
const browser=await chromium.launch({headless:true});
const viewports=[
  {name:'desktop',width:1440,height:1000},
  {name:'mobile',width:390,height:844}
];
const results=[];
let failures=0;

for(const item of manifest.files){
  const file=item.path.split('/').pop();
  for(const vp of viewports){
    const context=await browser.newContext({viewport:{width:vp.width,height:vp.height}});
    const page=await context.newPage();
    const errors=[];
    page.on('console',msg=>{ if(msg.type()==='error') errors.push('console:'+msg.text()); });
    page.on('pageerror',err=>errors.push('pageerror:'+err.message));

    const url='http://127.0.0.1:8000/pilot-v45-exam-5x6/'+encodeURIComponent(file);
    let navError=null;
    try{
      await page.goto(url,{waitUntil:'domcontentloaded',timeout:10000});
      await page.waitForTimeout(50);
    }catch(e){
      navError=e.message;
    }

    const metrics=navError?null:await page.evaluate(()=>{
      const h1=document.querySelector('h1');
      const heroPhone=document.querySelector('.hero a[href="tel:+821050068027"]');
      const contentLink=document.querySelector('.hero a[href="#detail"]');
      const consultLink=document.querySelector('.hero a[href="#consultation-preview"]');
      const isVisible=(el)=>{
        if(!el) return false;
        const s=getComputedStyle(el);
        const r=el.getBoundingClientRect();
        return s.display!=='none' && s.visibility!=='hidden' && Number(s.opacity)!==0 && r.width>0 && r.height>0;
      };
      return {
        h1Count:document.querySelectorAll('h1').length,
        h1:h1?.textContent?.trim()||'',
        h1Visible:isVisible(h1),
        scrollWidth:document.documentElement.scrollWidth,
        bodyScrollWidth:document.body.scrollWidth,
        innerWidth:window.innerWidth,
        phoneLinks:document.querySelectorAll('a[href="tel:+821050068027"]').length,
        heroPhoneVisible:isVisible(heroPhone),
        detailCtaVisible:isVisible(contentLink),
        consultCtaVisible:isVisible(consultLink),
        robots:document.querySelector('meta[name="robots"]')?.getAttribute('content')||'',
        canonical:document.querySelector('link[rel="canonical"]')?.getAttribute('href')||'',
        bodyProductionFlag:document.body?.dataset?.productionDeploy||'',
        bodyHeight:document.body?.scrollHeight||0
      };
    });

    const overflow=metrics ? Math.max(metrics.scrollWidth,metrics.bodyScrollWidth) > metrics.innerWidth+1 : true;
    const expectedH1=item.h1;
    const pass=!navError &&
      errors.length===0 &&
      !overflow &&
      metrics.h1Count===1 &&
      metrics.h1===expectedH1 &&
      metrics.h1Visible &&
      metrics.phoneLinks>0 &&
      metrics.heroPhoneVisible &&
      metrics.detailCtaVisible &&
      metrics.consultCtaVisible &&
      metrics.robots.toLowerCase().includes('noindex') &&
      metrics.canonical===item.canonical &&
      metrics.bodyProductionFlag==='false' &&
      metrics.bodyHeight>vp.height;

    if(!pass) failures++;
    results.push({
      file,
      exam:item.exam,
      locality:item.locality,
      viewport:vp.name,
      pass,
      navError,
      errors,
      overflow,
      metrics,
      expectedH1
    });
    await context.close();
  }
}
await browser.close();

const summary={
  version:'1.0',
  page_count:manifest.files.length,
  render_cases:results.length,
  desktop_cases:results.filter(x=>x.viewport==='desktop').length,
  mobile_cases:results.filter(x=>x.viewport==='mobile').length,
  failures,
  horizontal_overflow_failures:results.filter(x=>x.overflow).length,
  console_or_page_error_cases:results.filter(x=>x.errors?.length).length,
  h1_visibility_failures:results.filter(x=>x.metrics && !x.metrics.h1Visible).length,
  hero_phone_visibility_failures:results.filter(x=>x.metrics && !x.metrics.heroPhoneVisible).length,
  hero_detail_cta_visibility_failures:results.filter(x=>x.metrics && !x.metrics.detailCtaVisible).length,
  hero_consult_cta_visibility_failures:results.filter(x=>x.metrics && !x.metrics.consultCtaVisible).length,
  status:failures===0?'PASS':'FAIL',
  gold_standard:'V4_5_FULL_DEPTH_6_EXAM_GOLD_STANDARD.md',
  production_deploy:false,
  results
};
fs.writeFileSync(outPath,JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({
  status:summary.status,
  render_cases:summary.render_cases,
  desktop_cases:summary.desktop_cases,
  mobile_cases:summary.mobile_cases,
  failures:summary.failures,
  horizontal_overflow_failures:summary.horizontal_overflow_failures,
  console_or_page_error_cases:summary.console_or_page_error_cases,
  h1_visibility_failures:summary.h1_visibility_failures,
  hero_phone_visibility_failures:summary.hero_phone_visibility_failures,
  hero_detail_cta_visibility_failures:summary.hero_detail_cta_visibility_failures,
  hero_consult_cta_visibility_failures:summary.hero_consult_cta_visibility_failures
}));
if(failures) process.exit(1);
