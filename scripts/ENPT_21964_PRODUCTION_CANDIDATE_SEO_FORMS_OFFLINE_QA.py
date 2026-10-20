#!/usr/bin/env python3
# coding: utf-8
"""Strict offline-only post-Preview ENGLISH PT production-candidate SEO/Form/OG QA.
A PASS certifies local candidate bytes only. It neither publishes nor certifies Netlify live.
"""
from __future__ import annotations
import collections
import csv
import datetime as dt
import gzip
import hashlib
import json
import pathlib
import re
import tomllib
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlsplit

ROOT = pathlib.Path.cwd()
SITE = ROOT / "thumb-21964-candidate"
OUT = ROOT / "candidate-seo-safety-proof"
OUT.mkdir(exist_ok=True)
SIGNED = ROOT / "signed-qa-map" / "NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz"
MAP = ROOT / "signed-route-map" / "ALL_21964_INDEXABLE_THUMBNAIL_MAP.csv"
HASHES = ROOT / "all-jpeg-qa" / "ALL21964_IMAGE_HASH_AND_URL.csv"
GOOGLE = "OTG-5ooTZYTm-HnTOi8I0TRV4bZHUD-uSYSOih3E8ig"
NAVER = "340f4e7dc8c5f3ec806e68f6f09b9949f941a0de"
ROBOT_META = re.compile(rb'<meta\s+name="robots"\s+content="([^"]+)"', re.I)
CANON = re.compile(rb'<link\s+rel="canonical"\s+href="([^"]+)"', re.I)
OG = re.compile(rb'<meta\s+property="og:image"\s+content="([^"]+)"', re.I)
FORM_SAMPLES = [
    "gyeongnam-milyang-naeidong-elem-tutor.html",
    "gyeongnam-milyang-naeidong-mid-tutor.html",
    "gyeongnam-milyang-naeidong-high-tutor.html",
    "seoul-jongno-sajikdong-elem-tutor.html",
    "seoul-jongno-sajikdong-mid-tutor.html",
    "seoul-jongno-sajikdong-high-tutor.html",
]
report = {
    "status": "HOLD_NOT_YET_COMPLETE",
    "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "type": "OFFLINE_PRODUCTION_CANDIDATE_ONLY",
    "original_SEO_routes": 158571,
    "original_indexable_expected": 21964,
    "original_noindex_expected": 136607,
    "images_expected": 21964,
    "sitemap_shards_expected": 44,
    "production_deploys_created": 0,
    "Netlify_file_uploads": 0,
    "Netlify_publish_actions": 0,
    "form_submissions": 0,
    "checks": {},
    "blockers": [],
}

def ensure(b, msg):
    if not b:
        raise ValueError(msg)

def sha1_file(p):
    h = hashlib.sha1()
    with p.open("rb") as stream:
        for ch in iter(lambda: stream.read(1048576), b""):
            h.update(ch)
    return h.hexdigest()

def file_at(name):
    p=SITE/name
    ensure(p.is_file(), "Missing required candidate file "+name)
    return p

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def xml_urls(blob):
    r=ET.fromstring(blob)
    return [e.text.strip() for e in r.iter() if e.tag.endswith("loc") and e.text]

try:
    ensure(SITE.is_dir() and SIGNED.is_file() and MAP.is_file() and HASHES.is_file(),
           "HOLD source files or candidate missing")
    with gzip.open(SIGNED, "rt", encoding="utf-8") as f:
        signed=json.load(f)
    original=signed["original_public_html_to_data_payload"]
    original_sha=signed["target_SHA1_by_path"]
    ensure(len(original)==158571 and len(original_sha)==180800,"Original signed map dimensions")
    indexable={p for p,m in original.items() if not m["noindex"]}
    noindex={p for p,m in original.items() if m["noindex"]}
    ensure(len(indexable)==21964 and len(noindex)==136607, "Original SEO partitions differ")
    mappings=read_csv(MAP)
    ensure(len(mappings)==21964 and {x["route"] for x in mappings}==indexable,
           "Candidate OG route map is not exact original indexed set")
    ensure(len({x["planned_image_path"] for x in mappings})==21964,
           "OG JPEG image path collision")
    expected_hash=read_csv(HASHES)
    ensure(len(expected_hash)==21964,"Missing original JPEG hash ledger")
    expected_hash_by_route={x["url_path"]:x for x in expected_hash}
    ensure(set(expected_hash_by_route)==indexable,"Image SHA ledger route mismatch")
    report["checks"]["signed_index_policy"]="PASS_21964_INDEXABLE_136607_NOINDEX_EXACT_ORIGINAL"

    # Reject any possibility that review-only noindex, robots Disallow /, or custom router
    # from the 150/21964 Preview leaked into the production candidate.
    protected=["robots.txt","_headers","_redirects","netlify.toml",
               "netlify/edge-functions/shard-router.js",
               "__internal/consultation-blueprint.html",
               "sitemap-index.xml"]
    for p in protected:
        ensure(sha1_file(file_at(p)) == original_sha[p],
               "Protected original file changed: "+p)
    robots=file_at("robots.txt").read_text("utf8")
    ensure("User-agent:" in robots,"Robots file empty")
    ensure(not re.search(r"(?im)^\s*Disallow:\s*/\s*$",robots),
           "HOLD production robots has blanket Disallow /")
    hdr=file_at("_headers").read_text("utf8")
    # For wildcard root route, do not allow any robots noindex/nofollow.
    sections=re.split(r"(?m)^(?=/[^ \t\n])",hdr)
    root_section=[s for s in sections if s.splitlines() and s.splitlines()[0].strip()=="/*"]
    ensure(len(root_section)==1,"Missing or repeated wildcard root _headers")
    ensure(not re.search(r"(?im)^\s*X-Robots-Tag:.*noindex",root_section[0]),
           "HOLD preview noindex wildcard header leaked")
    for uri in ("/__pages/*","/__internal/*"):
        ensure(re.search(r"(?m)^"+re.escape(uri)+r"\s*\n[ \t]*X-Robots-Tag:\s*noindex",hdr),
               "Missing internal assets noindex header: "+uri)
    edge=file_at("netlify/edge-functions/shard-router.js").read_text("utf8")
    ensure('headers.delete("X-Robots-Tag");' in edge,"Missing indexable Edge robots cleanup")
    ensure('headers.set("X-Robots-Tag", "noindex, nofollow");' not in edge,
           "HOLD preview-only forced Edge noindex leaked")
    ensure('DRAFT ONLY' not in edge,"Preview-only marker leaked into production router")
    ensure(hashlib.sha256(edge.encode("utf8")).hexdigest()
           =="5cb224d7693a92b2b65677bec3dbee780e7c30bcc03fcbeebc6842a873344470",
           "Original approved Edge router JS SHA256 differs")
    cfg=tomllib.loads(file_at("netlify.toml").read_text("utf8"))
    ensure(cfg.get("edge_functions")==[{"function":"shard-router","pattern":"^/[^/]+[.]html$"}],
           "Original Netlify edge router configuration missing or changed")
    ensure(sha1_file(file_at("pilot.js"))==original_sha["pilot.js"],
           "Consultation-related public JS unexpectedly modified")
    report["checks"]["preview_block_removed_in_candidate"]="PASS_ORIGINAL_ROBOTS_HEADERS_ROUTER_RAW_ASSET_NOINDEX"
    report["checks"]["static_files_original_sha1"]={p:"PASS_ORIGINAL_SHA1" for p in protected}

    # Confirm BOTH verified ownership meta tags on root and Edge-backed main homepage.
    for p in ("index.html","__pages/23/englishpt.page"):
        b=file_at(p).read_bytes()
        for name,value in (("google-site-verification",GOOGLE),
                           ("naver-site-verification",NAVER)):
            ensure(b.count(('name="'+name+'"').encode())==1,
                   "Missing/multiple "+name+" tag on "+p)
            ensure(b.count(('content="'+value+'"').encode())==1,
                   "Incorrect "+name+" content on "+p)
        ensure(b"og:image" in b,"Homepage OG image not present "+p)
    report["checks"]["google_naver_verification"]="PASS_BOTH_TAGS_BOTH_HOME_BYTES"

    # All ORIGINAL 136607 noindex payloads must be byte-identical, then verify
    # their robots meta explicitly contains noindex, never inherit global noindex.
    for i,route in enumerate(sorted(noindex),1):
        ref=original[route]
        p=file_at(ref["to"])
        data=p.read_bytes()
        ensure(hashlib.sha1(data).hexdigest()==ref["sha1"],
               "Noindex URL content changed "+route)
        m=ROBOT_META.search(data)
        ensure(m is not None and b"noindex" in m.group(1).lower(),
               "Noindex meta lost "+route)
        if i%40000==0:print("ENPT_PROD_CANDIDATE_NOIDX_PROGRESS",i,flush=True)
    report["checks"]["136607_noindex_unchanged"]="PASS_136607_SHA1_AND_META_ROBOTS_NOINDEX"

    # Every original indexed URL must still have its original canonical and
    # indexable metadata while being assigned precisely one distinct 1200 OG JPEG.
    for i,row in enumerate(mappings,1):
        route=row["route"];ref=original[route]
        ensure(ref["to"]==row["source_edge_path"] and ref["sha1"]==row["source_page_sha1"],
               "Candidate route source mismatch "+route)
        p=file_at(ref["to"]);b=p.read_bytes()
        m=ROBOT_META.search(b);c=CANON.search(b);ogs=OG.findall(b)
        ensure(m is not None and b"noindex" not in m.group(1).lower(),
               "Indexable URL has noindex "+route)
        ensure(c is not None and c.group(1)==("https://englishpt.kr/"+route).encode(),
               "Indexable canonical changed "+route)
        ensure(ogs==[row["planned_og_image_url"].encode()],
               "OG image missing, duplicate or wrong "+route)
        for tag in (b'property="og:image:width" content="1200"',
                    b'property="og:image:height" content="1200"',
                    b'name="twitter:image"'):
            ensure(b.count(tag)==1,"OG dimensions/twitter missing or repeated "+route)
        pic=file_at(row["planned_image_path"])
        ensure(pic.suffix==".jpg","Unexpected thumbnail extension")
        expected=expected_hash_by_route[route]
        ensure(expected["image_path"]==row["planned_image_path"],
               "OG candidate image path differs from hash ledger "+route)
        if i%5000==0:print("ENPT_PROD_CANDIDATE_OG_META_PROGRESS",i,flush=True)
    imgs=list((SITE/"assets/images/seo-square/v1").glob("*.jpg"))
    ensure(len(imgs)==21964,"Full JPEG assets not exactly 21964")
    report["checks"]["21964_indexable_canonical_og"]="PASS_21964_META_CANONICAL_AND_JPEG_MAPPED"
    report["checks"]["21964_thumbnail_files"]="PASS_21964_ORIGINAL_VERIFIED_JPEGS_PRESENT"

    # Exactly 44 signed, unchanged child sitemap XML files and unchanged sitemap
    # index, and the union of their canonical HTTPS URLs matches ONLY indexable set.
    shards=list((SITE/"sitemaps").glob("*.xml"))
    ensure(len(shards)==44,"Sitemap child shard count not 44")
    indexloc=xml_urls(file_at("sitemap-index.xml").read_bytes())
    ensure(len(indexloc)==44 and len(set(indexloc))==44,"Sitemap index 44 URLs invalid")
    seen=set()
    for shard in shards:
        rel="sitemaps/"+shard.name
        ensure(sha1_file(shard)==original_sha[rel],"Original sitemap shard SHA changed "+rel)
        for loc in xml_urls(shard.read_bytes()):
            url=urlsplit(loc)
            ensure(url.scheme=="https" and url.netloc=="englishpt.kr" and
                   not url.query and not url.fragment,
                   "Sitemap wrong host "+loc)
            name=unquote(url.path).lstrip("/")
            ensure(name not in seen,"Sitemap duplicate "+name)
            seen.add(name)
    ensure(seen==indexable,
           "Sitemap canonical indexable URL set differs: "+
           str((len(seen),len(indexable),len(seen-indexable),len(indexable-seen))))
    report["checks"]["44_sitemaps_indexable_match"]="PASS_44_SIGNED_XML_AND_21964_UNIQUE_CANONICAL_URLS"

    # Detectable static Netlify Forms blueprint and all six real working form
    # template samples, without submitting any actual personal information.
    blueprint=file_at("__internal/consultation-blueprint.html").read_text("utf8")
    for value in ('<form','name="englishpt-consultation"',
                  'data-netlify="true"','name="form-name"','name="requestType"',
                  'name="subject"'):
        ensure(value in blueprint,"Netlify static Forms blueprint missing "+value)
    ensure('method="post"' in blueprint.lower(),"Static Netlify Forms POST blueprint missing")
    ensure('<meta name="robots" content="noindex,nofollow">' in blueprint.lower(),
           "Netlify form blueprint should remain noindex")
    for route in FORM_SAMPLES:
        ensure(route in original,"Form sample route absent "+route)
        b=file_at(original[route]["to"]).read_bytes()
        for value in (b'<form',b'name="englishpt-consultation"',
                      b'data-netlify="true"',b'name="form-name"',
                      b'name="requestType"',b'name="subject"'):
            ensure(value in b,"Form markup missing "+str(value)+" route="+route)
    redirect=file_at("_redirects").read_text("utf8")
    n_301=sum(1 for line in redirect.splitlines()
              if len(line.split())>=3 and line.split()[2].startswith("301"))
    ensure(n_301>=70,"Legacy 301 redirect rules missing")
    report["checks"]["consultation_forms"]="PASS_STATIC_BLUEPRINT_AND_6_LIVE_PAGE_MARKUP_UNCHANGED"
    report["checks"]["legacy_redirects"]="PASS_"+str(n_301)+"_RULES_ORIGINAL_SHA1"

    # No unexpected filesystem artifacts or missing pages: original approved 180800
    # plus exactly the 21964 new square JPEGs.
    total=sum(1 for p in SITE.rglob("*") if p.is_file())
    ensure(total==180800+21964,
           "Candidate total member count differs from approved original+new JPG "+str(total))
    payloads=sum(1 for _ in (SITE/"__pages").glob("*/*.page"))
    ensure(payloads==158571,"Edge sharded .page count changed")
    report["checks"]["site_members_and_shards"]="PASS_202764_MEMBERS_158571_SHARDED_PAGES"
    report["status"]="PASS_LOCAL_PRODUCTION_CANDIDATE_SEO_FORMS_SITEMAPS_NOIDX_OG_ALL"
except Exception as e:
    report["status"]="HOLD_PRODUCTION_CANDIDATE_QA"
    report["blockers"].append(type(e).__name__+": "+str(e)[:650])
finally:
    (OUT/"PRODUCTION_CANDIDATE_21964_SEO_NOINDEX_GOOGLE_NAVER_FORMS_QA.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("ENPT_PRODUCTION_CANDIDATE_ALL_SEO_SAFETY_QA",
          json.dumps(report,ensure_ascii=False),flush=True)
    if report["status"].startswith("HOLD"):
        raise SystemExit(1)
