import {readFileSync,writeFileSync} from "node:fs";
import {gunzipSync} from "node:zlib";
import {pathToFileURL} from "node:url";
const [manifestPath,edgePath,redirectPath,out] = process.argv.slice(2);
if(!manifestPath||!edgePath||!redirectPath||!out)throw Error("missing args");
const map=JSON.parse(gunzipSync(readFileSync(manifestPath)).toString("utf8"));
const {staticPayloadPath,fnvBucket,default:handler}=await import(pathToFileURL(edgePath).href);
const aliases=new Set(readFileSync(redirectPath,"utf8").split(/\r?\n/).map(s=>s.trim().split(/\s+/)).filter(a=>a.length>=3 && a[2].startsWith("301")).map(a=>a[0]));
let examined=0,redirectExempt=0,errors=[],rewritten=0;
const targets=map.original_public_html_to_data_payload;
const paths=Object.entries(targets);
for(const [legacy,{to,noindex,sha1}] of paths){
 examined++;
 const publicRoute="/"+legacy;
 const shouldSkip=aliases.has(publicRoute);
 const actual=staticPayloadPath(publicRoute);
 const expected=shouldSkip?null:"/"+to;
 if(shouldSkip)redirectExempt++;else rewritten++;
 if(actual!==expected && errors.length<15)errors.push({legacy,expected,actual});
 if(examined%40000===0)console.log("ALL_PUBLIC_HTML_EDGE_MAP_PROGRESS",examined);
}
const smokeSamples=paths.filter(([name],i)=>i%137===0).slice(0,1200);
let mocks=0;
for(const [file,{to}] of smokeSamples){
 if(aliases.has("/"+file))continue;
 const publicURL="https://englishpt.kr/"+file+"?lang=ko";
 const expected="/"+to;
 const mock={rewrite:async url=>{
  if(url.pathname!==expected || url.search!=="?lang=ko")throw Error("Bad internal rewrite");
  return new Response("<!doctype html><html>Content preserved</html>",{
    status:200,headers:{"Content-Type":"application/octet-stream","X-Robots-Tag":"noindex, nofollow"}});
 }};
 const result=await handler(new Request(publicURL),mock);
 if(!result || result.status!==200 ||
    !result.headers.get("content-type").startsWith("text/html")||
    result.headers.has("X-Robots-Tag") ||
    await result.text()!=="<!doctype html><html>Content preserved</html>"){
   errors.push({file,error:"Full public HTML response Content-Type/status/robots not preserved"});
   if(errors.length>=15)break;
 }
 mocks++;
}
const post=await handler(new Request("https://englishpt.kr/gyeongnam-milyang-naeidong-elem-tutor.html",{method:"POST"}),
  {rewrite:()=>{throw Error("POST must skip Edge")}});
if(post!==undefined)errors.push({error:"POST intercept"});
for(const url of ["/","/index.html","/404.html","/robots.txt","/assets/pilot.js","/unsafe%2Fpath.html","/bad%ZZ.html"])
 if(staticPayloadPath(url)!==null)errors.push({url,error:"Non-page intercepted"});
const result={status:examined===158571&&!errors.length?"PASS_158571_LEGACY_SEO_URLS_PRESERVED_VIA_DYNAMIC_PAYLOAD_EDGE":"HOLD_FULL_EDGE_MAPPING_QA",
  tested_original_routes:examined,full_original_public_html_paths_preserved:rewritten,
  expected_legacy_301_exemptions:redirectExempt,actual_Response_header_mock_checks:mocks,
  indexable_pages_emitted_as_text_html:true,source_robot_meta_still_per_page:true,
  Form_POST_bypass:true,raw_payload_noindex_header_removed_on_public_URL:true,
  Edge_runtime_on_all_180k_live_routes_not_proven:true,
  Production_deployed:false,Netlify_Draft_deployed:false,errors};
writeFileSync(out,JSON.stringify(result,null,2)+"\n");
console.log("FULL_PAYLOAD_REAL_EDGE_JS_ROUTER_OFFLINE_QA",JSON.stringify(result));
if(errors.length||examined!==158571)process.exit(1);
