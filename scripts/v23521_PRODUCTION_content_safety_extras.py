#!/usr/bin/env python3
"""Production-only robots, global noindex, Edge & Forms blueprint safety; OFFLINE."""
import argparse,gzip,json,pathlib,re,subprocess,tarfile,tomllib,sys
SHA="0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8"
def main():
 p=argparse.ArgumentParser();p.add_argument("--archive",required=True);p.add_argument("--mapping",required=True)
 p.add_argument("--full-qa",required=True);p.add_argument("--output",required=True);a=p.parse_args()
 r={"status":"HOLD_PRODUCTION_CONTENT_QA","passed":[],"blockers":[],"netlify_uploads":0,"forms_POST":0,"production_published":False}
 try:
  qa=json.loads(pathlib.Path(a.full_qa).read_text("utf8"))
  must={"status":"PASS_FULL_158571_PAYLOAD_SEO_URL_PARITY_AND_FOUR_HTML_NETLIFY",
   "archive_sha256":SHA,"site_files_sha1_verified":180800,"indexable":21964,
   "noindex":136607,"site_map_urls":21964,"static_html_count":4,"png_total":22088}
  for k,v in must.items():
   if qa.get(k)!=v:raise ValueError("Full file QA "+k+" not PASS")
  r["passed"].append("full_180800_file_SHA1_indexable_21964_noindex_136607_sitemaps")
  with gzip.open(a.mapping,"rt",encoding="utf8") as f:mp=json.load(f)["original_public_html_to_data_payload"]
  if len(mp)!=158571 or len({x["to"] for x in mp.values()})!=158571:raise ValueError("URL mapping invalid")
  if sum(bool(x["noindex"]) for x in mp.values())!=136607:raise ValueError("per URL meta robots policy invalid")
  r["passed"].append("158571_canonical_public_urls_and_per_route_index_policy")
  wanted={"robots.txt","_headers","_redirects","netlify.toml",
          "netlify/edge-functions/shard-router.js","__internal/consultation-blueprint.html"}
  found={}
  z=subprocess.Popen(["zstd","-dc",a.archive],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
  try:
   with tarfile.open(fileobj=z.stdout,mode="r|") as archive:
    for m in archive:
     n=m.name.removeprefix("./")
     if m.isfile() and n in wanted:
      if n in found or m.size>5000000:raise ValueError("Config missing/collision/too large: "+n)
      found[n]=archive.extractfile(m).read().decode("utf8")
   if z.wait(timeout=90)!=0:raise ValueError("Invalid candidate zstd stream")
  finally:z.stdout.close()
  if set(found)!=wanted:raise ValueError("Missing site config "+str(wanted-set(found)))
  robots=found["robots.txt"]
  hdr=found["_headers"]
  edge=found["netlify/edge-functions/shard-router.js"]
  form=found["__internal/consultation-blueprint.html"]
  redirects=found["_redirects"]
  cfg=tomllib.loads(found["netlify.toml"])
  if re.search(r"(?im)^\s*Disallow:\s*/\s*$",robots):raise ValueError("Production robots globally disallows indexing")
  if "User-agent:" not in robots:raise ValueError("Production robots empty")
  if re.search(r"(?im)^/\*\s*\n[ \t]*X-Robots-Tag:[ \t]*noindex",hdr):
   raise ValueError("Review-wide noindex X-Robots-Tag leaked into Production")
  for route in ("/__pages/*","/__internal/*"):
   if not re.search(r"(?m)^"+re.escape(route)+r"\s*\n[ \t]*X-Robots-Tag:\s*noindex",hdr):
    raise ValueError("Internal .page/Form route missing raw-asset noindex: "+route)
  if 'headers.delete("X-Robots-Tag");' not in edge:raise ValueError("Public Edge noindex cleanup absent")
  if 'headers.set("X-Robots-Tag", "noindex, nofollow");' in edge:
   raise ValueError("Review Edge global noindex leaked into Production")
  r["passed"].append("Production_robots_not_globally_disallowed_and_Edge_clears_payload_noindex")
  r["passed"].append("internal_payload_and_Form_blueprint_are_noindex")
  if len(cfg.get("edge_functions",[]))!=1:raise ValueError("Edge config not exactly one")
  for token in ('<form','name="englishpt-consultation"','data-netlify="true"',
                'name="form-name"','name="requestType"','name="subject"'):
   if token not in form:raise ValueError("Consultation blueprint missing "+token)
  if 'method="post"' not in form.lower():raise ValueError("Forms blueprint missing POST method")
  if '<meta name="robots" content="noindex,nofollow"' not in form.lower():
   raise ValueError("Form blueprint public indexing not blocked")
  r["passed"].append("Static_Netlify_Forms_detection_blueprint_POST_noindex")
  redirects301=[s for s in redirects.splitlines() if len(s.split())>=3 and s.split()[2].startswith("301")]
  if len(redirects301)<70:raise ValueError("Existing 301 redirects missing")
  r["redirect_rules_preserved"]=len(redirects301)
  r["passed"].append("legacy_301_redirects_preserved")
  r["status"]="PASS_PRODUCTION_CONTENT_SEO_EDGE_FORMS_SAFETY"
 except Exception as e:
  r["blockers"].append(type(e).__name__+": "+str(e)[:300])
 out=pathlib.Path(a.output);out.parent.mkdir(exist_ok=True,parents=True)
 out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("PRODUCTION_CONTENT_FINAL_EXTRA",json.dumps(r,ensure_ascii=False),flush=True)
 return 0 if r["status"].startswith("PASS_") else 1
if __name__=="__main__":sys.exit(main())
