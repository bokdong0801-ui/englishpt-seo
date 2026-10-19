import { readFileSync, writeFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { pathToFileURL } from "node:url";
const [file, redirects, bundle, dest] = process.argv.slice(2);
if (![file,redirects,bundle,dest].every(Boolean)) throw Error("Missing QA input");
const t=JSON.parse(gunzipSync(readFileSync(file)).toString("utf8"));
const {fnvBucket,rewritePath,default:handler}=await import(pathToFileURL(bundle).href);
const legacy = new Set(readFileSync(redirects,"utf8").split(/\r?\n/).map(s=>s.trim().split(/\s+/)).filter(x=>x.length>=3&&x[2].startsWith("301")).map(x=>x[0]));
let seen=0,errors=[],numExcluded=0,numRewritten=0;
for(const [original, {to,sha1,size}] of Object.entries(t.original_to_new)){
 if (!original.endsWith(".html")||!to.startsWith("__pages/")) continue;
 seen++;
 const publicPath="/"+original;
 const shouldExclude=legacy.has(publicPath);
 const expected=shouldExclude?null:"/"+to;
 const actual=rewritePath(publicPath);
 if(actual!==expected&&errors.length<50)errors.push({original,actual,expected});
 if(shouldExclude)numExcluded++;else numRewritten++;
 const request={url:"https://englishpt.kr"+publicPath+"?utm_source=qa",method:"GET"};
 const result=handler(request);
 if(shouldExclude && result!==undefined && errors.length<50)errors.push({original,"error":"301_alias_not_bypassed"});
 if(!shouldExclude&&result?.pathname!==expected&&errors.length<50)errors.push({original,"error":"actual handler wrong URL rewrite"});
 if(!shouldExclude&&result?.search!=="?utm_source=qa"&&errors.length<50)errors.push({original,"error":"query lost"});
}
const samples=["/","/index.html","/404.html","/sitemap-index.xml","/pilot.js","/foo/bar.html","/foo%2Fbar.html","/bad%ZZ.html"];
for(const sample of samples)if(rewritePath(sample)!==null)errors.push({sample,error:"unsafe route unexpectedly matches"});
for(const m of ["POST","PUT","DELETE"]){
 let result=handler({url:"https://englishpt.kr/gyeongnam-milyang-naeidong-elem-tutor.html",method:m});
 if(result!==undefined)errors.push({method:m,error:"write-like HTTP method intercepted"});
}
const result={status:seen===158571&&errors.length===0?"PASS_ACTUAL_EDGE_BUNDLE_158571_ROOT_SEO_URLS_AND_301_ALIASES":"HOLD_ACTUAL_EDGE_BUNDLE_URL_REGRESSION",
 original_source_sha256:t.source_sha256,processed_root_urls:seen,
 valid_rewritten_urls:numRewritten,legacy_301_redirect_exemptions:numExcluded,legacy_redirect_count:legacy.size,
 errors,external_website_urls_unchanged:true,no_lost_query_params:true,
 forms_POST_bypass:true,edge_unit_test_only:true,netlify_edge_runtime_verified:false,
 created_or_published_deploy:false};
writeFileSync(dest,JSON.stringify(result,null,2)+"\n");
console.log("ACTUAL_SHARDED_EDGE_FULL_ROUTE_QA",JSON.stringify(result));
if(errors.length||seen!==158571)process.exit(1);
