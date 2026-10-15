#!/usr/bin/env python3
"""Exhaustive v23.4 Open Graph metadata + PNG IHDR validation; read-only.

Checks each of the 140391 generated pages, the shared master/page image
file dimensions (real PNG headers), secure OG links, Twitter, alt, schema,
and the expected landscape aspect. Fails closed; JSON diagnostics always saved.
"""
from __future__ import annotations
import argparse
import json
import re
import struct
import sys
from pathlib import Path
from urllib.parse import urlparse

OG_BASE = "https://englishpt.kr"
SIZE = (1200, 630)

META = re.compile(r'<meta\s+(?:property|name)="([^"]+)"\s+content="([^"]*)"\s*/?>', re.I)
IMAGE_SRC = re.compile(r'<link rel="image_src" href="([^"]*)">', re.I)
SCHEMA = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.I | re.S)

def png_size(path: Path):
    with path.open("rb") as f:
        header = f.read(24)
    if (len(header) < 24 or header[:8] != b'\x89PNG\r\n\x1a\n'
            or header[12:16] != b'IHDR'):
        raise ValueError("invalid_png_header")
    return struct.unpack(">II", header[16:24])

def schema_has_image(document, url):
    if isinstance(document, dict):
        return (document.get("image") == url or document.get("thumbnailUrl") == url
                or any(schema_has_image(v, url) for v in document.values()))
    if isinstance(document, list):
        return any(schema_has_image(v, url) for v in document)
    return False

def scan(root: Path, expected: int, report_path: Path):
    report = {
        "status":"FAIL_V23_4_OG_ALL_PAGES", "version":"v23.4",
        "total_expected":expected, "pages_checked":0,
        "valid_pages":0, "unique_image_paths_checked":0,
        "master_image_count":0, "page_image_count":0,
        "missing_image_files":0, "incorrect_png_dimensions":0,
        "metadata_issues":0, "schema_issues":0,
        "errors":0, "samples":[],
        "image_format":"PNG", "dimensions":{"width":1200,"height":630},
        "crop_safe_layout":"center-square x=285..915; primary content x=306..894",
        "deployment":"NONE",
    }
    root = root.resolve()
    checked_assets = {}
    def fail(page, reason, detail=""):
        report["errors"] += 1
        key = ("missing_image_files" if reason=="missing_image" else
               "incorrect_png_dimensions" if reason.startswith("png_") else
               "schema_issues" if reason.startswith("schema_") else
               "metadata_issues")
        report[key] += 1
        if len(report["samples"]) < 100:
            report["samples"].append({"page":page,"reason":reason,"detail":str(detail)[:200]})
    try:
        pages = sorted(root.glob("*.html"))
        pages = [p for p in pages if p.name not in ("404.html","index.html")]
        if len(pages) != expected:
            fail("(release)", "generated_page_count_mismatch", f"{len(pages)} / {expected}")
        manifest_file = root / "assets/search-thumbnail-manifest.json"
        if not manifest_file.is_file():
            raise FileNotFoundError("search-thumbnail-manifest.json not found")
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        for p in pages:
            report["pages_checked"] += 1
            try:
                raw=p.read_text(encoding="utf-8",errors="replace")
                entries={}
                for k,v in META.findall(raw):
                    entries.setdefault(k.lower(),[]).append(v)
                entry=manifest.get(p.name)
                if not entry:
                    fail(p.name,"missing_manifest_entry")
                    continue
                image_url=entry.get("absolute_image","")
                image_rel=entry.get("image","")
                if not image_url.startswith(OG_BASE+"/assets/images/") or image_url != OG_BASE+image_rel:
                    fail(p.name,"manifest_image_url_bad",image_url)
                if entry.get("width") != 1200 or entry.get("height") != 630 or entry.get("safe_crop") != "center-square":
                    fail(p.name,"manifest_geometry_invalid",entry)
                required={
                    "og:image":image_url, "og:image:secure_url":image_url,
                    "og:image:width":"1200","og:image:height":"630",
                    "og:image:type":"image/png",
                    "twitter:card":"summary_large_image",
                    "twitter:image":image_url,
                }
                for key,value in required.items():
                    if entries.get(key)!=[value]:
                        fail(p.name,"metadata_bad_"+key,entries.get(key))
                if not entries.get("og:image:alt") or not entries["og:image:alt"][0].strip():
                    fail(p.name,"og_image_alt_missing")
                if not entries.get("twitter:image:alt") or not entries["twitter:image:alt"][0].strip():
                    fail(p.name,"twitter_image_alt_missing")
                if IMAGE_SRC.findall(raw)!=[image_url]:
                    fail(p.name,"image_src_mismatch")
                if not any(schema_has_image(json.loads(x),image_url) for x in SCHEMA.findall(raw)):
                    fail(p.name,"schema_image_not_matching")
                local_asset=root/image_rel.lstrip("/")
                if not local_asset.is_relative_to(root):
                    fail(p.name,"unsafe_image_asset_path",image_rel)
                elif image_rel not in checked_assets:
                    try:
                        if not local_asset.is_file():
                            fail(p.name,"missing_image",image_rel)
                            checked_assets[image_rel] = None
                        else:
                            dims=png_size(local_asset)
                            checked_assets[image_rel]=dims
                            if dims!=SIZE:
                                fail(p.name,"png_wrong_dimensions",f"{image_rel} {dims}")
                    except Exception as ex:
                        checked_assets[image_rel]=None
                        fail(p.name,"png_unreadable",f"{image_rel} {ex}")
                if report["pages_checked"]%20000==0:
                    print("OG_AUDIT_PROGRESS",report["pages_checked"],"errors",report["errors"],flush=True)
            except Exception as ex:
                fail(p.name,"audit_page_exception",repr(ex))
        report["unique_image_paths_checked"]=len(checked_assets)
        report["master_image_count"]=sum(p.startswith("/assets/images/og-master/") for p in checked_assets)
        report["page_image_count"]=sum(p.startswith("/assets/images/og-pages/") for p in checked_assets)
        report["valid_pages"]=len(pages) if report["errors"]==0 else None
        if report["errors"]==0 and len(pages)==expected and report["page_image_count"]>0 and report["master_image_count"]>0:
            report["status"]="PASS_V23_4_OG_ALL_PAGES"
    except Exception as ex:
        fail("(runner)","audit_runner_exception",repr(ex))
    finally:
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(report["status"],"pages",report["pages_checked"],"assets",report["unique_image_paths_checked"],"errors",report["errors"],flush=True)
        return report["errors"]==0 and report["status"].startswith("PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--expected",type=int,default=140391)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args()
    sys.exit(0 if scan(a.root,a.expected,a.report) else 1)
