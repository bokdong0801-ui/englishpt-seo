#!/usr/bin/env python3
# coding: utf-8
"""Generate 120 exact-route square EnglishPT editorial PILOT images, deterministic and read-only.
This process NEVER modifies production OG metadata or Netlify.
"""
from __future__ import annotations
import collections,csv,functools,hashlib,io,json,math,pathlib,random,re,statistics,sys
from PIL import Image,ImageDraw,ImageFont,ImageFilter

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"thumb-21964-outputs"
PILOT=OUT/"pilot-jpg"
PILOT.mkdir(parents=True,exist_ok=True)
WIDTH=HEIGHT=1200
LEFT_CENTER=474
SIZE=(WIDTH,HEIGHT)
FONTS=[
 "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
 "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf",
]
BOLD=[
 "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
 "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf",
]
def find_font(candidates):
 for p in candidates:
  if pathlib.Path(p).exists():return p
 raise RuntimeError("Korean glyph font missing; install fonts-noto-cjk")
REGULAR=find_font(FONTS)
STRONG=find_font(BOLD)
@functools.lru_cache(maxsize=450)
def ft(size,strong=False):return ImageFont.truetype(STRONG if strong else REGULAR,size)
def bb(d,s,f):return d.textbbox((0,0),s,font=f)
def fittest(d,s,start,width,maxheight=None,minsize=26,strong=False):
 for n in range(start,minsize-1,-1):
  f=ft(n,strong)
  b=bb(d,s,f)
  if b[2]-b[0]<=width and (not maxheight or b[3]-b[1]<=maxheight):return f
 raise ValueError("TEXT_FIT_FAIL "+str(s))
def centered(d,s,cx,top,f,color="#263037"):
 b=bb(d,s,f)
 x=round(cx-(b[0]+b[2])/2);y=round(top-b[1])
 real=d.textbbox((x,y),s,font=f)
 d.text((x,y),s,font=f,fill=color)
 return real
def base_texture():
 image=Image.new("RGB",SIZE,(251,249,244))
 # Soft editorial paper, low contrast to maximize readability.
 import random
 random.seed(20261020)
 overlay=Image.new("L",(200,200),128);px=overlay.load()
 for y in range(200):
  for x in range(200):px[x,y]=max(125,min(131,128+int(random.gauss(0,1.2))))
 overlay=overlay.resize(SIZE,Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(1))
 col=Image.new("RGB",SIZE)
 col.paste((249,247,243),(0,0,WIDTH,HEIGHT))
 return Image.blend(image,col,0.18)
PAPER=base_texture()
def choose_pilot(rows,limit=150):
 # Always cover 23 intents + hubs + regional + long Korean station labels + mixed test categories.
 fixed=[r for r in rows if r["route_type"]=="national_hub"]
 regions=[r for r in rows if r["route_type"]=="regional" and r["mapping_status"]=="READY_METADATA_ONLY"]
 candidates=[r for r in rows if r["route_type"]=="station"]
 by_intent={}
 for r in candidates:
  by_intent.setdefault(r["intent_slug"],r)
 fixed+=list(by_intent.values())+regions[:10]
 # Edge cases are essential for fitting QA.
 longest=sorted(candidates,key=lambda x:len(x["location_name"]),reverse=True)
 fixed+=longest[:23]
 # Random stable selection from remainder, seeded.
 rng=random.Random(20261020)
 out=[];seen=set()
 for x in fixed+rng.sample(candidates,min(len(candidates),max(0,limit-len(fixed)+35))):
  if x["route"] in seen:continue
  seen.add(x["route"]);out.append(x)
  if len(out)>=limit:break
 return out
def draw_one(row):
 im=PAPER.copy()
 d=ImageDraw.Draw(im)
 rgb=tuple(bytes.fromhex(row["accent_hex"].lstrip("#")))
 d.ellipse((825,-200,1790,800),fill=rgb)
 softer=tuple(min(255,int(x*0.3+255*0.7)) for x in rgb)
 d.ellipse((765,902,1700,1740),fill=softer)
 name=row["location_name"];lines=[row[k] for k in ("title_line_1","title_line_2","title_line_3") if row[k]]
 if not 1<=len(lines)<=3:raise ValueError("TITLE_LINES_LENGTH")
 if not name or not row["search_keyword"]:raise ValueError("EMPTY_LABEL_OR_KEYWORD")
 f_head=fittest(d,name,58,750,minsize=26)
 hb=centered(d,name,105+(bb(d,name,f_head)[2]-bb(d,name,f_head)[0])/2,122,f_head)
 d.line((110,235,245,235),fill="#2B3034",width=5)
 text_area=(83,880)
 gap=44 if len(lines)==2 else 31
 candidates=[fittest(d,t,221 if len(lines)==2 else 158,780,minsize=54,strong=True) for t in lines]
 heights=[bb(d,t,f)[3]-bb(d,t,f)[1] for t,f in zip(lines,candidates)]
 block_height=sum(heights)+gap*(len(lines)-1)
 # Vertical center content between header and footer, allowing long 3-line tests.
 top=round(368+(3-len(lines))*48)
 if top+block_height>940:top=940-block_height
 top=max(300,top)
 title_boxes=[];current=top
 for t,f,height in zip(lines,candidates,heights):
  rect=centered(d,t,LEFT_CENTER,current,f)
  title_boxes.append(rect);current+=height+gap
 footer=row["subtitle"]
 footfont=fittest(d,footer,46,780,minsize=26)
 footerbox=centered(d,footer,LEFT_CENTER,1068,footfont,"#33363A")
 err=[]
 for box in title_boxes:
  if box[0]<text_area[0] or box[2]>text_area[1] or box[1]<290 or box[3]>969:err.append("TITLE_SAFE_BOUNDS")
  if abs((box[0]+box[2])/2-LEFT_CENTER)>1.5:err.append("TITLE_CENTER")
 if footerbox[0]<75 or footerbox[2]>885 or footerbox[1]<1030 or footerbox[3]>1140:err.append("FOOTER_SAFE_BOUNDS")
 if abs((footerbox[0]+footerbox[2])/2-LEFT_CENTER)>1.5:err.append("FOOTER_CENTER")
 if any(a[3]>=b[1] for a,b in zip(title_boxes,title_boxes[1:])):err.append("LINE_OVERLAP")
 if any(box[3]>=footerbox[1]-40 for box in title_boxes):err.append("TITLE_FOOTER_COLLISION")
 if hb[0]<85 or hb[2]>830 or hb[1]<100 or hb[3]>215:err.append("HEADER_BOUNDS")
 filename=row["image_key"]+".jpg"
 out=PILOT/filename
 im.save(out,"JPEG",quality=84,optimize=True,subsampling=0)
 if Image.open(out).size!=(1200,1200):err.append("WRONG_SIZE")
 if out.stat().st_size>350_000:err.append("FILE_TOO_LARGE_350KB")
 tiny=im.resize((102,102),Image.Resampling.LANCZOS)
 return {"route":row["route"],"header":name,"keyword":row["search_keyword"],"category":row["category"],
  "color":row["accent_hex"],"image":"pilot-jpg/"+filename,"bytes":out.stat().st_size,
  "title_boxes":title_boxes,"footer_box":footerbox,"errors":err,"small":tiny}
with (OUT/"ALL_21964_INDEXABLE_THUMBNAIL_MAP.csv").open(encoding="utf-8-sig",newline="") as f:
 rows=list(csv.DictReader(f))
pilot=choose_pilot(rows,limit=150)
results=[draw_one(r) for r in pilot]
issues=[{"route":r["route"],"issues":r["errors"]} for r in results if r["errors"]]
# 4-column full preview and mobile 102-pixel list preview, no platform endorsement.
cells=results[:32]
sheet=Image.new("RGB",(4*320,math.ceil(len(cells)/4)*365),"#EFEFED")
D=ImageDraw.Draw(sheet)
for i,row in enumerate(cells):
 x=(i%4)*320+12;y=(i//4)*365+12
 im=Image.open(PILOT/(row["image"].rsplit("/",1)[-1]))
 sheet.paste(im.resize((295,295)),(x,y))
 lab=row["route"].replace(".html","")[-35:]
 D.text((x,y+302),lab,font=ft(16),fill="#253039")
sheet.save(OUT/"PILOT_32_GRID.jpg",quality=86,optimize=True)
mobile=Image.new("RGB",(750,20+min(36,len(results))*117),"white")
MD=ImageDraw.Draw(mobile)
for i,row in enumerate(results[:36]):
 y=13+i*117
 mobile.paste(row["small"],(16,y))
 label=row["header"]+" · "+row["keyword"]
 MD.text((137,y+19),label,font=ft(26),fill="#1B2430")
 MD.text((137,y+60),"102px 모바일 축소 가독성 QA",font=ft(19),fill="#66717D")
mobile.save(OUT/"PILOT_102PX_MOBILE.jpg",quality=87,optimize=True)
for row in results:del row["small"]
report={"status":"PASS_150_JPEG_SQUARE_PILOT_QA" if len(results)==150 and not issues else "HOLD_PILOT_NEEDS_REVIEW",
 "rendered":len(results),"sample_selection":"23 intents + 6 hubs + regional ready + long station labels + stable random sample",
 "size":[1200,1200],"test_mobile_width_px":102,
 "max_jpeg_bytes":max(x["bytes"] for x in results),"avg_jpeg_bytes":int(statistics.mean(x["bytes"] for x in results)),
 "total_bytes":sum(x["bytes"] for x in results),"estimated_21964_file_bytes":round(statistics.mean(x["bytes"] for x in results)*21964),
 "issues":issues[:70],"production_changed":False,"full_21964_images_rendered":False}
(OUT/"PILOT_150_IMAGE_QA_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
(OUT/"PILOT_150_IMAGE_ROWS.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("ENPT_THUMBNAIL_PILOT_IMAGE_QA",json.dumps(report,ensure_ascii=False),flush=True)
if issues or len(results)!=150:raise SystemExit("HOLD pilot visual centering / layout / compression")
