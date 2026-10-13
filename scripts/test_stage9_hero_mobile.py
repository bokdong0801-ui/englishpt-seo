#!/usr/bin/env python3
"""Fast real-Chromium layout check for the five Hero V2 national hubs.

Run this before expensive Stage 9 regeneration; no site deploy, no form submission.
"""
from __future__ import annotations
import http.server
import json
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from pathlib import Path
import pychrome

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("englishpt.html", "courses.html", "student-english.html", "english-conversation.html", "exam-english.html")
BROWSER = (shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser"))
assert BROWSER, "Chromium unavailable"
PORT = 8893
DEBUG_PORT = 9239
with tempfile.TemporaryDirectory(prefix="hero-v2-layout-") as tmp:
    root = Path(tmp)
    (root / "assets").mkdir()
    for name in PAGES:
        shutil.copy2(ROOT / name, root / name)
    for name in ("styles.css", "site.js"):
        shutil.copy2(ROOT / "assets" / name, root / "assets" / name)
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(*args, directory=str(root), **kwargs)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    proc = subprocess.Popen(
        [BROWSER, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
         f"--remote-debugging-port={DEBUG_PORT}", "--remote-allow-origins=*",
         f"--user-data-dir={root / 'chrome-profile'}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", DEBUG_PORT), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.15)
        browser = pychrome.Browser(url=f"http://127.0.0.1:{DEBUG_PORT}")
        tab = browser.new_tab()
        tab.start()
        tab.Page.enable()
        tab.Runtime.enable()
        expr = r'''(()=>{
          const el=document.querySelector('.hero h1');
          const range=document.createRange();range.selectNodeContents(el);
          const rects=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0);
          const tops=[];
          rects.forEach(r=>{if(!tops.some(t=>Math.abs(t-r.top)<2))tops.push(r.top)});
          const cta=document.querySelector('.hero-choice-actions');
          const cs=cta?getComputedStyle(cta):null;
          return {title:el.textContent.trim(), lines:tops.length,
            scrollWidth:document.documentElement.scrollWidth,
            viewport:innerWidth,
            ctaVisible:!!cta&&cta.getBoundingClientRect().height>0,
            ctaCols:cs?.gridTemplateColumns||'',
            ctaCount:cta?.querySelectorAll('a,button').length||0};
        })()'''
        errors = []
        results = []
        for w,h in ((320,700),(360,800),(390,844),(430,932),(768,1024),(1440,900)):
            tab.call_method("Emulation.setDeviceMetricsOverride", width=w, height=h,
                            deviceScaleFactor=1, mobile=w<769,
                            screenWidth=w,screenHeight=h, dontSetVisibleSize=False)
            for name in PAGES:
                tab.Page.navigate(url=f"http://127.0.0.1:{PORT}/{name}")
                time.sleep(0.22)
                m=tab.Runtime.evaluate(expression=expr, returnByValue=True)["result"]["value"]
                results.append({"page":name,"width":w,**m})
                if m["lines"]>3 or m["scrollWidth"]>w+1 or not m["ctaVisible"] or m["ctaCount"]<2:
                    errors.append({"page":name,"width":w,**m})
        print(json.dumps({"checked":len(results),"failures":errors,
                          "status":"PASS" if not errors else "FAIL"},ensure_ascii=False))
        tab.stop()
        browser.close_tab(tab)
        if errors:
            raise SystemExit(1)
    finally:
        proc.terminate()
        server.shutdown()
