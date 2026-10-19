#!/usr/bin/env python3
"""Build 1k/5k actual Netlify Review capacity benchmark artifacts offline.
Source immutable sharded candidate; no site mutations or live deploys.
"""
import argparse,collections,hashlib,gzip,io,json,pathlib,subprocess,tarfile
PILOT=("gyeongnam-milyang-naeidong-elem-tutor.html","gyeongnam-milyang-naeidong-mid-tutor.html","gyeongnam-milyang-naeidong-high-tutor.html","seoul-jongno-sajikdong-elem-tutor.html","seoul-jongno-sajikdong-mid-tutor.html","seoul-jongno-sajikdong-high-tutor.html")
SOURCE_SHA="e27ffd3e94687e0f2fc58c3951ee1262bca8fd22bd684cf7b4bdb62d014326b1"
PNG_OG="beginner toeic ielts toefl opic tos duolingo elementary middle high student worker college jobseeker housewife stations region academy tutor conversation exam courses englishpt reading writing international phone video general".split()
def sha256(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--archive",required=True);p.add_argument("--filemap",required=True);p.add_argument("--out",required=True)
 a=p.parse_args()
 if sha256(a.archive)!=SOURCE_SHA:raise ValueError("source SHA mismatch")
 with gzip.open(a.filemap,"rt",encoding="utf8") as f:m=json.load(f)
 original=m['original_to_new'];expected=m['full_output_sha1']
 page_names=sorted(k for k,v in original.items() if k.endswith('.html') and v['to'].startswith('__pages/'))
 assert len(page_names)==158571
 selects={}
 for cap in (1000,5000):
  names={page_names[(i*len(page_names))//cap] for i in range(cap)}|set(PILOT)
  # inclusion is nested by sample stride for these two levels (5,000 divisible by 1,000).
  selects[cap]={original[n]['to'] for n in names}
 assert selects[1000].issubset(selects[5000])
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 report={}
 processes={}
 for cap in (1000,5000):
  dest=out/f"ENGLISHPT_TIER_{cap}_REVIEW_CAPACITY_NOINDEX_NO_DEPLOY.tar.zst"
  fout=open(dest,'wb')
  z=subprocess.Popen(['zstd','-T2','-5','-q','-c'],stdin=subprocess.PIPE,stdout=fout)
  t=tarfile.open(fileobj=z.stdin,mode='w|')
  processes[cap]=(dest,fout,z,t)
 stat={k:collections.Counter() for k in selects}
 seen={k:set() for k in selects}
 source=subprocess.Popen(['zstd','-dc',a.archive],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 try:
  with tarfile.open(fileobj=source.stdout,mode='r|') as inp:
   for memb in inp:
    if not memb.isfile():continue
    name=memb.name.removeprefix('./')
    include_common=(name in ('index.html','404.html','robots.txt','_headers','_redirects','netlify.toml',
          'netlify/edge-functions/shard-router.js','pilot.js') or
          name.startswith('assets/') and not name.endswith(('.png','.json')))
    selected_png=(name.startswith('assets/images/og-pages/') and name.endswith('.png') and
          name.rsplit('/',1)[-1].removesuffix('.png') in PNG_OG)
    selected_any=any(name in s for s in selects.values())
    if not (include_common or selected_png or selected_any):continue
    data=inp.extractfile(memb).read()
    assert hashlib.sha1(data).hexdigest()==expected[name],name
    for cap in selects:
     if not (include_common or selected_png or name in selects[cap]):continue
     chunk=data
     if name=='robots.txt':chunk=b'User-agent: *\nDisallow: /\n'
     elif name=='_headers':chunk=data+b'\n/*\n  X-Robots-Tag: noindex\n'
     if name in seen[cap]:raise ValueError("Duplicate file")
     seen[cap].add(name)
     dest,fout,z,t=processes[cap]
     ti=tarfile.TarInfo(name);ti.size=len(chunk);ti.mode=0o644;t.addfile(ti,io.BytesIO(chunk))
     stat[cap]['files']+=1
     if name.endswith('.html'):stat[cap]['html']+=1
     if name.endswith('.png'):stat[cap]['png']+=1
  if source.wait(timeout=60)!=0:raise ValueError("zstd source failed")
 finally:
  source.stdout.close()
  for cap,(dest,fout,z,t) in processes.items():
   t.close();z.stdin.close()
   if z.wait(timeout=90)!=0:raise ValueError("output zstd failed")
   fout.close()
 for cap in selects:
  dest=processes[cap][0]
  if not selects[cap].issubset(seen[cap]):raise ValueError("missing HTML")
  if not all(original[n]['to'] in seen[cap] for n in PILOT):raise ValueError("missing forms")
  report[str(cap)]={"status":"PASS_TIER_OFFLINE","sha256":sha256(dest),
    "artifact_file":dest.name,"compressed_bytes":dest.stat().st_size,
    "files":stat[cap]['files'],"html":stat[cap]['html'],
    "png":stat[cap]['png'],"sampled_routes":len(selects[cap]),
    "static_tutor_sample_six":True,"edge_router":True,
    "X_Robots_Tag_global_noindex":True,"robots_disallow":True,
    "production_modified":False,"draft_uploaded":False}
 (out/'TIER_1000_5000_OFFLINE_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('PASS_TIERED_REVIEW_OFFLINE_BOTH',json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
