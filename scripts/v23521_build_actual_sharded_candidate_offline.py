#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create ACTUAL new sharded v23.5.2.1 site .tar.zst, full asset checksums, Edge code.
Strictly OFFLINE. Never Netlify deploy, upload, access credentials or submit forms.
"""
import argparse,collections,datetime,gzip,hashlib,io,json,os,pathlib,re,subprocess,sys,tarfile
EXPECTED="e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba"
EDGE_TEMPLATE=r'''// ENGLISH PT v23.5.2.1 — internally rewrite preserved public SEO .html routes.
// Source files physically stored under /__pages/XX/original.html, never a redirect.
const legacyRedirectPaths = new Set(__LEGACY_REDIRECTS__);
export function fnvBucket(filename) {
  const encoded = new TextEncoder().encode(filename);
  let h = 2166136261 >>> 0;
  for (const b of encoded) h = Math.imul(h ^ b, 16777619) >>> 0;
  return (h >>> 24).toString(16).padStart(2, "0");
}
export function rewritePath(pathname) {
  if (!/^\/[^/]+[.]html$/.test(pathname)) return null;
  let file;
  try { file = decodeURIComponent(pathname.slice(1)); }
  catch { return null; }
  if (file === "index.html" || file === "404.html" ||
      file.includes("/") || file.includes("\\") || file.includes("\0")) return null;
  if (legacyRedirectPaths.has("/" + file)) return null;
  return "/__pages/" + fnvBucket(file) + "/" + pathname.slice(1);
}
export default function handler(request) {
  // Allow existing Netlify Forms POST and redirects to proceed untouched.
  if (request.method !== "GET" && request.method !== "HEAD") return;
  const url = new URL(request.url);
  const rewritten = rewritePath(url.pathname);
  if (!rewritten) return;
  url.pathname = rewritten;
  return url;
}
'''
CONFIG_SECTION="\n# v23.5.2.1 sharded HTML edge router; original public URLs preserved.\n[[edge_functions]]\n  function = \"shard-router\"\n  pattern = '^/[^/]+[.]html$'\n"
def bucket(name):
    h=2166136261
    for b in name.encode("utf8"):h=((h^b)*16777619)&0xffffffff
    return f"{h>>24:02x}"
def sha_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()
class HashingReader:
    def __init__(self,source):
        self.source=source;self.sha=hashlib.sha1();self.n=0
    def read(self,n=-1):
        data=self.source.read(n)
        if data:self.sha.update(data);self.n+=len(data)
        return data
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--report",required=True)
    p.add_argument("--manifest",required=True)
    a=p.parse_args()
    if sha_file(a.input)!=EXPECTED:raise ValueError("Frozen v23.5.2.1 candidate SHA256 changed")
    output=pathlib.Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    outfile=open(output,"wb")
    compressor=subprocess.Popen(["zstd","-T2","-5","-q","-c"],stdin=subprocess.PIPE,stdout=outfile)
    source_proc=subprocess.Popen(["zstd","-dc",a.input],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    mapping={};dest_hash={};stat=collections.Counter();dirs=collections.Counter();redirects=[]
    original_redirects=None;original_toml=None;read_root_html=0
    try:
        with tarfile.open(fileobj=source_proc.stdout,mode="r|") as inp:
          with tarfile.open(fileobj=compressor.stdin,mode="w|") as out:
            for member in inp:
                old=member.name.removeprefix("./")
                if member.isdir():continue
                if not member.isfile():raise ValueError("Unexpected tar entry: "+old)
                if not old or old.startswith("/") or ".." in old.split("/"):
                    raise ValueError("Unsafe source name")
                if old=="netlify.toml":
                    original_toml=inp.extractfile(member).read()
                    continue
                if old=="_redirects":
                    original_redirects=inp.extractfile(member).read()
                    content=original_redirects
                    reader=HashingReader(io.BytesIO(content))
                else:
                    reader=HashingReader(inp.extractfile(member))
                new=old
                if "/" not in old and old.endswith(".html") and old not in ("index.html","404.html"):
                    read_root_html+=1
                    new="__pages/"+bucket(old)+"/"+old
                if new in dest_hash:raise ValueError("Collision path: "+new)
                meta=tarfile.TarInfo(new)
                meta.size=member.size;meta.mode=member.mode
                meta.mtime=member.mtime;meta.uid=0;meta.gid=0
                out.addfile(meta,reader)
                if reader.n!=member.size:raise ValueError("Byte truncation: "+old)
                digest=reader.sha.hexdigest()
                dest_hash[new]=digest
                mapping[old]={"to":new,"sha1":digest,"size":member.size}
                stat["files"]+=1;stat["source_bytes"]+=member.size
                if old.endswith(".html"):stat["html"]+=1
                dirs[new.rsplit("/",1)[0] if "/" in new else "(root)"]+=1
                if stat["files"]%30000==0:
                    print("SHARDED_CANDIDATE_BUILD_PROGRESS",stat["files"],read_root_html,flush=True)
            if not original_toml or not original_redirects:
                raise ValueError("Source netlify.toml or _redirects missing")
            if b"[[edge_functions]]" in original_toml:
                raise ValueError("Unexpected pre-existing Edge function declarations, must inspect manually")
            if b'[build]' not in original_toml:
                raise ValueError("Unexpected original netlify.toml")
            for ln in original_redirects.decode("utf8").splitlines():
                words=ln.strip().split()
                if len(words)>=3 and words[0].startswith("/") and words[2].startswith("301"):
                    redirects.append(words[0])
            if len(redirects)<10:raise ValueError("Suspiciously short legacy redirects")
            edge=EDGE_TEMPLATE.replace("__LEGACY_REDIRECTS__",json.dumps(sorted(set(redirects)),ensure_ascii=False)).encode("utf8")
            toml=original_toml+CONFIG_SECTION.encode("utf8")
            for name,content in (("netlify.toml",toml),("netlify/edge-functions/shard-router.js",edge)):
                if name in dest_hash:raise ValueError("Duplicate new code "+name)
                header=tarfile.TarInfo(name);header.size=len(content);header.mode=0o644;header.mtime=0
                out.addfile(header,io.BytesIO(content))
                dest_hash[name]=hashlib.sha1(content).hexdigest()
                dirs[name.rsplit("/",1)[0] if "/" in name else "(root)"]+=1
                stat["new_code_bytes"]+=len(content)
    finally:
        try:source_proc.stdout.close()
        except:pass
        if source_proc.wait(timeout=90)!=0:raise ValueError("Source ZSTD stream failed")
        try:compressor.stdin.close()
        except:pass
        if compressor.wait(timeout=120)!=0:raise ValueError("Output zstd compressor failed")
        outfile.close()
    if stat["files"]!=180797 or read_root_html!=158571 or stat["html"]!=158574:
        raise ValueError("Incorrect source inventory/count: "+str(stat)+" moved:"+str(read_root_html))
    if len(dest_hash)!=180799:raise ValueError("Unexpected output inventory "+str(len(dest_hash)))
    if max(dirs.values())>=54000:raise ValueError("Netlify per-directory max exceeded")
    if dirs["(root)"]!=20:raise ValueError("Unexpected sharded root count "+str(dirs["(root)"]))
    # All source file bytes are hashed while they are streamed verbatim into the new archive.
    # Original netlify.toml excluded and replaced with injected Edge declaration.
    map_path=pathlib.Path(a.manifest);map_path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(map_path,"wt",encoding="utf8",compresslevel=6) as f:
        json.dump({"source_sha256":EXPECTED,"original_to_new":mapping,
                   "full_output_sha1":dest_hash},f,ensure_ascii=False,separators=(",",":"))
    report={"status":"PASS_ACTUAL_SHARDED_CANDIDATE_ARCHIVE_BUILT",
      "produced_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "source_sha256":EXPECTED,
      "new_candidate_sha256":sha_file(output),"new_candidate_archive_bytes":output.stat().st_size,
      "output_regular_files":len(dest_hash),"source_regular_files":stat["files"]+1,
      "original_html":stat["html"],"moved_root_html":read_root_html,
      "output_root_files":dirs["(root)"],"max_files_per_directory":max(dirs.values()),
      "directory_count":len(dirs),"max_directory":max(dirs,key=dirs.get),
      "legacy_redirect_source_routes":len(set(redirects)),
      "source_content_bytes_copied_verbatim":stat["source_bytes"],
      "sha1_mapping_count":len(mapping),
      "netlify_calls":0,"production_deployed":False,"review_draft_deployed":False,
      "added_edge_function":"netlify/edge-functions/shard-router.js",
      "edge_config":"[[edge_functions]] pattern = '^/[^/]+[.]html$'",
      "caveat":"Real Netlify Edge execution and Form detection must be verified in an independently approved Draft before Production."}
    rp=pathlib.Path(a.report);rp.parent.mkdir(parents=True,exist_ok=True)
    rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("PASS_ACTUAL_SHARDED_SITE_GENERATED",json.dumps(report,ensure_ascii=False),flush=True)
    return 0
if __name__=="__main__":sys.exit(main())
