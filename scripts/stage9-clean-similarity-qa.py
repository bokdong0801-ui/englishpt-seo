#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json, math, re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

INTENTS=[
 "elem-tutor","mid-conv","high-conv","univ-conv","jobseeker-conv",
 "biz-business-conv","housewife-conv","toeic","toeic-speaking","opic",
 "ielts","duolingo","toefl",
 "toeic-academy","toeic-speaking-academy","opic-academy","ielts-academy","duolingo-academy","toefl-academy",
 "english-conv-academy","adult-english-conv-academy","worker-english-conv-academy","beginner-english-conv"
]
TAG_RE=re.compile(r"<script.*?</script>|<style.*?</style>|<[^>]+>",re.S|re.I)
TOK_RE=re.compile(r"[가-힣A-Za-z0-9]+")

def visible(raw:str)->str:
    # Compare substantive page copy, not repeated site chrome or navigation clusters.
    # Regional cross-navigation intentionally repeats course labels and nearby links
    # across pages; counting those links would inflate similarity without indicating
    # duplicate editorial content.
    cleaned=raw
    for pattern in (
        r"<header\b.*?</header>",
        r"<footer\b.*?</footer>",
        r'<div class="form-modal".*?</div></body>',
        r'<div class="mobile-sticky".*?</div>',
        r'<section class="section related[^"]*".*?</section>',
        r'<section class="section soft region-navigation[^"]*".*?</section>',
    ):
        cleaned=re.sub(pattern," ",cleaned,flags=re.S|re.I)
    return re.sub(r"\s+"," ",html.unescape(TAG_RE.sub(" ",cleaned))).strip()

def tokens(text:str)->Counter:
    toks=[t.lower() for t in TOK_RE.findall(text) if len(t)>1]
    return Counter(toks)

def cosine(a:Counter,b:Counter)->float:
    common=set(a)&set(b)
    num=sum(a[k]*b[k] for k in common)
    da=math.sqrt(sum(v*v for v in a.values()))
    db=math.sqrt(sum(v*v for v in b.values()))
    return num/(da*db) if da and db else 0.0

def shingles(text:str,n:int=5)->set[tuple[str,...]]:
    toks=[t.lower() for t in TOK_RE.findall(text) if len(t)>1]
    return {tuple(toks[i:i+n]) for i in range(max(0,len(toks)-n+1))}

def jac(a:set,b:set)->float:
    u=a|b
    return len(a&b)/len(u) if u else 0.0

def intent_of(name:str)->str|None:
    for intent in sorted(INTENTS,key=len,reverse=True):
        if name.endswith(f"-{intent}.html"):
            return intent
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--samples-per-intent",type=int,default=60)
    ap.add_argument("--output",default="")
    args=ap.parse_args()
    root=Path(args.root)
    grouped=defaultdict(list)
    for p in sorted(root.glob("*.html")):
        intent=intent_of(p.name)
        if intent: grouped[intent].append(p)

    result={"status":"PASS","samples_per_intent":args.samples_per_intent,"intents":{},"max_cosine":0.0,"max_jaccard5":0.0,"failures":[]}
    for intent in INTENTS:
        files=grouped[intent]
        if len(files)<2:
            result["failures"].append({"intent":intent,"reason":"too_few_pages","count":len(files)})
            continue
        n=min(args.samples_per_intent,len(files))
        idxs=sorted(set(round(i*(len(files)-1)/(n-1)) for i in range(n))) if n>1 else [0]
        docs=[]
        for i in idxs:
            p=files[i]
            txt=visible(p.read_text(encoding="utf-8"))
            docs.append((p.name,tokens(txt),shingles(txt)))
        maxc=maxj=0.0; worstc=worstj=None
        for (na,ta,sa),(nb,tb,sb) in combinations(docs,2):
            c=cosine(ta,tb); j=jac(sa,sb)
            if c>maxc:maxc,worstc=c,(na,nb)
            if j>maxj:maxj,worstj=j,(na,nb)
        result["intents"][intent]={
            "available":len(files),"sampled":len(docs),
            "max_cosine":round(maxc,6),"cosine_pair":worstc,
            "max_jaccard5":round(maxj,6),"jaccard_pair":worstj,
        }
        result["max_cosine"]=max(result["max_cosine"],maxc)
        result["max_jaccard5"]=max(result["max_jaccard5"],maxj)
    result["max_cosine"]=round(result["max_cosine"],6)
    result["max_jaccard5"]=round(result["max_jaccard5"],6)
    # This is a human-review diagnostic. Stage 6 proved the source corpus thresholds;
    # Stage 9 clean rendering is additionally flagged if near-identical pages remain.
    if result["max_cosine"]>=0.94 or result["max_jaccard5"]>=0.65:
        result["status"]="FAIL_NEAR_IDENTICAL_STAGE9_RENDER"
        result["failures"].append({
            "reason":"near_identical_render",
            "cosine_gate_lt":0.94,
            "jaccard5_gate_lt":0.65
        })
    if args.output:
        Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    if result["status"]!="PASS":
        raise SystemExit(1)

if __name__=="__main__":
    main()
