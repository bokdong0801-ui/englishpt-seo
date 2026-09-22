import { chromium } from 'playwright';
import fs from 'node:fs';

const root='stage3-production-dryrun-10x13';
const manifest=JSON.parse(fs.readFileSync(root+'/STAGE3_10X13_MANIFEST_V1.json','utf8'));
const outPath=root+'/STAGE3_10X13_RENDER_QA_V1.json';
const browser=await chromium.launch({headless:true});
const viewports=[{name:'desktop',width:1440,height:1000},{name:'mobile',width:390,height:844}];
const results=[];let failures=0;
for(const item of manifest.files){
 const file=item.path.split('/').pop();
 for(const vp of viewports){
  const context=await browser.newContext({viewport:{width:vp.width,height:vp.height}});
  const page=await context.newPage();const errors=[];
  page.on('console',m=>{if(m.type()==='error')errors.push('console:'+m.text())});
  page.on('pageerror',e=>errors.push('pageerror:'+e.message));
  let navError=null;
  try{await page.goto('http://127.0.0.1:8000/'+root+'/'+encodeURIComponent(file),{waitUntil:'domcontentloaded',timeout:10000});await page.waitForTimeout(20);}catch(e){navError=e.message}
  const metrics=navError?null:await page.evaluate(()=>{
   const vis=el=>{if(!el)return false;const s=getComputedStyle(el),r=el.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0&&r.width>0&&r.height>0};
   const h1=document.querySelector('h1'),phone=document.querySelector('.hero a[href="tel:+821050068027"]'),detail=document.querySelector('.hero a[href="#detail"]'),consult=document.querySelector('.hero a[href="#consultation-preview"]');
   return {h1Count:document.querySelectorAll('h1').length,h1:h1?.textContent?.trim()||'',h1Visible:vis(h1),scrollWidth:document.documentElement.scrollWidth,bodyScrollWidth:document.body.scrollWidth,innerWidth:innerWidth,phoneVisible:vis(phone),detailVisible:vis(detail),consultVisible:vis(consult),decisionStrip:!!document.querySelector('.decision-strip'),midCta:!!document.querySelector('.mid-cta'),robots:document.querySelector('meta[name="robots"]')?.content||'',canonical:document.querySelector('link[rel="canonical"]')?.href||'',bodyFlag:document.body?.dataset?.productionDeploy||'',bodyHeight:document.body?.scrollHeight||0};
  });
  const overflow=metrics?Math.max(metrics.scrollWidth,metrics.bodyScrollWidth)>metrics.innerWidth+1:true;
  const pass=!navError&&errors.length===0&&!overflow&&metrics.h1Count===1&&metrics.h1===item.h1&&metrics.h1Visible&&metrics.phoneVisible&&metrics.detailVisible&&metrics.consultVisible&&metrics.decisionStrip&&metrics.midCta&&metrics.robots.toLowerCase().includes('noindex')&&metrics.canonical===item.canonical&&metrics.bodyFlag==='false'&&metrics.bodyHeight>vp.height;
  if(!pass)failures++;
  results.push({file,intent:item.intent,locality:item.locality,viewport:vp.name,pass,navError,errors,overflow,metrics,expectedH1:item.h1});
  await context.close();
 }
}
await browser.close();
const summary={version:'1.0',status:failures===0?'PASS':'FAIL',page_count:manifest.files.length,render_cases:results.length,desktop_cases:results.filter(x=>x.viewport==='desktop').length,mobile_cases:results.filter(x=>x.viewport==='mobile').length,failures,horizontal_overflow_failures:results.filter(x=>x.overflow).length,console_or_page_error_cases:results.filter(x=>x.errors?.length).length,h1_visibility_failures:results.filter(x=>x.metrics&&!x.metrics.h1Visible).length,hero_phone_visibility_failures:results.filter(x=>x.metrics&&!x.metrics.phoneVisible).length,benchmark_block_failures:results.filter(x=>x.metrics&&(!x.metrics.decisionStrip||!x.metrics.midCta)).length,production_deploy:false,results};
fs.writeFileSync(outPath,JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({status:summary.status,render_cases:summary.render_cases,desktop_cases:summary.desktop_cases,mobile_cases:summary.mobile_cases,failures:summary.failures,horizontal_overflow_failures:summary.horizontal_overflow_failures,console_or_page_error_cases:summary.console_or_page_error_cases,benchmark_block_failures:summary.benchmark_block_failures}));
if(failures)process.exit(1);
