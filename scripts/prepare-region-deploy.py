from __future__ import annotations
import json, os, re, shutil, subprocess, sys, time, urllib.request, zipfile
from pathlib import Path

ARTIFACT_URL = 'https://api.github.com/repos/bokdong0801-ui/korea-region-db/actions/artifacts/10381378865/zip'
BUILD = Path('.region-build')
PARTS = Path('scripts/region-build-parts')
LOCAL_ZIP = os.environ.get('REGION_V5_ZIP','').strip()


def log(msg):
    print(f'[region-deploy] {msg}', flush=True)


def download_artifact(dest: Path):
    if LOCAL_ZIP:
        src=Path(LOCAL_ZIP)
        if not src.exists(): raise FileNotFoundError(src)
        shutil.copy2(src,dest)
        log(f'using local V5 zip: {src}')
        return
    headers={'User-Agent':'englishpt-netlify-region-builder/1.0','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    last=None
    for attempt in range(1,4):
        try:
            req=urllib.request.Request(ARTIFACT_URL,headers=headers)
            with urllib.request.urlopen(req,timeout=120) as r, dest.open('wb') as f:
                shutil.copyfileobj(r,f)
            if dest.stat().st_size < 1000: raise RuntimeError('artifact download unexpectedly small')
            log(f'downloaded V5 artifact: {dest.stat().st_size:,} bytes')
            return
        except Exception as e:
            last=e
            log(f'artifact download attempt {attempt}/3 failed: {e}')
            if attempt<3: time.sleep(3*attempt)
    raise RuntimeError(f'cannot download public V5 artifact: {last}')


def concat_parts(stem: str, dest: Path):
    parts=sorted(PARTS.glob(stem+'.part*'))
    if not parts: raise FileNotFoundError(f'no parts for {stem}')
    with dest.open('w',encoding='utf-8') as out:
        for p in parts: out.write(p.read_text(encoding='utf-8'))
    subprocess.run([sys.executable,'-m','py_compile',str(dest)],check=True)
    log(f'assembled {stem} from {len(parts)} parts')


def copytree_clean(src: Path, dst: Path):
    if dst.exists(): shutil.rmtree(dst)
    shutil.copytree(src,dst)


def count_locs(path: Path):
    return len(re.findall(r'<loc>.*?</loc>',path.read_text(encoding='utf-8'),re.S))


def main():
    if BUILD.exists(): shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    source_zip=BUILD/'v5-source.zip'
    download_artifact(source_zip)
    with zipfile.ZipFile(source_zip) as z: z.extractall(BUILD)
    master=BUILD/'v5/master'
    required=['places_geo_master.csv','relations_geo_master.csv','aliases_geo_master.csv']
    missing=[x for x in required if not (master/x).exists()]
    if missing: raise RuntimeError(f'V5 artifact missing required master files: {missing}')
    log('V5 master input gate PASS')

    concat_parts('build_region_pages_v1_full.py',BUILD/'build_region_pages_v1_full.py')
    concat_parts('finalize_englishpt_region_pages.py',BUILD/'finalize_englishpt_region_pages.py')
    concat_parts('integrate_englishpt_region_ui_v2.py',BUILD/'integrate_englishpt_region_ui_v2.py')

    for script in ['build_region_pages_v1_full.py','finalize_englishpt_region_pages.py','integrate_englishpt_region_ui_v2.py']:
        log(f'running {script}')
        subprocess.run([sys.executable,str(BUILD/script)],check=True)

    src=BUILD/'v2-ui'
    qa=json.loads((src/'manifest/ui-integration-qa.json').read_text(encoding='utf-8'))
    if not qa.get('pass'): raise RuntimeError(f'region UI QA failed: {qa}')

    for name in ['region','station','newtown','district','search']:
        copytree_clean(src/name,Path(name))
    Path('assets').mkdir(exist_ok=True)
    for name in ['region.css','search.js','search-index.json']:
        shutil.copy2(src/'assets'/name,Path('assets')/name)
    Path('sitemaps').mkdir(exist_ok=True)
    sitemap_map={'admin.xml':'region-admin.xml','stations.xml':'region-stations.xml','newtowns.xml':'region-newtowns.xml','districts.xml':'region-districts.xml'}
    for s,d in sitemap_map.items(): shutil.copy2(src/'sitemaps'/s,Path('sitemaps')/d)

    entity_html=sum(1 for root in ['region','station','newtown','district'] for _ in Path(root).glob('*/index.html'))
    search_records=len(json.loads(Path('assets/search-index.json').read_text(encoding='utf-8')))
    region_sitemap_urls=sum(count_locs(Path('sitemaps')/d) for d in sitemap_map.values())
    service_sitemap_urls=count_locs(Path('sitemap.xml')) if Path('sitemap.xml').exists() else 0
    deploy_qa={
        'pass': entity_html==26937 and search_records==26937 and region_sitemap_urls==11209 and service_sitemap_urls>=95,
        'entity_html':entity_html,'search_records':search_records,'region_sitemap_urls':region_sitemap_urls,
        'existing_service_sitemap_urls':service_sitemap_urls,'region_ui_qa':qa
    }
    Path('region-deploy-qa.json').write_text(json.dumps(deploy_qa,ensure_ascii=False,indent=2),encoding='utf-8')
    if not deploy_qa['pass']: raise RuntimeError(f'deployment QA failed: {deploy_qa}')
    log('deployment QA PASS')
    shutil.rmtree(BUILD)

if __name__=='__main__':
    main()
