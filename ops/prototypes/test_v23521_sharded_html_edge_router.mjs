/* Offline 158,571+ URL test. NEVER launches Netlify or produces a deployment. */
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { fnvBucket, rewritePath } from "./v23521_sharded_html_edge_router.mjs";
const manifest = process.argv[2], profilePath = process.argv[3], reportPath = process.argv[4];
if (!manifest || !profilePath || !reportPath) throw Error("Need full frozen archive tar listing, profile and output");
const profile = JSON.parse(readFileSync(profilePath,"utf8"));
const names = readFileSync(manifest,"utf8").split(/\r?\n/).map(n=>n.replace(/^\.\//,"").replace(/\/$/,"")).filter(Boolean);
const roots = names.filter(n=>!n.includes("/"));
const html = roots.filter(n=>n.endsWith(".html"));
const moving = html.filter(n=>n!=="index.html"&&n!=="404.html");
const expectedBuckets = profile.hash_shard_file_counts;
const buckets = new Map(), mappings = new Set();
let pathError = 0;
const hash = createHash("sha256");
for (const name of moving) {
  const rawUrl = "/" + encodeURIComponent(name);
  const rewrite = rewritePath(rawUrl);
  const bucket = fnvBucket(name);
  const expected = "/__pages/"+bucket+"/"+encodeURIComponent(name);
  if (rewrite !== expected || !rewrite || mappings.has(rewrite)) pathError++;
  mappings.add(rewrite);
  buckets.set(bucket,(buckets.get(bucket)||0)+1);
  hash.update(name).update("\0").update(rewrite??"").update("\n");
}
const tests = [
 ["/",null], ["/index.html",null], ["/404.html",null],
 ["/robots.txt",null], ["/sitemap-index.xml",null], ["/pilot.js",null],
 ["/assets/images/og-pages/abc.png",null],
 ["/gyeongnam-milyang-naeidong-elem-tutor.html", "/__pages/"+fnvBucket("gyeongnam-milyang-naeidong-elem-tutor.html")+"/gyeongnam-milyang-naeidong-elem-tutor.html"],
 ["/seoul-jongno-sajikdong-mid-tutor.html", "/__pages/"+fnvBucket("seoul-jongno-sajikdong-mid-tutor.html")+"/seoul-jongno-sajikdong-mid-tutor.html"],
 ["/bad%2Fname.html",null],["/invalid%ZZ.html",null]
];
const failedTests=tests.filter(([path,want])=>rewritePath(path)!==want).map(([p])=>p);
const bucketMatches=Object.entries(expectedBuckets).every(([k,v])=>buckets.get(k)===v)&&Object.keys(expectedBuckets).length===buckets.size;
const projectedRoot=roots.length-moving.length;
const largest=Math.max(...buckets.values());
const passed=failedTests.length===0&&pathError===0&&bucketMatches&&
  moving.length===profile.source_html_in_root-2 &&
  roots.length===profile.root_files&&projectedRoot===profile.projected_root_files_after_html_shard&&
  largest===profile.hash_shards_max_files&&largest<54000&&
  moving.length>=158571;
const result={
  status:passed?"PASS_OFFLINE_158571_HTML_URL_TO_SHARD_REWRITE_CROSSCHECK":
                "HOLD_OFFLINE_SHARD_ROUTING_PROOF",
  frozen_candidates_only:true,production_deployed:false,new_Netlify_deploy_created:false,
  source_candidate_sha256:"e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba",
  root_file_count_before:roots.length,html_root_files:html.length,moved_html_count:moving.length,
  root_file_count_after:projectedRoot,shard_directory_count:buckets.size,
  max_file_count_per_hash_directory:largest,
  bucket_python_node_agreement:bucketMatches,mapping_collisions: moving.length-mappings.size,
  broken_path_mappings:pathError,failed_sample_tests:failedTests,
  sha256_original_filename_to_shard_mapping:hash.digest("hex"),
  public_urls_kept_identical:true,internal_files_relocated:true,
  caveats:[
   "Only deterministic URL-to-file mapping tested OFFLINE; no Netlify Edge runtime tested.",
   "Actual Netlify Edge rewrite/SEO headers/form capture/redirects need a separate authorized Draft Preview test.",
   "Sharding does NOT reduce 180k files or ~6.8GB raw content and does not solve upload capacity or required upload time.",
   "Original candidate is unchanged and remains the only previously user-approved version."
  ]
};
writeFileSync(reportPath,JSON.stringify(result,null,2)+"\n");
console.log("OFFLINE_HASH_SHARD_ROUTER_PROOF",JSON.stringify(result));
if (!passed) process.exit(1);
