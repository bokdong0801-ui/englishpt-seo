#!/usr/bin/env python3
# coding: utf-8
"""Mutate only a LOCAL extracted copy of last approved 180800-member ENPT site for Draft.
21,964 indexable OG changes + 21,964 preverified square JPEG; all noindex routes immutable.
Never call Netlify or GitHub from this file.
"""
import csv,gzip,hashlib,html,json,pathlib,re,shutil,sys,time
from collections import Counter

ROOT=pathlib.Path(__file__).resolve().parents[1]
SITE=ROOT/"thumb-21964-candidate"
MAPPING=ROOT/"signed-route-map"/"ALL_21964_INDEXABLE_THUMBNAIL_MAP.csv"
PROOF=ROOT/"all-jpeg-qa"/"ALL21964_IMAGE_HASH_AND_URL.csv"
SIGNED=ROOT/"signed-qa-map"/"NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
PICS=ROOT/"existing-jpegs"/"full-jpg"
OUTPUT=ROOT/"thumb-draft-qa"
OUTPUT.mkdir(exist_ok=True)
EXPECTED_ARCHIVE_SHA="6d0272d1601a1a47abeccc4d740359af9e7678293ee0a3d257eecd2ca478d884"
TARGET="https://englishpt.kr"
IMAGE_META=re.compile(r'<meta\b(?=[^>]*(?:property|name)\s*=\s*["\x27](?:og:image(?:[:][-\w]+)?|twitter:image(?:[:][-\w]+)?|twitter:card)["\x27])[^>]*>',re.I)
HEAD=re.compile(r"<head\b[^>]*>(.*?)</head\s*>",re.I|re.S)
ROBOTS=re.compile(r'<meta\b[^>]*name=["\x27]robots["\x27][^>]*>',re.I)
CANONICAL=re.compile(r'<link\b[^>]*rel=["\x27]canonical["\x27][^>]*>',re.I)
def sha1(b):return hashlib.sha1(b).hexdigest()
def sha256(b):return hashlib.sha256(b).hexdigest()
def assertion(flag,msg):
 if not flag:raise ValueError(msg)
def readcsv(p):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def patch_img(blob,row):
 src=blob.decode("utf8")
 match=HEAD.search(src)
 assertion(bool(match),"HEAD not found "+row["route"])
 head=match.group(1)
 before_robot=ROBOTS.search(head)
 before_can=CANONICAL.search(head)
 assertion(bool(before_robot),"Missing robots meta "+row["route"])
 assertion(bool(before_can),"Missing canonical "+row["route"])
 url=row["planned_og_image_url"]
 assertion(url==TARGET+"/"+row["planned_image_path"],"Image host mismatch")
 label=html.escape(row["header_label"]+" "+row["search_keyword"],quote=True)
 payload=(
  '<meta property="og:image" content="'+url+'">'
  '<meta property="og:image:secure_url" content="'+url+'">'
  '<meta property="og:image:type" content="image/jpeg">'
  '<meta property="og:image:width" content="1200">'
  '<meta property="og:image:height" content="1200">'
  '<meta property="og:image:alt" content="'+label+'">'
  '<meta name="twitter:card" content="summary">'
  '<meta name="twitter:image" content="'+url+'">'
 )
 new_head=IMAGE_META.sub("",head)+payload
 assertion(ROBOTS.search(new_head).group(0)==before_robot.group(0),"Robots changed "+row["route"])
 assertion(CANONICAL.search(new_head).group(0)==before_can.group(0),"Canonical changed "+row["route"])
 for tag in ('property="og:image"','property="og:image:width"','property="og:image:height"','name="twitter:image"'):
  assertion(new_head.count(tag)==1,"Duplicate metadata "+tag+" "+row["route"])
 return (src[:match.start(1)]+new_head+src[match.end(1):]).encode("utf8")
if not (SITE.is_dir() and PICS.is_dir() and MAPPING.is_file() and SIGNED.is_file() and PROOF.is_file()):
 raise SystemExit("HOLD required original source or signed image map files missing")
rows=readcsv(MAPPING)
assertion(len(rows)==21964 and all(r["mapping_status"]=="READY_METADATA_ONLY" and r["indexable"]=="TRUE" for r in rows),
 "Image source 21964 indexable mapping guard")
hashrows=readcsv(PROOF)
hash_by_route={x["url_path"]:x for x in hashrows}
assertion(len(hash_by_route)==21964,"Full SHA256 image evidence missing")
with gzip.open(SIGNED,"rt",encoding="utf8") as f:signed=json.load(f)
source=signed["original_public_html_to_data_payload"]
assertion(len(source)==158571 and sum(not x["noindex"] for x in source.values())==21964,"Original site source index count")
indexed={k for k,v in source.items() if not v["noindex"]}
assertion({x["route"] for x in rows}==indexed,"Full mapping must exactly equal SEO indexable route set")
assertion(sum(x["noindex"] for x in source.values())==136607,"noindex partition mismatch")
# Check source original other than to-be-changed images is intact and untouched. Do not touch noindex.
start=time.monotonic()
for i,row in enumerate(rows,1):
 route=row["route"]
 orig=source[route]
 source_rel=row["source_edge_path"]
 assertion(source_rel==orig["to"] and row["source_page_sha1"]==orig["sha1"],
  "Preflight Edge routing parity "+route)
 src=SITE/source_rel
 b=src.read_bytes()
 assertion(sha1(b)==orig["sha1"],"Original source file diverged "+route)
 img=PICS/(row["image_key"]+".jpg")
 irow=hash_by_route[route]
 assertion(img.is_file() and sha256(img.read_bytes())==irow["sha256"],"Verified image contents mismatch "+route)
 assertion(irow["image_path"]==row["planned_image_path"],"Verified image asset path mismatch "+route)
 patched=patch_img(b,row)
 assertion(patched!=b,"Image metadata unchanged unexpectedly "+route)
 src.write_bytes(patched)
 dest=SITE/row["planned_image_path"];dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(img,dest)
 if i%3500==0:print("ENPT_DRAFT_LOCAL_OG_PATCH_PROGRESS",i,len(rows),round(time.monotonic()-start,1),flush=True)
# Redirect root must display same branded image when shared as https://englishpt.kr/.
main=next(r for r in rows if r["route"]=="englishpt.html")
for rel in ("index.html",):
 fp=SITE/rel
 b=fp.read_bytes()
 new=patch_img(b,main)
 fp.write_bytes(new)
# Verify ALL excluded routes unchanged by source SHA; watch for dangerous noindex leaks.
checked=0
for route,ref in source.items():
 if ref["noindex"]:
  fp=SITE/ref["to"]
  if sha1(fp.read_bytes())!=ref["sha1"]:raise ValueError("NOINDEX CONTENT CHANGED "+route)
  checked+=1
assertion(checked==136607,"NOINDEX exact contents count mismatch")
checks={}
for file in ("robots.txt","sitemap-index.xml","_redirects","_headers","netlify.toml","netlify/edge-functions/shard-router.js"):
 path=SITE/file
 assert path.is_file()
 assert sha1(path.read_bytes())==signed["target_SHA1_by_path"][file], "Critical source changed "+file
 checks[file]="UNCHANGED_SHA1"
xmls=list((SITE/"sitemaps").glob("*.xml"))
assertion(len(xmls)==44,"44 sitemap shard count wrong")
for x in xmls:assertion(sha1(x.read_bytes())==signed["target_SHA1_by_path"]["sitemaps/"+x.name],"Sitemap unexpectedly changed")
for home in ("index.html","__pages/23/englishpt.page"):
 page=(SITE/home).read_bytes()
 assert page.count(b'meta name="naver-site-verification"')==1
 assert page.count(b'meta name="google-site-verification"')==1
assertion(len(list((SITE/"assets/images/seo-square/v1").glob("*.jpg")))==21964,"Actual site images all exist")
assertion(len(list((SITE/"__pages").glob("*/*.page")))==158571,"Actual preserved Edge pages count")
report={
 "status":"PASS_DRAFT_CANDIDATE_21964_REAL_OG_LINKS_ALL_NOIDX_PRESERVED",
 "indexable_image_tags_added_exactly_once":21964,
 "root_index_og_updated":True,
 "new_image_count":21964,
 "all_158571_SEO_urls_kept":len(source),
 "all_136607_noindex_edge_files_sha1_identical":checked,
 "actual_site_page_count":158571,
 "all_44_sitemap_shards_sha1_identical":44,
 "critical_file_sha1_checks":checks,
 "both_google_naver_owner_tags_preserved":True,
 "all_jpeg_images_verified_sha256_against_source":21964,
 "total_candidate_site_members_expected":180800+21964,
 "production_published":False,
 "netlify_draft_uploaded":False,
 "source_full_release_sha256":EXPECTED_ARCHIVE_SHA,
 "elapsed_sec":round(time.monotonic()-start,2),
 "notes":"Source folder is an offline prepared candidate. A separately guarded Netlify Draft is optional; no Production mutation allowed."
}
(OUTPUT/"CANDIDATE_21964_SOURCE_PRESERVATION_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("ENPT_CANDIDATE_21964_LOCAL_IMAGE_OG_QA",json.dumps(report,ensure_ascii=False),flush=True)
