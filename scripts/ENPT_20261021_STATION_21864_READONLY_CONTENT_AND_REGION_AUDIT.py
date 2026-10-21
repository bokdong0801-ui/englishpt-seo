#!/usr/bin/env python3
"""ENPT 2026-10-21 source-only station audit. No Netlify/production writes."""
import csv,hashlib,heapq,json,os,pathlib,re,subprocess,tarfile,zlib
from collections import Counter,defaultdict
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=pathlib.Path("readonly-station-audit");OUT.mkdir(exist_ok=True)
SRC=pathlib.Path("frozen-source/ENGLISHPT_v23.5.2.1_SHARDED_EDGE_NEW_CANDIDATE_NOT_DEPLOYED.tar.zst")
SHA="e27ffd3e94687e0f2fc58c3951ee1262bca8fd22bd684cf7b4bdb62d014326b1"
ST=json.loads((ROOT/"data/stations.json").read_text(encoding="utf8"))["stations"]
INTENTS="elem-tutor mid-conv high-conv univ-conv jobseeker-conv biz-business-conv housewife-conv toeic toeic-speaking opic ielts duolingo toefl toeic-academy toeic-speaking-academy opic-academy ielts-academy duolingo-academy toefl-academy english-conv-academy adult-english-conv-academy worker-english-conv-academy beginner-english-conv".split()
assert len(ST)==911 and len(INTENTS)==23
def csvout(name,rows,fields):
 with (OUT/name).open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
# These are CANDIDATE province inferences from unambiguous area names, not corrected live site data.
provmap={}
for prov,names in {
"경기도":"의정부시 구리시 김포시 광주시 과천시 안산시 광명시 군포시 안양시 부천시 고양시 파주시 남양주시 시흥시 오산시 수원시 화성시 용인시 성남시 하남시 양주시 동두천시 포천시 이천시 여주시 평택시 안성시 의왕시 가평군 양평군 연천군",
"강원특별자치도":"춘천시 강릉시 원주시 동해시 태백시 속초시 삼척시 홍천군 횡성군 영월군 평창군 정선군 철원군 화천군 양구군 인제군 고성군 양양군",
"충청북도":"청주시 충주시 제천시 증평군 진천군 음성군 괴산군 단양군 보은군 옥천군 영동군",
"충청남도":"천안시 아산시 공주시 보령시 서산시 논산시 계룡시 당진시 금산군 부여군 서천군 청양군 홍성군 예산군 태안군",
"경상북도":"경산시 구미시 경주시 김천시 안동시 영주시 영천시 상주시 문경시 포항시 칠곡군 청도군",
"경상남도":"김해시 양산시 창원시 진주시 사천시 거제시 통영시 밀양시 함안군",
"전북특별자치도":"전주시 익산시 군산시 김제시 정읍시 남원시 완주군",
"전라남도":"목포시 여수시 순천시 광양시 나주시 무안군"
}.items():
 for name in names.split():provmap[name]=prov
for short in ("서울","부산","대구","인천","광주","대전","세종","울산"):provmap[short]=short
for key,short in [("서울특별시","서울"),("부산광역시","부산"),("대구광역시","대구"),("인천광역시","인천"),("광주광역시","광주"),("대전광역시","대전"),("울산광역시","울산"),("세종특별자치시","세종")]:provmap[key]=short
regions=[]
for st in ST:
 city=st.get("city") or "";area=(st.get("areas") or [""])[0] if st.get("areas") else ""
 candidate=provmap.get(area,"")
 if not city or not area:status="행정구역_누락";priority="P1"
 elif candidate and candidate!=city:status="시도_불일치_후보";priority="P0"
 elif not candidate:status="시군구_상위시도_대조필요";priority="P2"
 else:status="기준상_이상없음";priority="OK"
 regions.append({"역명":st["name"],"slug":st["slug"],"기존_city":city,"기존_areas":area,"후보_시도":candidate if candidate!=city else "","노선":"|".join(st.get("lines") or []),"위도":st.get("lat"),"경도":st.get("lng"),"문제유형":status,"우선순위":priority,"실주소_교차확인":"필수" if priority!="OK" else "해당없음","원본_URL":"https://github.com/bokdong0801-ui/englishpt-seo/blob/ops/v23521-OG21964-APPROVED-PUBLISH-EXACT-DRAFT-ONCE-20261020/data/stations.json"})
csvout("ALL_911_REGION_AUDIT.csv",regions,list(regions[0]))
csvout("REGION_CORRECTION_CANDIDATES_ONLY.csv",[r for r in regions if r["우선순위"]!="OK"],list(regions[0]))
class MainP(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.depth=0;self.cap=None;self.parts=[];self.paras=[]
 def handle_starttag(self,t,a):
  if t=="main":self.depth+=1
  if self.depth and self.cap is None and t in ("p","h2","h3","li"):self.cap=t;self.parts=[]
 def handle_endtag(self,t):
  if self.depth and t==self.cap:
   p=re.sub(r"\s+"," ","".join(self.parts)).strip()
   if len(p)>=34:self.paras.append(p)
   self.cap=None
  if t=="main":self.depth=max(0,self.depth-1)
 def handle_data(self,d):
  if self.depth and self.cap:self.parts.append(d)
def norm(p,st):
 for x in [st.get("name"),st.get("city"),*(st.get("areas") or [])]:
  if x and len(x)>1:p=p.replace(x,"[지역]")
 return re.sub(r"\s+"," ",p).strip()
def sig(ps):
 ts=re.findall(r"[가-힣A-Za-z0-9]+"," ".join(ps).lower())
 hs={zlib.crc32(" ".join(ts[i:i+5]).encode()) for i in range(max(0,len(ts)-4))}
 return frozenset(heapq.nsmallest(256,hs))
def sim(a,b):return len(a&b)/max(1,min(len(a),len(b))) if a and b else 0.0
look={}
for st in ST:
 base="station-"+st["slug"];look[base+".html"]=(st,"hub")
 for intent in INTENTS:look[base+"-"+intent+".html"]=(st,intent)
assert len(look)==21864
if not SRC.exists():raise SystemExit("Frozen archive not present")
sha=hashlib.sha256()
with SRC.open("rb") as fh:
 for b in iter(lambda:fh.read(4*1024*1024),b""):sha.update(b)
if sha.hexdigest()!=SHA:raise SystemExit("Frozen SOURCE sha256 mismatch: "+sha.hexdigest())
records={};counts=Counter();normalized_groups=defaultdict(list)
proc=subprocess.Popen(["zstd","-dc",str(SRC)],stdout=subprocess.PIPE)
with tarfile.open(fileobj=proc.stdout,mode="r|") as tar:
 for member in tar:
  if not member.isfile():continue
  name=pathlib.PurePosixPath(member.name).name
  if name not in look:continue
  if name in records:raise RuntimeError("duplicate archive member: "+name)
  st,intent=look[name];data=tar.extractfile(member).read()
  p=MainP();p.feed(data.decode("utf8","replace"))
  paragraphs=[norm(x,st) for x in p.paras]
  ph=[hashlib.sha1(x.encode()).hexdigest() for x in paragraphs]
  counts.update(set(ph))
  dh=hashlib.sha256(" ".join(paragraphs).encode()).hexdigest()
  normalized_groups[dh].append(name)
  records[name]={"st":st["slug"],"intent":intent,"sig":sig(paragraphs),"ph":ph,"lens":list(map(len,paragraphs)),"sha":dh,"url":"https://englishpt.kr/"+name.removesuffix(".html")+".html"}
  if len(records)%5000==0:print("PROGRESS_EXACT_SOURCE_HTML",len(records),flush=True)
proc.stdout.close()
if proc.wait():raise RuntimeError("zstd failed")
if set(records)!=set(look):raise RuntimeError("Missing station HTML "+str(len(set(look)-set(records)))+" found="+str(len(records)))
by_st=defaultdict(list);by_intent=defaultdict(list)
for name,r in records.items():by_st[r["st"]].append(name);by_intent[r["intent"]].append(name)
out=[]
for name,p in records.items():
 same=[(sim(p["sig"],records[n]["sig"]),n) for n in by_st[p["st"]] if n!=name]
 closest=max(same,default=(0,""))
 pool=by_intent[p["intent"]]
 anchors=list(dict.fromkeys([pool[0],pool[len(pool)//4],pool[len(pool)//2],pool[3*len(pool)//4],pool[-1]]))
 cross=max(((sim(p["sig"],records[n]["sig"]),n) for n in anchors if n!=name),default=(0,""))
 allchars=sum(p["lens"])
 common=sum(sz for h,sz in zip(p["ph"],p["lens"]) if counts[h]>=10)/max(1,allchars)
 flags=[]
 if closest[0]>=.72:flags.append("동일역_다른과정_고유사")
 if cross[0]>=.83:flags.append("타역_동일과정_고유사")
 if common>=.80 and allchars>=800:flags.append("10개URL이상_반복문단80퍼센트")
 if len(normalized_groups[p["sha"]])>1:flags.append("지역정규화_본문완전일치")
 if len(p["ph"])<5:flags.append("본문_추출문단부족")
 out.append({"URL":p["url"],"역슬러그":p["st"],"과정":p["intent"],"문단수":len(p["ph"]),"본문문자":allchars,"반복문단비중":round(common,4),"동일역최대유사도":round(closest[0],4),"동일역비교URL":records[closest[1]]["url"] if closest[1] else "","다른역5개표본최대유사도":round(cross[0],4),"비교_표본_URL":records[cross[1]]["url"] if cross[1] else "","플래그":"|".join(flags),"판정":"REVIEW" if flags else "PASS_SCREEN"})
fields=list(out[0]);flagged=[x for x in out if x["판정"]=="REVIEW"]
csvout("ALL_21864_HTML_METRICS.csv",out,fields)
csvout("PROBLEM_URLS_ONLY.csv",flagged,fields)
summary={"status":"PASS_SOURCE_ONLY_21864_HTML_AUDITED","source_original_sha256":SHA,"stations":len(ST),"urls_examined":len(records),"urls_flagged":len(flagged),"flags":dict(Counter(f for x in flagged for f in x["플래그"].split("|"))),"station_admin_candidates":sum(r["우선순위"]!="OK" for r in regions),"admin_types":dict(Counter(r["문제유형"] for r in regions)),"method":"All 21864 checked against 23 same-station peers and 5 same-intent cross-station anchors, normalized repeated paragraphs; not exhaustive all-pairs, not Google duplicate adjudication","published_or_original_modified":False}
(OUT/"AUDIT_SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
print("AUDIT_FINAL_RESULT",json.dumps(summary,ensure_ascii=False),flush=True)
