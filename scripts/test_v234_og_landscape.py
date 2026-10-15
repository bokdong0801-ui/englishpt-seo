#!/usr/bin/env python3
"""Small, deployment-free OG regression: 8 page types, all 29 masters."""
import importlib.util
import json
import re
import shutil
import tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = {
    "englishpt.html": "영어 공부, 지금 내 수준에 맞게 시작하세요.",
    "courses.html": "과정 찾기",
    "english-conversation.html": "영어회화 수업 안내",
    "exam-english.html": "토익부터 아이엘츠까지 시험영어",
    "student-english.html": "초등 중등 고등 학생영어 안내",
    "stations.html": "가까운 역에서 영어 시작하기",
    "station-gangnam.html": "강남역 영어회화 영어과외",
    "station-amsayeoksagongwon.html": "암사역사공원역 영어회화 영어과외",
    "seoul-jongno-sajikdong-beginner-english-conv.html": "사직동 왕초보영어회화",
    "seoul-jongno-sajikdong-toeic.html": "사직동 토익과외",
    "seoul-jongno-sajikdong-ielts.html": "사직동 아이엘츠과외",
    "seoul-jongno-sajikdong-worker-english-conv-academy.html": "사직동 직장인영어회화학원",
    "dalseo-songhyeondong.html": "송현동 영어과외 목적부터 나눠보세요",
}
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    out = Path("og-landscape-preview-artifact")
    out.mkdir(parents=True, exist_ok=True)
    generator = load("stage9_og_generator", ROOT / "scripts/stage9-square-search-thumbnails.py")
    builder = load("stage9_release_builder", ROOT / "scripts/build-stage9-production-release.py")
    test_root = Path(tempfile.mkdtemp(prefix="v234-og-"))
    report = {"status": "FAIL", "tested_pages": 0, "master_designs": 0,
              "aspect_ratio": "1200x630", "crop_safe": "central 630px",
              "issues": [], "pages": []}
    try:
        for name, title in SAMPLES.items():
            canonical = "https://englishpt.kr/" + name
            robots = "noindex,follow" if name == "stations.html" else "index,follow"
            raw = (
                '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
                f'<title>{title}</title><meta name="description" content="영어 과정 안내">'
                f'<meta name="robots" content="{robots}">'
                f'<meta property="og:url" content="{canonical}">'
                '<script type="application/ld+json">'
                + json.dumps({"@context":"https://schema.org",
                              "@type":"WebPage","name":title,"url":canonical},ensure_ascii=False)
                + '</script></head><body><h1>' + title + '</h1></body></html>')
            (test_root / name).write_text(raw, encoding="utf-8")
        generator_result = generator.build(test_root)
        errors = []
        metadata = builder.apply_search_image_metadata(test_root, errors)
        if errors:
            report["issues"].extend(str(x) for x in errors)
        manifest = json.loads((test_root / "assets/search-thumbnail-manifest.json").read_text(encoding="utf-8"))
        report["master_designs"] = generator_result["masters"]
        report["tested_pages"] = len(manifest)
        for name in SAMPLES:
            raw = (test_root / name).read_text(encoding="utf-8")
            image = manifest[name]["image"]
            asset = test_root / image.lstrip("/")
            checks = [
                '<meta property="og:image:width" content="1200">' in raw,
                '<meta property="og:image:height" content="630">' in raw,
                '<meta name="twitter:card" content="summary_large_image">' in raw,
                ('<meta property="og:image" content="https://englishpt.kr' + image + '">') in raw,
                ('<meta name="twitter:image" content="https://englishpt.kr' + image + '">') in raw,
                raw.count('<meta property="og:image"') == 1,
                'thumbnailUrl' in raw,
                manifest[name]["width"] == 1200 and manifest[name]["height"] == 630,
                manifest[name]["safe_crop"] == "center-square",
            ]
            with Image.open(asset) as im:
                checks.append(im.size == (1200, 630))
                if name in ("englishpt.html", "seoul-jongno-sajikdong-worker-english-conv-academy.html",
                            "station-amsayeoksagongwon.html"):
                    # Only for human screenshot approval: crop simulates square-share
                    # consumers, while preserving the meaningful central design.
                    im.crop((285,0,915,630)).save(out / (name[:-5]+"-center-square-crop.png"))
                    im.save(out / (name[:-5]+"-landscape.png"))
            passed = all(checks)
            report["pages"].append({"page":name,"status":"PASS" if passed else "FAIL","image":image})
            if not passed:
                report["issues"].append({"page":name,"checks":checks})
        full_audit = load("stage9_og_audit", ROOT / "scripts/qa_v234_og_all_pages.py")
        all_page_ok = full_audit.scan(test_root,len(SAMPLES),out / "OG_ALL_PAGE_SAMPLE_AUDIT.json")
        if not all_page_ok:
            report["issues"].append("all-page metadata/asset audit failed on synthetic preview")
        report["status"] = "PASS_V23_4_OG_LANDSCAPE_SAMPLE" if not report["issues"] and generator_result["masters"]==29 and metadata["missing_assets"]==0 else "FAIL_V23_4_OG_LANDSCAPE_SAMPLE"
        (out / "OG_LANDSCAPE_TEST_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(report["status"],"pages",report["tested_pages"],"masters",report["master_designs"],"issues",len(report["issues"]),flush=True)
        for issue in report["issues"][:10]:print("::error::"+str(issue),flush=True)
        return 0 if report["status"].startswith("PASS") else 1
    except Exception as exc:
        report["issues"].append(repr(exc))
        (out / "OG_LANDSCAPE_TEST_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        raise
    finally:
        shutil.rmtree(test_root,ignore_errors=True)

if __name__=="__main__":
    raise SystemExit(main())
