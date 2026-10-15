#!/usr/bin/env python3
"""Repackage immutable v23.4 without changing a single body/CTA/link.

Regenerate only crop-safe 1200x630 Open Graph images and meta tags. Every page
is checked by qa_v234_og_all_pages, and all 140391 HTML bodies are compared
bit-for-bit before/after. No Netlify or Production interactions.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import traceback
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN = "38689660290"
SOURCE_SHA = "a18b8901ecda7d37f65e35b15f03d579ec63c70f"
SAMPLES = (
    "englishpt.html","courses.html","english-conversation.html",
    "exam-english.html","student-english.html","stations.html",
    "station-gangnam.html","station-amsayeoksagongwon.html",
    "seoul-jongno-sajikdong-beginner-english-conv.html",
    "seoul-jongno-sajikdong-toeic.html","seoul-jongno-sajikdong-ielts.html",
    "seoul-jongno-sajikdong-worker-english-conv-academy.html",
    "dalseo-songhyeondong.html",
)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,str(path))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def body_hash(root:Path):
    h=hashlib.sha256(); count=0
    for p in sorted(root.glob("*.html")):
        if p.name in ("index.html","404.html"):
            continue
        raw=p.read_bytes()
        parts=raw.split(b"</head>",1)
        if len(parts)!=2:
            raise ValueError("Missing </head>: "+p.name)
        h.update(p.name.encode("utf-8")+b"\0")
        h.update(hashlib.sha256(parts[1]).digest())
        count+=1
    return h.hexdigest(),count

def run(root:Path,out:Path):
    report={
        "status":"FAIL_V23_4_OG_ONLY_REPACK", "source_run":SOURCE_RUN,
        "source_sha":SOURCE_SHA,"expected_generated_pages":140391,
        "generated_pages_checked":0,"original_body_digest":None,
        "modified_body_digest":None,"body_unchanged":False,
        "og_all_pages_report":None,"og_error_count":None,
        "netlify_uploaded":False,"production_deployed":False,
        "consultation_form_submitted":False,"issues":[],
        "started_at":datetime.now(timezone.utc).isoformat(),
    }
    out.mkdir(parents=True,exist_ok=True)
    try:
        original,count=body_hash(root)
        report["original_body_digest"]=original
        report["generated_pages_checked"]=count
        if count!=140391:
            raise ValueError(f"Expected 140391 HTML documents, got {count}")
        print("PASS_V234_IMMUTABLE_BODY_SNAPSHOT",count,original,flush=True)
        generator=module("og_generator",ROOT/"scripts/stage9-square-search-thumbnails.py")
        builder=module("og_release_builder",ROOT/"scripts/build-stage9-production-release.py")
        auditor=module("og_auditor",ROOT/"scripts/qa_v234_og_all_pages.py")

        generation=generator.build(root)
        if generation["masters"]!=29:
            raise ValueError("Wrong master count")
        print("PASS_OG_LANDSCAPE_GENERATION",json.dumps(generation),flush=True)

        failures=[]
        metadata=builder.apply_search_image_metadata(root,failures)
        if failures:
            raise ValueError("OG metadata patch failed: "+json.dumps(failures[:5],ensure_ascii=False))
        if metadata.get("landscape_size")!="1200x630":
            raise ValueError("OG size metadata remains square")
        print("PASS_OG_METADATA_APPLIED",metadata["html_pages"],flush=True)

        audited=auditor.scan(root,140391,out/"STAGE9_OG_LANDSCAPE_ALL_PAGES_QA.json")
        audit=json.loads((out/"STAGE9_OG_LANDSCAPE_ALL_PAGES_QA.json").read_text(encoding="utf-8"))
        report["og_all_pages_report"]=audit["status"]
        report["og_error_count"]=audit["errors"]
        report["og_pages_checked"]=audit["pages_checked"]
        report["og_image_files_checked"]=audit["unique_image_paths_checked"]
        if not audited:
            raise ValueError("OG exhaustive audit did not pass")

        current,post_count=body_hash(root)
        report["modified_body_digest"]=current
        report["body_unchanged"]=(current==original and post_count==count)
        if not report["body_unchanged"]:
            raise ValueError("BODY_CONTENT_OR_LINKS_CHANGED; abort repack")
        print("PASS_140391_UNCHANGED_BODIES_AND_LINKS",post_count,current,flush=True)
        # Copy a few small actual new PNGs and JSON metadata examples.
        sample_rows=[]
        for name in SAMPLES:
            html_doc=root/name
            if not html_doc.is_file():
                raise FileNotFoundError("Missing representative page "+name)
            rel=json.loads((root/"assets/search-thumbnail-manifest.json").read_text(encoding="utf-8"))[name]["image"] if False else None
            sample_rows.append(name)
        manifest=json.loads((root/"assets/search-thumbnail-manifest.json").read_text(encoding="utf-8"))
        sample_dir=out/"sample-og-images"
        sample_dir.mkdir(parents=True,exist_ok=True)
        examples={}
        for name in SAMPLES:
            entry=manifest[name]
            src=root/entry["image"].lstrip("/")
            if not src.is_file():
                raise FileNotFoundError(str(src))
            dst=sample_dir/name[:-5]
            shutil.copyfile(src,dst.with_suffix(".png"))
            examples[name]={"image":entry["absolute_image"],
                             "width":entry["width"],"height":entry["height"]}
        (out/"OG_REPRESENTATIVE_IMAGES.json").write_text(json.dumps(examples,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        report["sample_og_previews"]=len(examples)
        report["status"]="PASS_V23_4_OG_ONLY_REPACK"
    except Exception as exc:
        report["issues"].append(str(exc))
        report["exception_traceback"]=traceback.format_exc()[-3500:]
        print("::error::"+str(exc),flush=True)
    finally:
        report["completed_at"]=datetime.now(timezone.utc).isoformat()
        (out/"OG_ONLY_REPACK_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(report["status"],"pages",report["generated_pages_checked"],
              "og_errors",report["og_error_count"],"body_unchanged",report["body_unchanged"],flush=True)
    return report["status"]=="PASS_V23_4_OG_ONLY_REPACK"

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--root",required=True,type=Path)
    p.add_argument("--report-dir",required=True,type=Path)
    a=p.parse_args();sys.exit(0 if run(a.root,a.report_dir) else 1)
