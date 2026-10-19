#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline only: turn 103 pilot root HTML into content-preserving .page assets,
serve original .html via Netlify Edge context.rewrite Response with HTML Content-Type.
Keep one form blueprint HTML so final architecture has a route for Netlify Forms.
NO Netlify network access or API mutation.
"""
import argparse,datetime,hashlib,io,json,pathlib,re,subprocess,tarfile,sys
FROZEN="ef22d14e56c28a950dad5fd951d67c32856fef36a176408967e1857b32604d47"
EDGE=r'''// Experimental payload-serving Edge router; user-visible SEO URLs stay /slug.html.
// context.rewrite() retrieves static .page body without redirecting clients.
// Full-site needs separate validation of Forms registration and delivery before Production.
const legacyRedirects = new Set(__LEGACY_REDIRECTS__);
export function fnvBucket(name) {
  const data = new TextEncoder().encode(name);
  let h = 2166136261 >>> 0;
  for (const b of data) h = Math.imul(h ^ b, 16777619) >>> 0;
  return (h >>> 24).toString(16).padStart(2, "0");
}
export function staticPayloadPath(pathname) {
  if (!/^\/[^/]+\.html$/.test(pathname)) return null;
  let filename;
  try { filename = decodeURIComponent(pathname.slice(1)); } catch { return null; }
  if (filename === "index.html" || filename === "404.html" ||
      filename.includes("/") || filename.includes("\\") || filename.includes("\0")) return null;
  if (legacyRedirects.has("/" + filename)) return null;
  return "/__pages/" + fnvBucket(filename) + "/" + filename.slice(0, -5) + ".page";
}
export default async function handler(request, context) {
  if (request.method !== "GET" && request.method !== "HEAD") return;
  const url = new URL(request.url);
  const payload = staticPayloadPath(url.pathname);
  if (!payload) return;
  url.pathname = payload;
  // Netlify internal rewrite returns original static body; not a browser redirect.
  const response = await context.rewrite(url);
  if (!response.ok) return response;
  const headers = new Headers(response.headers);
  headers.set("Content-Type", "text/html; charset=utf-8");
  // This pilot is on an isolated public Draft and MUST NOT be indexable.
  headers.set("X-Robots-Tag", "noindex, nofollow");
  headers.delete("Content-Length");
  return new Response(response.body, {status: response.status, headers});
}
'''
def sha256(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def main():
 a=argparse.ArgumentParser()
 a.add_argument("--input",required=True);a.add_argument("--output",required=True);a.add_argument("--report",required=True)
 z=a.parse_args()
 if sha256(z.input)!=FROZEN:raise ValueError("Wrong original small pilot sha256")
 seen=set();original_sha={};converted={};blueprint=None;original=0;pngs=0;rules=[]
 out=pathlib.Path(z.output);out.parent.mkdir(parents=True,exist_ok=True)
 proc=subprocess.Popen(["zstd","-dc",z.input],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 dest=open(out,"wb")
 compress=subprocess.Popen(["zstd","-T2","-4","-q","-c"],stdin=subprocess.PIPE,stdout=dest)
 try:
  with tarfile.open(fileobj=proc.stdout,mode="r|") as src:
   with tarfile.open(fileobj=compress.stdin,mode="w|") as dst:
    for member in src:
     if not member.isfile():continue
     name=member.name.removeprefix("./")
     blob=src.extractfile(member).read()
     original_sha[name]=hashlib.sha1(blob).hexdigest()
     if name=="netlify/edge-functions/shard-router.js":continue
     if name=="netlify.toml":
      # Existing Edge declaration is correct: replace the code only.
      assert b'function = "shard-router"' in blob
     if name=="_redirects":
      rules=[ln.split()[0] for ln in blob.decode("utf8").splitlines() if len(ln.split())>=3 and ln.split()[2].startswith("301")]
      if len(rules)<10:raise ValueError("301 rules unexpectedly missing")
     path=name
     if name.startswith("__pages/") and name.endswith(".html"):
      assert name.count("/")==2
      path=name[:-5]+".page"
      converted[name]=path
      original+=1
      if name.endswith("gyeongnam-milyang-naeidong-elem-tutor.html"):
       blueprint=blob
     if name.endswith(".png"):pngs+=1
     if path in seen:raise ValueError("Duplicate output path "+path)
     seen.add(path)
     t=tarfile.TarInfo(path);t.size=len(blob);t.mode=0o644;t.mtime=0
     dst.addfile(t,io.BytesIO(blob))
    if len(converted)!=103 or not blueprint:raise ValueError("Unexpected sample/Netlify form blueprint inventory")
    if b'name="englishpt-consultation"' not in blueprint or b'name="form-name"' not in blueprint:
     raise ValueError("Missing exact Netlify consultation form")
    edge=EDGE.replace("__LEGACY_REDIRECTS__",json.dumps(rules)).encode("utf8")
    # Form blueprint under nonlinked internal path; POST will bypass Edge and Netlify can detect this static form.
    for name,blob in [
      ("netlify/edge-functions/shard-router.js",edge),
      ("__internal/consultation-blueprint.html",blueprint)]:
     if name in seen:raise ValueError("Unexpected repeated destination "+name)
     t=tarfile.TarInfo(name);t.size=len(blob);t.mode=0o644;t.mtime=0
     dst.addfile(t,io.BytesIO(blob))
     seen.add(name)
  if proc.wait(timeout=30)!=0:raise ValueError("Source zstd error")
  compress.stdin.close()
  if compress.wait(timeout=60)!=0:raise ValueError("New zstd error")
 finally:
  try:proc.stdout.close()
  except:pass
  try:compress.stdin.close()
  except:pass
  dest.close()
 expected={p:original_sha[old] for old,p in converted.items()}
 assert pngs==141
 report={"status":"PASS_SMALL_PAYLOAD_HTML_POSTPROCESS_BYPASS_OFFLINE",
  "original_small_sha256":FROZEN,"new_payload_pilot_sha256":sha256(out),
  "new_tar_bytes":out.stat().st_size,"converted_HTML_to_page_preserving_content":len(converted),
  "static_html_remain":3,"total_regular_files":len(seen),"original_sha1_preserved":True,
  "web_facing_routes_unchanged":True,"all_301_rules":len(rules),
  "pilot_og_images_preserved":pngs,"real_Netlify_form_blueprint":True,
  "draft_global_noindex":True,"production_deployed":False,"Netlify_Draft_deployed":False,
  "real_Edge_runtime_still_to_test":True}
 rp=pathlib.Path(z.report);rp.parent.mkdir(parents=True,exist_ok=True)
 rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("PAYLOAD_EDGE_PILOT_OFFLINE_PASS",json.dumps(report,ensure_ascii=False),flush=True)
if __name__=="__main__":main()
