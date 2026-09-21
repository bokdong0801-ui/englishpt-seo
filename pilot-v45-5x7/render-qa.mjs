import { chromium } from 'playwright';
import fs from 'node:fs';

const manifest = JSON.parse(fs.readFileSync('pilot-v45-5x7/PILOT_5X7_MANIFEST_V1.json','utf8'));
const browser = await chromium.launch({headless:true});
const viewports = [
  {name:'desktop', width:1440, height:1000},
  {name:'mobile', width:390, height:844}
];
const results = [];
let failures = 0;

for (const item of manifest.files) {
  const file = item.path.split('/').pop();
  for (const vp of viewports) {
    const context = await browser.newContext({viewport:{width:vp.width,height:vp.height}});
    const page = await context.newPage();
    const errors = [];
    page.on('console', msg => { if (msg.type()==='error') errors.push('console:'+msg.text()); });
    page.on('pageerror', err => errors.push('pageerror:'+err.message));
    const url = 'http://127.0.0.1:8000/pilot-v45-5x7/' + encodeURIComponent(file);
    let navError = null;
    try { await page.goto(url,{waitUntil:'networkidle',timeout:30000}); } catch(e) { navError=e.message; }
    const metrics = navError ? null : await page.evaluate(() => ({
      h1Count: document.querySelectorAll('h1').length,
      h1: document.querySelector('h1')?.textContent?.trim() || '',
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      phoneLinks: document.querySelectorAll('a[href="tel:+821050068027"]').length,
      robots: document.querySelector('meta[name="robots"]')?.getAttribute('content') || '',
      canonical: document.querySelector('link[rel="canonical"]')?.getAttribute('href') || ''
    }));
    const overflow = metrics ? metrics.scrollWidth > metrics.innerWidth + 1 : true;
    const expectedH1 = item.h1;
    const pass = !navError && errors.length===0 && !overflow && metrics.h1Count===1 &&
      metrics.h1===expectedH1 && metrics.phoneLinks>0 &&
      metrics.robots.toLowerCase().includes('noindex') &&
      metrics.canonical===item.canonical;
    if (!pass) failures++;
    results.push({file,viewport:vp.name,pass,navError,errors,overflow,metrics,expectedH1});
    await context.close();
  }
}
await browser.close();

const summary = {
  version:'1.0',
  page_count: manifest.files.length,
  render_cases: results.length,
  failures,
  desktop_cases: results.filter(x=>x.viewport==='desktop').length,
  mobile_cases: results.filter(x=>x.viewport==='mobile').length,
  horizontal_overflow_failures: results.filter(x=>x.overflow).length,
  console_or_page_error_cases: results.filter(x=>x.errors?.length).length,
  status: failures===0 ? 'PASS' : 'FAIL',
  production_deploy:false,
  results
};
fs.writeFileSync('pilot-v45-5x7/PILOT_5X7_RENDER_QA_V1.json', JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({status:summary.status,render_cases:summary.render_cases,failures:summary.failures,horizontal_overflow_failures:summary.horizontal_overflow_failures,console_or_page_error_cases:summary.console_or_page_error_cases}));
if (failures) process.exit(1);
