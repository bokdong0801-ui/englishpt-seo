#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ENGLISH PT v23.5.2.1 release preflight gate. NO network, NO deploy, NO POST.
Runs BEFORE Netlify upload. Immutable review/production are separate modes.
"""
import argparse, hashlib, json, re, struct, sys
from pathlib import Path
from urllib.parse import urlsplit

EXPECTED_OG=set(("beginner toeic ielts toefl opic tos duolingo elementary middle high "
"student worker college jobseeker housewife stations region academy tutor "
"conversation exam courses englishpt reading writing international phone video general").split())
EXPECTED_JS="d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede"
REVIEW_SITE="englishpt-final-ia-review-bokdong.netlify.app"
AREAS=("gyeongnam-milyang-naeidong","seoul-jongno-sajikdong")
GRADES=("elem-tutor","mid-tutor","high-tutor")

def inspect_host(host):
    if not host:
        raise ValueError("Hostname missing")
    if len(host)>253:
        raise ValueError("DNS hostname longer than 253 characters")
    labels=host.split(".")
    if any(not 1<=len(p)<=63 or not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?",p) for p in labels):
        raise ValueError("Invalid DNS label lengths/characters: "+repr([(p,len(p)) for p in labels]))
    return [(p,len(p)) for p in labels]

def test(mode,root,alias):
    r=dict(status="RUNNING",mode=mode,root=str(root),draft_redeployed=False,
           production_deployed=False,form_submitted=False,errors=[],checked=[])
    try:
        if mode in ("dns","review"):
            if not alias.startswith("https://"):
                raise ValueError("Expected HTTPS preview OG alias")
            host=urlsplit(alias).hostname
            r["dns_labels"]=inspect_host(host)
            if not host.endswith("--"+REVIEW_SITE):
                raise ValueError("OG host not the dedicated Review Netlify site")
            if host.startswith("englishpt.kr"):
                raise ValueError("Production OG host not permitted in Review")
            r["checked"].append("valid_review_og_dns_host")
        if mode!="dns":
            if not root.is_dir():
                raise ValueError("Expected unpacked site root")
            headers=(root/"_headers").read_text("utf8")
            if mode=="review" and "X-Robots-Tag: noindex" not in headers:
                raise ValueError("Review global noindex header missing")
            if mode=="production" and "X-Robots-Tag: noindex" in headers:
                raise ValueError("Production has global noindex")
            r["checked"].append("draft_production_header_separation")
            js=root/"pilot.js"
            if not js.is_file() or hashlib.sha256(js.read_bytes()).hexdigest()!=EXPECTED_JS:
                raise ValueError("Old / incorrect pilot.js: do NOT deploy")
            r["checked"].append("verified_patched_js_sha256")
            files=list(root.glob("*.html"))
            if len(files)!=158573:
                raise ValueError("Unexpected generated HTML count, expected 158573, found "+str(len(files)))
            r["checked"].append("158573_html_inventory")
            og_dir=root/"assets/images/og-pages"
            for stem in sorted(EXPECTED_OG):
                fn=og_dir/(stem+".png")
                with fn.open("rb") as f:
                    header=f.read(24)
                if len(header)!=24 or header[:8]!=bytes.fromhex("89504e470d0a1a0a"):
                    raise ValueError("Invalid PNG: "+fn.name)
                if struct.unpack(">II",header[16:24])!=(1200,630):
                    raise ValueError("Incorrect 1200x630 OG PNG: "+fn.name)
            r["checked"].append("29_og_pngs_1200x630")
            expect_og_prefix=(alias if mode=="review" else "https://englishpt.kr")+"/assets/images/og-pages/"
            for loc in AREAS:
                for grade in GRADES:
                    html=(root/(loc+"-"+grade+".html")).read_text("utf8")
                    if expect_og_prefix not in html:
                        raise ValueError("Wrong OG host for "+loc+"-"+grade)
                    if "영어과외 상담 신청" not in html:
                        raise ValueError("Tutor consultation copy missing")
                    if "name=\"consent\"" not in html:
                        raise ValueError("Consent missing")
                    if "rel=\"canonical\" href=\"https://englishpt.kr/" not in html:
                        raise ValueError("Canonical unexpected")
                    if mode=="production" and REVIEW_SITE in html:
                        raise ValueError("Review hostname leaked into Production")
            r["checked"].append("6_live_pilot_html_contracts")
        r["status"]="PASS_"+mode.upper()+"_RELEASE_PREFLIGHT"
    except Exception as exc:
        r["status"]="HOLD_"+mode.upper()+"_RELEASE_PREFLIGHT"
        r["errors"].append(str(exc))
    return r

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("dns","review","production"),required=True)
    p.add_argument("--root",type=Path,default=Path("review-site"))
    p.add_argument("--og-alias",default="")
    p.add_argument("--report",type=Path,default=Path("v2352-live-report/RELEASE_PREFLIGHT.json"))
    a=p.parse_args()
    r=test(a.mode,a.root,a.og_alias.rstrip("/"))
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(r["status"],r["checked"],r["errors"],flush=True)
    return 0 if r["status"].startswith("PASS_") else 1

if __name__=="__main__":
    sys.exit(main())
