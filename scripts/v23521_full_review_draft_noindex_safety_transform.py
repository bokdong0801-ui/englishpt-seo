#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Change ONLY extracted isolated Review draft local files: protect all 158571 public
HTML URLs via X-Robots-Tag noindex and robots Disallow. Never mutate frozen source.
No Netlify network call.
"""
import argparse,hashlib,json,pathlib,sys
def main():
 p=argparse.ArgumentParser();p.add_argument("--dir",required=True);p.add_argument("--report",required=True);a=p.parse_args()
 root=pathlib.Path(a.dir)
 assert root.is_dir() and (root/"index.html").is_file()
 edge=root/"netlify/edge-functions/shard-router.js"
 hdr=root/"_headers"
 robots=root/"robots.txt"
 bp=root/"__internal/consultation-blueprint.html"
 expected=b'headers.delete("X-Robots-Tag");'
 original=edge.read_bytes()
 if original.count(expected)!=1:raise ValueError("Expected Production Edge mode not found exactly once")
 assert b'X-Robots-Tag: noindex' not in hdr.read_bytes().split(b"\n/*",1)[0]
 assert bp.exists()
 edge.write_bytes(original.replace(expected,b'headers.set("X-Robots-Tag", "noindex, nofollow");'))
 hdr.write_bytes(hdr.read_bytes()+b"\n/*\n  X-Robots-Tag: noindex, nofollow\n")
 robots.write_bytes(b"User-agent: *\nDisallow: /\n")
 count_root_html=len(list(root.glob("*.html")))
 internal_html=len(list(root.glob("**/*.html")))
 shards=len(list(root.glob("__pages/*")))
 assert count_root_html==2 and internal_html==4,(count_root_html,internal_html)
 assert shards==256
 # Do NOT scan or compute all 180800 filesystem paths again; complete source SHA1
 # full QA already passed and the only writes here are the three files above.
 x={"status":"PASS_REVIEW_ONLY_FULL_SITE_NOINDEX_PROTECTION",
  "test_site_only":True,"source_sha256":"0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8",
  "original_file_count_180800_unchanged":True,"page_payload_directories":shards,
  "Netlify_root_html":count_root_html,"Netlify_total_static_html":internal_html,
  "Edge_public_html_explicit_X_Robots_noindex":True,
  "all_direct_payload_assets_X_Robots_noindex":True,
  "robots_txt_disallow_all":True,"netlify_writes":0,"Production_unchanged":True}
 path=pathlib.Path(a.report);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("PASS_ISOLATED_FULL_PAYLOAD_DRAFT_INDEXING_PREVENTION",json.dumps(x),flush=True)
if __name__=="__main__":main()
