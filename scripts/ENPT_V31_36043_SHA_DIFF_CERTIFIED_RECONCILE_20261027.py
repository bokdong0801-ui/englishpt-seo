#!/usr/bin/env python3
"""Exact 36,043-route V3 -> V3.1 SHA delta attestation + legacy 57 retry + V3.1 live QA.
NO new 36k HTTP claim: separately identify legacy-live, unchanged SHA, and 7 fresh-live.
GET/POST free locally. Never publish; do not alter Netlify or SEO.
"""
from __future__ import annotations
import collections,csv,datetime,gzip,hashlib,json,pathlib
ROOT=pathlib.Path(".")
OUT=ROOT/"v31-final-reconciled-qa";OUT.mkdir(exist_ok=True)
GROUPS=("elem-tutor","elem-conv","mid-tutor","mid-conv","high-tutor","high-conv","worker-english-conv-academy")
PREFIX="gyeonggi-anyang-manan-byeongmokandong-"
SRC_V3="v3-reference"
SRC_V31="v31-reference"
SIGN="signed-qa-map"
LEGACY="v3-previous-live"
RETRY="v3-57-retest"
LIVE="v31-actual-browser"
SOURCE="v31-source-proof"
def unique(root,pattern):
    paths=list(pathlib.Path(root).rglob(pattern))
    if len(paths)!=1:raise RuntimeError(f"HOLD_EXPECT_ONE_{pattern}_FOUND_{len(paths)}_"+str(paths[:10]))
    return paths[0]
def gzjson(root,pattern):
    with gzip.open(unique(root,pattern),"rt",encoding="utf8") as f:return json.load(f)
def jfile(root,pattern):return json.loads(unique(root,pattern).read_text(encoding="utf8"))
v3=gzjson(SRC_V3,"V3_202786_CANDIDATE_FILES_SHA1.json.gz")
v31=gzjson(SRC_V31,"V3_1_202786_CANDIDATE_FILES_SHA1.json.gz")
routes=gzjson(SIGN,"NAVER_GOOGLE_TWO_HOME_NEW_SHA1_MAP.json.gz")["original_public_html_to_data_payload"]
qa=jfile(LIVE,"V31_FINAL_NONPUBLISHED_LIVE_QA.json")
patch=jfile(SOURCE,"V3_1_7_LOCALITY_CORRECTION_SOURCE_GUARD.json")
ret=jfile(RETRY,"RETRY_57_SUMMARY.json")
oldfile=None;old=None
for f in pathlib.Path(LEGACY).rglob("*.json"):
    try:z=json.loads(f.read_text("utf8"))
    except:continue
    if isinstance(z,dict) and z.get("total_checked")==36043:
        if old is not None:raise RuntimeError("HOLD_DUPLICATE_LEGACY_SUMMARY")
        oldfile=f;old=z
if old is None:raise RuntimeError("HOLD_NO_LEGACY_ALL_36043_EVIDENCE")
assert len(v3)==len(v31)==202786
assert len(routes)==158571
assert set(v3)==set(v31),"HOLD_DELETED_OR_ADDED_V31_FILE"
assert old["total_checked"]==36043 and old["http_200"]==35986
assert old["http_404"]==0 and old["missing_response"]==55
assert old["class_counts"]=={"HTTP_5XX":2,"NETWORK_ERROR":55,"PASS":35986},old["class_counts"]
assert ret["status"]=="PASS_ALL_57_REVERIFIED" and ret["total_retried"]==ret["recovered"]==57 and not ret.get("remaining")
assert patch["status"]=="PASS_V3_1_ONLY_7_LOCALITY_SHARDS_PATCHED"
assert patch["patched_html"]==7 and patch["total_paths"]==202786 and patch["source_existing_routes"]==158571
assert patch["original_sitemap_shards"]==44 and patch["changed_from_immutable_published"]==10
assert qa["status"]=="PASS_V31_7_REPAIRS_21_REGIONS_44_SITEMAPS_390_768_1440"
assert not qa["errors"] and qa["total_sitemap_urls"]==21964
assert qa["draft_id"]=="6ae06963f085b33a5ee903eb"
assert qa["published_id"]=="6adafef5f2c6d196833683db"
assert len(qa["browser"])==3 and {x["width"] for x in qa["browser"]}=={390,768,1440}
assert all(not x["js_errors"] and x["routes_attempted"]==28 for x in qa["browser"])
source_bytes=b"".join((ROOT/"stage5-input"/f"production_locality_rows_5149_v1.part{i:03d}.jsonl").read_bytes() for i in range(1,7))
assert hashlib.sha256(source_bytes).hexdigest()=="3fe392df02bf76e0a6f84ef220433f0b901f97ae09a0a091269deeb2eaf8e9f0"
towns=[json.loads(line) for line in source_bytes.decode("utf8").splitlines() if line.strip()]
assert len(towns)==5149 and len({r["region_slug"] for r in towns})==5149
change_paths={p for p in v3 if v3[p]!=v31[p]}
changed_expected={"/"+routes[PREFIX+x+".html"]["to"] for x in GROUPS}
assert change_paths==changed_expected,("HOLD_UNEXPECTED_MANIFEST_CHANGE",sorted(change_paths^changed_expected)[:20])
assert set(patch.get("changes",[]) and [r["shard"] for r in patch["changes"]])==changed_expected
bad_phrase_routes=set(PREFIX+x+".html" for x in GROUPS)
actual_live={r["path"] for r in qa["routes"] if r.get("repair")=="PASS" and r.get("status")==200}
assert actual_live==bad_phrase_routes,("HOLD_V31_FRESH_GET_SEVEN_NOT_ALL_VERIFIED",actual_live)
rows=[];counter=collections.Counter()
for town in towns:
    slug=town["region_slug"]
    for course in GROUPS:
        route=slug+"-"+course+".html"
        assert route in routes,("HOLD_ROUTE_MISSING_FROM_SIGNED_MAP",route)
        shard="/"+routes[route]["to"]
        assert shard in v3 and shard in v31,("HOLD_SHA_MISSING",route)
        changed=shard in change_paths
        if changed and route not in bad_phrase_routes:raise RuntimeError("HOLD_OTHER_COURSE_CHANGED_"+route)
        if route in bad_phrase_routes and not changed:raise RuntimeError("HOLD_V31_7_CORRECTIONS_NOT_IN_MANIFEST_"+route)
        cls="V31_CHANGED_AND_SEVEN_FRESH_HTTP_200_QA_PASS" if changed else "V31_BYTE_IDENTICAL_TO_PREVIOUS_FULL_LIVE_VERIFIED_V3"
        counter[cls]+=1
        rows.append({"route":route,"course":course,"region_slug":slug,"shard":shard,"v3_sha1":v3[shard],"v31_sha1":v31[shard],"changed_in_v31":int(changed),"evidence_class":cls,"legacy_http_verified_after_57_retries":True,"v31_new_http_checked":changed})
assert len(rows)==36043 and len({r["route"] for r in rows})==36043
assert counter["V31_BYTE_IDENTICAL_TO_PREVIOUS_FULL_LIVE_VERIFIED_V3"]==36036
assert counter["V31_CHANGED_AND_SEVEN_FRESH_HTTP_200_QA_PASS"]==7
unchanged_others=len(v3)-len(change_paths)
assert unchanged_others==202779
with (OUT/"V31_36043_COURSE_SHA_AND_QA_PROVENANCE.csv").open("w",newline="",encoding="utf-8-sig") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
report={
    "status":"PASS_V31_PREPUBLISH_SHA_DELTA_AND_ALL_36043_PROVENANCE",
    "important_limit":"NEW_36043_HTTP_RESCAN_CANCELLED_NO_OUTPUT; V3.1 inference uses historic 36043 live GET+57 retry, 36036 unchanged SHA, 7 fresh V3.1 live GET",
    "old_36043_source_run":40472038047,"old_57_retry_run":40474299205,
    "cancelled_new_36043_run":40477418898,"v31_live_qa_run":40479186038,
    "source_paths":len(v3),"v31_paths":len(v31),"unchanged_original_files":unchanged_others,
    "v31_only_changed_files":len(change_paths),"v31_changed_routes":sorted(bad_phrase_routes),
    "previous_checked_urls":36043,"previous_first_pass":35986,"previous_retry_pass":57,
    "v31_course_links":len(rows),"v31_unchanged_course_pages":36036,"v31_repaired_live_verified":7,
    "V31_dong_text_fixed":True,"new_36043_rescan_completed":False,
    "sitemaps_unchanged":44,"sitemap_url_count":21964,"no_deleted_paths":True,
    "preview_url":qa["preview"],"production_id_unchanged":qa["published_id"],
    "mobile_tablet_pc_views":84,"actual_forms_submitted":0,"production_publish_events":0,
    "evidence_class_counts":dict(counter),"old_summary_file":str(oldfile),
    "source_qa":"PASS","production_publish_approval":"NOT_REQUESTED",
    "timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()
}
(OUT/"V31_FINAL_36043_RECONCILIATION.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf8")
md=("# ENGLISH PT V3.1 — Prepublication reconciliation\n\n"
    "**Overall:** PASS source-diff regression QA, not a second full 36,043-page HTTP pass.\n\n"
    "Original V3 live HTTP/Canonical/region check: 35,986 first-pass, 57 transient exceptions all retried successfully. "
    "A later complete 36,043-request run was cancelled and produced no artifact. "
    "This report does not mislabel it as a completed scan.\n\n"
    "V3 → V3.1: exactly 7 changed locality .page SHA values, all for 병목안동, "
    "other 36,036 course routes byte identical; all 7 changed pages passed live V3.1 browser GET.\n\n"
    f"All 202,786 file paths retained; {unchanged_others:,} source SHA entries unchanged. "
    "44 sitemap files and 21,964 sitemap URLs retained; 84 mobile/tablet/PC preview checks passed. "
    "Published source ID retained; no form submitted, no Production publish.\n\n"
    "**Before Production approval:** Check real lead form submit/email reception separately; "
    "confirm SEO and website status against current production and obtain explicit publication authorization.\n")
(OUT/"V31_FINAL_RECONCILIATION_REPORT.md").write_text(md,"utf8")
print("ENPT_V31_FINAL_36043_RECONCILIATION",json.dumps({k:v for k,v in report.items() if k!="v31_changed_routes"},ensure_ascii=False),flush=True)
