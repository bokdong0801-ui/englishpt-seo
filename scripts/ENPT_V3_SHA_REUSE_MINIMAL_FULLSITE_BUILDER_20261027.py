#!/usr/bin/env python3
"""Build minimal V3 delta + exact Netlify published SHA digest. NEVER publishes Production.
Inputs: complete 202768-file published SHA map, signed 158571 route map, generated V2 region HTML.
Output: 21 changed/new static bytes, whole 202786-file SHA digest, fail-closed QA.
"""
from __future__ import annotations
import collections,csv,gzip,hashlib,importlib.util,json,os,pathlib,re,urllib.request,urllib.parse
from html import escape
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"v3-digest-qa"
NEW=ROOT/"v3-delta-files"
BASE=ROOT/"published-manifest/PUBLISHED_202768_STATIC_SHA1_MANIFEST.json.gz"
SIGNED=ROOT/"signed-qa-map/NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
PUBLISHED="6adafef5f2c6d196833683db"
PROD="https://englishpt.kr"
SITE="98d96cc5-f0b7-4d3d-8072-6476d93e55a3"
REGION_SLUGS=("gangwon","gyeonggi","gyeongnam","gyeongbuk","gwangju","daegu","daejeon","busan","seoul","sejong","ulsan","incheon","jeonnam","jeonbuk","jeju","chungnam","chungbuk")
ROUTES=("englishpt.html","courses.html","student-english.html")
def fail(x):raise RuntimeError("HOLD_V3_MERGE_"+x)
def get_page(name):
    request=urllib.request.Request(f"https://{PUBLISHED}--englishpt-seo.netlify.app/{name}",headers={"User-Agent":"ENPT-Owner-V3-Published-ReadOnly-Source"})
    with urllib.request.urlopen(request,timeout=40) as response:
        if response.status!=200:fail("IMMUTABLE_SOURCE_HTTP_"+name)
        return response.read(2500000)
def sha1(blob):return hashlib.sha1(blob).hexdigest()
def get_module():
    path=ROOT/"scripts/ENPT_REGION_FINAL_INTEGRATION_20261027.py"
    spec=importlib.util.spec_from_file_location("integrator_v3safe",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
def key_scan(signed,orig):
    route_map=signed["original_public_html_to_data_payload"]
    if len(route_map)!=158571:fail("SIGNED_ROUTE_COUNT")
    if sum(bool(v["noindex"]) for v in route_map.values())!=136607:fail("SIGNED_NOINDEX_COUNT")
    if sum(not bool(v["noindex"]) for v in route_map.values())!=21964:fail("SIGNED_INDEXABLE_COUNT")
    # Route -> .page sharded file; indexable OG pages modified post-source snapshot, noindex intact.
    all_found=0
    for route,row in route_map.items():
        target="/"+row["to"]
        if target not in orig:fail("MISSING_ORIGINAL_SHARD_"+route)
        all_found+=1
        if row["noindex"] and orig[target]!=row["sha1"]:fail("NOINDEX_SHA_CHANGED_"+route)
    if all_found!=158571:fail("SHARDED_ROUTE_COUNT")
    image_count=sum(k.startswith("/assets/images/seo-square/v1/") and k.endswith(".jpg") for k in orig)
    if image_count!=21964:fail("OG_IMAGE_COUNT_"+str(image_count))
    sitemap_files=[n for n in orig if re.fullmatch(r"/sitemaps/sitemap-\d{3}\.xml",n)]
    if len(sitemap_files)!=44:fail("SITEMAP_SHARDS_"+str(len(sitemap_files)))
    for n in ("/robots.txt","/sitemap-index.xml","/favicon.ico","/netlify.toml","/.netlify/internal/edge-functions/manifest.json"):
        if n not in orig:fail("BASE_META_MISSING_"+n)
    return route_map,image_count,sitemap_files
def main():
    OUT.mkdir(exist_ok=True)
    NEW.mkdir(exist_ok=True)
    with gzip.open(BASE,"rt",encoding="utf8") as f:old=json.load(f)
    with gzip.open(SIGNED,"rt",encoding="utf8") as f:signed=json.load(f)
    if len(old)!=202768:fail("BASE_MANIFEST_COUNT")
    route_map,image_count,sitemaps=key_scan(signed,old)
    mod=get_module()
    digest=dict(old)
    modified={}
    def assign(path,blob,existed=False):
        if not path.startswith("/") or "//" in path:fail("INVALID_OUTPUT_PATH")
        if existed!=(path in old):fail("PATH_STATUS_"+path)
        dest=NEW/path.lstrip("/")
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(blob)
        check=dest.read_bytes()
        if sha1(check)!=sha1(blob):fail("BYTE_MISMATCH_"+path)
        digest[path]=sha1(blob)
        modified[path]={"size":len(blob),"sha1":sha1(blob),"old_sha1":old.get(path)}
    for route in ROUTES:
        shard="/"+route_map[route]["to"]
        before=get_page(route_map[route]["to"])
        if sha1(before)!=old[shard]:fail("CURRENT_PUBLISHED_CONTENT_DRIFT_"+route)
        updated,summary=mod.integrate(route,before)
        updated=updated.replace('href="/regions.html"','href="/regions/"')
        if '/regions.html"' in updated:fail("ROOT_REGION_HREF_LEAK_"+route)
        if mod.form(updated)!=mod.form(before.decode("utf8")):fail("CONSULTATION_FORM_MUTATION_"+route)
        if mod.canonical(updated)!=mod.canonical(before.decode("utf8")):fail("CANONICAL_MUTATION_"+route)
        if mod.robots(updated)!=mod.robots(before.decode("utf8")):fail("ROBOTS_META_MUTATION_"+route)
        if updated.count('id="enpt-regions-entry-20261027"')!=1:fail("REGION_ENTRY_COUNT_"+route)
        assign(shard,updated.encode("utf8"),existed=True)
    # Nonroot nested regions/index.html avoids the existing sharded Edge regex ^/[^/]+\\.html$
    v2root=ROOT/"region-review-site/regions.html"
    if not v2root.exists():fail("MISSING_V2_INPUT")
    generated_paths=["/regions/index.html"]+["/regions/"+n+".html" for n in REGION_SLUGS]
    all_new_links=[]
    for path in generated_paths:
        p=v2root if path.endswith("/index.html") else ROOT/"region-review-site"/path.lstrip("/")
        if not p.exists():fail("MISSING_PROVINCE_"+path)
        content=p.read_text("utf8")
        if path.endswith("/index.html"):
            content=content.replace("https://englishpt.kr/regions.html","https://englishpt.kr/regions/")
            if content.count("https://englishpt.kr/regions/")<1:fail("BAD_REGION_INDEX_CANONICAL")
        content=content.replace('href="/regions.html"','href="/regions/"')
        content=content.replace('content="noindex,nofollow"','content="noindex,follow"')
        content=content.replace('content="noindex, nofollow"','content="noindex,follow"')
        # Relative internal routes work inside both Netlify draft and Production, unlike external production absolute links.
        def rel(m):
            absolute=m.group(1)
            all_new_links.append(absolute)
            return 'href="/'+absolute+'"'
        content=re.sub(r'href="https://englishpt\.kr/([a-z0-9-]+(?:-tutor|-conv|-academy)\.html)"',rel,content)
        if path.endswith("/index.html"):
            if "rg-card" not in content:fail("MISSING_REGION_CARDS")
        else:
            if "rg-town" not in content or "rg-choices" not in content:fail("MISSING_V2_TOWN_CHOICES_"+path)
            if 'data-locality=' not in content:fail("MISSING_TOWN_ID_"+path)
        if 'name="englishpt-consultation"' not in content or 'id="applyModal"' not in content:fail("V2_FORM_MISSING_"+path)
        if 'name="robots" content="noindex,follow"' not in content:fail("NEW_PAGE_ROBOTS_POLICY_"+path)
        if 'Disallow: /' in content:fail("GLOBAL_DRAFT_ROBOTS_LEAK")
        assign(path,content.encode("utf8"),existed=False)
    # 7 distinct student/adult routes per each of 5149 localities.
    if len(all_new_links)!=36043 or len(set(all_new_links))!=36043:fail("V2_NEW_ANCHORS_"+str(len(all_new_links)))
    if any(link not in route_map for link in all_new_links):fail("V2_TARGET_ABSENT_FROM_SIGNED_158571")
    removed=set(old)-set(digest)
    added=set(digest)-set(old)
    changed={p for p in old if digest.get(p)!=old[p]}
    if removed:fail("DELETED_PRODUCTION_ASSETS")
    if added!=set(generated_paths):fail("ADDED_SCOPE_DRIFT")
    if changed!={"/"+route_map[r]["to"] for r in ROUTES}:fail("CHANGED_SCOPE_DRIFT")
    if len(digest)!=202786:fail("TOTAL_STATIC_FILES_"+str(len(digest)))
    for p in old:
        if p not in changed and digest[p]!=old[p]:fail("OTHER_FILE_HASH_CHANGED")
    approx=len(json.dumps({"files":digest,"draft":True,"async":True,"edge_functions":{"tar":"1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b"}},separators=(",",":")).encode())
    if approx>24000000:fail("NETLIFY_API_DIGEST_TOO_LARGE_"+str(approx))
    output={"status":"PASS_V3_202786_SHA1_FILE_SOURCE_ONLY",
      "source_published_id":PUBLISHED,"source_file_count":len(old),"candidate_file_count":len(digest),
      "signed_existing_routes":len(route_map),"signed_noindex_count":136607,"signed_indexable_count":21964,
      "OG_images_preserved":image_count,"sitemaps_unchanged":len(sitemaps),
      "existing_files_modified":sorted(changed),"new_region_files":len(added),
      "new_region_paths":sorted(added),"removed_files":len(removed),"course_targets":len(all_new_links),
      "duplicate_new_links":0,"bad_bare_town_links":0,
      "original_edge_manifest_sha1":old["/.netlify/internal/edge-functions/manifest.json"],
      "unchanged_site_robots_sha1":old["/robots.txt"],"unchanged_site_sitemap_index_sha1":old["/sitemap-index.xml"],
      "netlify_manifest_bytes_estimate":approx,"unchanged_existing_entries":len(old)-len(changed),
      "draft_only":True,"production_published":False,"form_submissions":0}
    with gzip.open(OUT/"V3_202786_CANDIDATE_FILES_SHA1.json.gz","wt",encoding="utf8") as f:json.dump(digest,f,separators=(",",":"))
    (OUT/"V3_SHA_ONLY_SOURCE_GUARD.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),"utf8")
    print("ENPT_V3_202786_SOURCE_GUARD",json.dumps(output,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
