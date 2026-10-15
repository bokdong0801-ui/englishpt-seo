#!/usr/bin/env python3
"""Create cropped-safe 1200x630 OG PNGs and insert OG/Twitter tags across an extracted v23.4 release.
Offline only. Never publishes anything to Netlify or englishpt.kr.
"""
import argparse, html, json, re, sys
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DOMAIN="https://englishpt.kr"
CATS=[
 ("beginner","왕초보 영어회화",("#203C31","#E2F2E8"),("beginner","basic","phonics")),
 ("toeic","토익 맞춤 영어",("#153C65","#DFEAF9"),("toeic",)),
 ("ielts","IELTS 영어",("#452B3D","#F5E8E9"),("ielts",)),
 ("toefl","TOEFL 영어",("#313D62","#ECEDF9"),("toefl",)),
 ("opic","오픽 영어",("#285B48","#E8F4E7"),("opic",)),
 ("tos","토익스피킹",("#225071","#E9F4F8"),("tos","toeic-speaking")),
 ("duolingo","듀오링고 영어",("#594A36","#F8F0E2"),("duolingo",)),
 ("elementary","초등학생 영어",("#336252","#E7F7E6"),("elem-","elementary")),
 ("middle","중학생 영어",("#304A68","#ECF2FA"),("mid-","middle-")),
 ("high","고등학생 영어",("#3B466A","#F1F3FD"),("high-","suneung")),
 ("student","학생 영어",("#386254","#E8F6ED"),("student-english",)),
 ("worker","직장인 영어",("#203B31","#E4F1E9"),("worker","business","biz-")),
 ("college","대학생 영어",("#253F61","#EAF1FA"),("college","university")),
 ("jobseeker","취업 영어",("#4C394A","#F6EBF4"),("jobseeker","interview")),
 ("housewife","성인 생활영어",("#315D59","#E5F5EE"),("housewife",)),
 ("stations","역에서 찾는 영어",("#1E5542","#E6F4ED"),("station-","stations")),
 ("region","지역별 맞춤 영어",("#285444","#E7F2E9"),("songhyeondong","sajikdong","neighborhood")),
 ("academy","영어학원 수업",("#28445B","#EDF2F7"),("academy",)),
 ("tutor","1:1 영어과외",("#245643","#E3F2E8"),("tutor","1to1","visit")),
 ("conversation","영어회화",("#245845","#E6F5EB"),("english-conversation","conv")),
 ("exam","시험영어",("#433A56","#F0ECFA"),("exam-english","cert")),
 ("courses","과정별 영어 안내",("#205346","#E9F6EF"),("courses",)),
 ("englishpt","잉글리시PT",("#152D24","#E7F5EB"),("englishpt","index")),
 ("reading","영어 독해",("#284965","#E8F2FB"),("reading",)),
 ("writing","영어 작문",("#503D55","#F5EFF9"),("writing",)),
 ("international","국제학교 영어",("#325063","#EAF4F7"),("intl-","international")),
 ("phone","전화 영어",("#345267","#ECF4FB"),("phone",)),
 ("video","화상 영어",("#285D62","#E9F7F8"),("video",)),
 ("general","내 수준에 맞춘 영어",("#1D4637","#E7F4EA"),()),
]

def category(name):
    n=name.lower()
    # Most specific types first; fallback to broad categories.
    for key,_,_,tokens in CATS:
        if key=="region":
            continue
        if any(t in n for t in tokens):
            return key
    if any(x in n for x in ("songhyeondong","sajikdong","dong-")):
        return "region"
    return "general"

def font(size):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
              "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf",
              "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p,size)
    raise FileNotFoundError("No Korean-capable font; install fonts-noto-cjk before rendering")

def draw_png(folder, key, title, colors):
    bg,light=colors
    im=Image.new("RGB",(1200,630),bg)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((28,28,1172,602),radius=34,outline=light,width=3)
    d.rounded_rectangle((84,105,1116,525),radius=36,fill=light)
    # Main semantic content stays inside central square x=285..915;
    # square-safe title inside x=330..870 with readable margin.
    d.text((600,177),"ENGLISH PT",fill=bg,font=font(33),anchor="mm")
    d.line((468,215,732,215),fill=bg,width=3)
    title_font=font(55)
    while d.textbbox((0,0),title,font=title_font)[2]>518:
        title_font=font(title_font.size-2)
        if title_font.size<24:break
    d.text((600,310),title,fill=bg,font=title_font,anchor="mm")
    d.text((600,405),"1:1 맞춤 영어 학습",fill=bg,font=font(30),anchor="mm")
    d.text((600,466),"수준과 목표에 맞춘 단계별 안내",fill=bg,font=font(20),anchor="mm")
    out=folder/(key+".png")
    im.save(out,format="PNG",optimize=True)
    assert Image.open(out).size==(1200,630)
    return out

def meta_transform(content, png):
    head=re.search(r"<head(?:\s[^>]*)?>",content,re.I)
    if not head:raise ValueError("head opening tag absent")
    closing=re.search(r"</head\s*>",content,re.I)
    if not closing:raise ValueError("head closing tag absent")
    titlematch=re.search(r"<title[^>]*>(.*?)</title>",content,re.S|re.I)
    title=html.unescape(re.sub(r"<[^>]+>","",titlematch.group(1))).strip() if titlematch else "잉글리시PT"
    title=title[:150]
    alt=html.escape(title,quote=True)
    url=DOMAIN+"/assets/images/og-pages/"+png+".png"
    # Existing OG/Twitter image tags replaced in-place, with no duplicates.
    strip=re.compile(r'<meta\b(?=[^>]*(?:property|name)\s*=\s*["\x27](?:og:image(?:[:][\w-]+)?|twitter:image|twitter:card)["\x27])[^>]*>',re.I)
    content=strip.sub("",content)
    close=re.search(r"</head\s*>",content,re.I)
    payload=(
      '<meta property="og:image" content="'+url+'">'
      '<meta property="og:image:secure_url" content="'+url+'">'
      '<meta property="og:image:type" content="image/png">'
      '<meta property="og:image:width" content="1200">'
      '<meta property="og:image:height" content="630">'
      '<meta property="og:image:alt" content="'+alt+'">'
      '<meta name="twitter:card" content="summary_large_image">'
      '<meta name="twitter:image" content="'+url+'">'
    )
    return content[:close.start()]+payload+content[close.start():]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--expected",type=int,default=140391)
    a=ap.parse_args()
    root=a.root.resolve()
    images=root/"assets/images/og-pages"
    images.mkdir(parents=True,exist_ok=True)
    counts=Counter();errors=[]
    for key,title,colors,tokens in CATS:
        draw_png(images,key,title,colors)
    pages=sorted(root.glob("*.html"))
    generated=[x for x in pages if x.name not in ("404.html","index.html")]
    if len(generated)!=a.expected:
        errors.append("Unexpected generated page count "+str(len(generated)))
    for index,p in enumerate(pages):
        try:
            original=p.read_text(encoding="utf-8")
            key=category(p.stem)
            updated=meta_transform(original,key)
            p.write_text(updated,encoding="utf-8")
            counts[key]+=1
            if index and index%25000==0:print("OG_PATCH_PROGRESS",index,len(pages),flush=True)
        except Exception as exc:
            errors.append(f"{p.name}: {exc}")
            if len(errors)>500:break
    report={"status":"PASS_V23_4_OG_METADATA" if not errors else "FAIL_V23_4_OG_METADATA",
       "expected_generated":a.expected,"generated_found":len(generated),"html_scanned":len(pages),
       "html_updated":sum(counts.values()),"image_count":len(CATS),"categories":dict(counts),
       "width":1200,"height":630,"square_center_safe_zone":[285,0,915,630],
       "published":False,"production_modified":False,
       "source_run":"38689660290",
       "source_sha":"a18b8901ecda7d37f65e35b15f03d579ec63c70f",
       "errors":errors[:500],
       "important_note":"OG image absolute URLs use englishpt.kr; they resolve publicly only after separately approved Production publication."}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(report["status"],"updated",report["html_updated"],"generated",len(generated),"errors",len(errors),flush=True)
    return 0 if not errors else 1

if __name__=="__main__":
    sys.exit(main())
