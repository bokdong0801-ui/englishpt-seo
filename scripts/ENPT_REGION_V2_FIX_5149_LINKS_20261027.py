#!/usr/bin/env python3
"""ENPT Region V2: rewrite ALL 5149 broken bare-dong hrefs to live course choices.
Run only AFTER the V1 frozen-source builder and immutable core-page integration.
Writes only nonpublished region-review-site/ and evidence; never Production.
"""
from __future__ import annotations
import csv,json,re,collections
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"region-review-site"
OUT=ROOT/"region-review-evidence"
EXPECTED=5149
COURSES=(
 ("elem-tutor","초등 영어과외"),
 ("elem-conv","초등 영어회화"),
 ("mid-tutor","중등 영어과외"),
 ("mid-conv","중등 영어회화"),
 ("high-tutor","고등 영어과외"),
 ("high-conv","고등 영어회화"),
 ("worker-english-conv-academy","직장인 영어회화"),
)
BAD_LINK_RE=re.compile(r'<a href="https://englishpt\.kr/([a-z0-9-]+)\.html" data-locality="([a-z0-9-]+)" title="([^"]*)">([^<]*)</a>')
FILTER=r"""<script id="enpt-region-v2-filter">
(function(){
const box=document.getElementById('rgSearch');if(!box)return;
const all=Array.from(document.querySelectorAll('.rg-district'));
const empty=document.getElementById('rgEmpty');
box.addEventListener('input',()=>{
 const q=box.value.trim().normalize('NFC').toLocaleLowerCase('ko');
 let hits=0;
 for(const district of all){
  const matchDistrict=(district.dataset.district||'').normalize('NFC').toLocaleLowerCase('ko').includes(q);
  let visibleTowns=0;
  for(const town of district.querySelectorAll('.rg-town')){
   const name=(town.dataset.town||'').normalize('NFC').toLocaleLowerCase('ko');
   const shown=!q||matchDistrict||name.includes(q);
   town.hidden=!shown;
   if(shown){visibleTowns++;if(q&&!matchDistrict)town.open=true;else if(!q)town.open=false}
  }
  district.hidden=visibleTowns===0;
  if(visibleTowns){hits++;if(q)district.open=true}
 }
 if(empty)empty.style.display=hits?'none':'block';
});
})();
</script>"""
STYLE=r"""<style id="enpt-region-v2-choices-css">
.rg-town-links{align-items:start}
.rg-town{background:#f4f7f3;border:1px solid #dce8df;border-radius:11px;min-width:0;overflow:hidden}
.rg-town[hidden],.rg-district[hidden]{display:none!important}
.rg-town summary{list-style:none;display:flex;align-items:center;gap:7px;justify-content:space-between;padding:12px 12px;cursor:pointer;color:#214833;font-weight:750;line-height:1.5;min-height:47px}
.rg-town summary::-webkit-details-marker{display:none}
.rg-town summary:hover,.rg-town summary:focus-visible{background:#e3ede4}
.rg-town summary:focus-visible{outline:3px solid #367a56;outline-offset:-3px}
.rg-town summary:after{content:'+';font-size:19px;color:#236347}
.rg-town[open] summary:after{content:'−'}
.rg-choices{display:grid;grid-template-columns:1fr;gap:5px;padding:7px 9px 11px;background:#fff;border-top:1px solid #dfebe2}
.rg-choices a{display:block;border-radius:7px;padding:8px 10px!important;background:#eef4ed!important;text-decoration:none!important;color:#1e5034!important;font-size:13px!important;font-weight:600}
.rg-choices a:hover,.rg-choices a:focus-visible{background:#d7e9d9!important;outline-color:#3b8057}
.rg-course-note{font-size:12px;color:#5c7363;margin-top:8px}
@media(min-width:1000px){.rg-town-links{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:640px){.rg-town-links{grid-template-columns:1fr!important}.rg-town summary{padding:13px 14px}.rg-choices{grid-template-columns:repeat(2,minmax(0,1fr))}.rg-choices a{font-size:12px!important;line-height:1.5}}
</style>"""
def main():
 assert SITE.joinpath("regions.html").exists(),"HOLD_FIRST_GENERATE_V1"
 provinces=sorted(SITE.glob("regions/*.html"))
 assert len(provinces)==17
 seen={};items=[];stats=[]
 for p in provinces:
  source=p.read_text("utf8")
  def convert(match):
   slug,identity,full,dong=match.groups()
   assert slug==identity,("HOLD_SLUG_COLLISION",slug,identity)
   assert slug not in seen,("HOLD_DUPLICATE_TOWN",slug)
   seen[slug]=str(p)
   links=[]
   for suffix,label in COURSES:
    target=f"https://englishpt.kr/{slug}-{suffix}.html"
    links.append(f'<a href="{target}" data-course="{suffix}" title="{escape(full)} {label}">{label}</a>')
    items.append({"region_slug":slug,"region_full":full,"province_file":p.name,"course":suffix,"target_url":target})
   return (f'<details class="rg-town" data-town="{escape(dong)}" data-locality="{slug}">'
       f'<summary>{escape(dong)}<span class="rg-course-note">과정 선택</span></summary>'
       f'<div class="rg-choices">{"".join(links)}</div></details>')
  transformed,count=BAD_LINK_RE.subn(convert,source)
  if not count:raise RuntimeError("HOLD_NO_TOWN_LINKS "+str(p))
  assert "enpt-region-filter" in transformed
  transformed=re.sub(r'<script id="enpt-region-filter">[\s\S]*?</script>',lambda m:FILTER,transformed,count=1)
  transformed=transformed.replace("</head>",STYLE+"</head>",1)
  assert len(re.findall(r'<details class="rg-town" ',transformed))==count
  assert 'data-locality="' in transformed
  assert '<meta name="robots" content="noindex,nofollow">' in transformed
  assert "englishpt-consultation" in transformed
  assert not BAD_LINK_RE.search(transformed)
  p.write_text(transformed,"utf8")
  stats.append({"province":p.stem,"towns":count,"course_links":count*len(COURSES),"html_bytes":p.stat().st_size})
 assert len(seen)==EXPECTED,(len(seen),EXPECTED)
 assert len(items)==EXPECTED*len(COURSES),(len(items),EXPECTED*len(COURSES))
 assert len({x["target_url"] for x in items})==len(items)
 assert sum(x["towns"] for x in stats)==EXPECTED
 OUT.mkdir(exist_ok=True)
 with (OUT/"ENPT_V2_5149_X_7_REAL_COURSE_LINKS.csv").open("w",newline="",encoding="utf-8-sig") as f:
  w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
 summary={"status":"PASS_V2_BARE_404_LINKS_REPLACED","towns":len(seen),"original_bare_town_links_remaining":0,"actual_course_anchors":len(items),"types":[x[0] for x in COURSES],"provinces":len(provinces),"static_target_duplicates":0,"draft_only":True,"production_file_modifications":0,"form_posts":0,"province_stats":stats}
 (OUT/"ENPT_V2_RELINK_STATIC_QA.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),"utf8")
 print("ENPT_V2_RELINK_STATIC_QA",json.dumps({k:v for k,v in summary.items() if k!="province_stats"},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
