# ENGLISH PT v23.5.2.1 — Netlify Production timeout forensics & safe release plan

As of October 19, 2026 (KST). STATUS: PRODUCTION HOLD. All new work in this investigation was GET-only or offline; no Netlify deployments, Form submissions, billing or search-registration changes.

## Confirmed failed attempt

- Approved single GitHub Production attempt: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39007687919
- Immutable previous Production deploy, still published: 6ac4bd517c30220008bb9661 (ready).
- Failed Production deploy: 6ad30d01781992bcb8dd92a1, state error, error message Deploy canceled, published_at null.
- CLI used: netlify-cli/27.13.0; deploy command ran 2026-10-17 05:51:58Z to 06:50:27Z, approximately 58 minutes 29 seconds. Error: Timeout while waiting for deploy.
- The GitHub command redirected --json stdout, so intermediate file-upload and postprocessing progress was not recorded reliably. Netlify deploy summary status was unavailable with an empty messages list; the canceled deploy now has an empty readable files manifest. It cannot prove no upload ever occurred.
- Last known good Production backup: complete 1,791 files ZIP Artifact 12091475871, SHA256 b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5.
- Forensic Netlify GET run: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39192158516
- Summary-message GET run: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39192492944

## Exact 180,798-file candidate profile (verified source)

- Frozen candidate SHA256: e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba.
- 180,798 regular files / 9 directory members; total regular file sizes 6,814,005,542 bytes (6.81 decimal GB). The original .tar.zst download is about 1.23 GB; actual network transfer bytes may vary.
- 158,574 HTML files; 158,573 HTML at root, including index and 404.
- 158,591 total root files, compared with Netlify's documented 54,000-per-directory limit.
- 180,794 unique content SHA1 hashes; just four duplicate content instances. Content hash dedup alone cannot eliminate the large file count.
- 22,088 PNG files; 21,990 files under assets/images/og-pages, 45 XML files, 11 JSON files.
- Largest file: assets/search-thumbnail-manifest.json, 36,793,785 bytes. Do not delete or split until callers and functionality are regression-tested.
- Another immutable Review site previously reached ready with 158,589 root entries. This conflicts with the published Netlify directory limit; do not attribute the failed Production deploy to the per-directory cap alone without Netlify internal logs.
- Profiler and SHA1 content audit (PASS): https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39192376231 (Artifact 12160955069).
- Official Netlify limits: https://docs.netlify.com/deploy/deploy-overview/

## Tested alternative A — 256 hash-sharded HTML directories (OFFLINE PASS)

- Prototype: ops/prototypes/v23521_sharded_html_edge_router.mjs
- All-file offline route test: ops/prototypes/test_v23521_sharded_html_edge_router.mjs
- Move 158,571 root HTML pages (keep index.html and 404.html) to 256 hash bucket directories under /__pages/XX/original.html.
- New root would have 20 files. Each HTML bucket 553–687 files, and the largest remaining directory (OG pages) 21,990, all below the documented limit.
- Independent Python FNV-1a and Node.js router matched on all 158,571 page paths; 0 collisions and 0 failed mappings; intended public /slug.html URL stays unchanged via same-site Edge rewrite.
- Passed offline proof: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39192755152 (Artifact 12160547879).
- Caveat: Edge runtime, redirect precedence, robots/canonical HTTP headers, noindex rules, Netlify Forms detection and actual URL delivery HAVE NOT been tested on a real Netlify Draft site. Sharding also does not reduce 6.81 GB or 180,798 physical files.
- Official Edge rewrite API: https://docs.netlify.com/build/edge-functions/api/

## Tested alternative B — async SHA1 digest, Draft first (OFFLINE PASS)

- Offline SHA1 draft digest generator: scripts/v23521_sharded_async_manifest_OFFLINE_ONLY.py
- Intended API payload uses async=true, draft=true, and file path -> SHA1 mapping. NO Netlify API POST or PUT occurred.
- Full digest covers all 180,798 files exactly once, raw 6,814,005,542 bytes, unique SHA1 count 180,794.
- Manifest JSON size: 18,636,262 bytes. JSON SHA256 db8f9d78eb2f4749f600a66ec31945bdb94192817e1737c921e39131434ba1b2.
- Intended sharded output: 265 directories; maximum 21,990 files in any directory; root only 20 files.
- Actual Netlify API acceptance of the 18.64 MB JSON, request limits, upload throughput, credits and Edge bundling is UNKNOWN. The manifest contains no Edge Function bundle. This is NOT a ready-to-publish release.
- Offline digest proof: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39192954977 (Artifact 12160632926).
- Official Netlify async digest documentation: https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/

## Recommended safe execution route — requires NEW user approval

1. Prepare a NEW sharded candidate with an actually packaged Netlify Edge Function, preserving all 158,571 external URLs, all 21,964 indexable pages, 136,607 noindex pages, SEO canonical/robots/sitemaps and actual Netlify Forms. Review the 36.8 MB JSON's frontend dependencies before changing it.
2. Run full offline candidate tests, actual page HTML/robots parity, local HTML/JS route tests, 22,088 PNG file integrity, 44 XML sitemap shards, regional links and 24 tutoring CTA tests.
3. With separate explicit approval for ONE isolated Draft stage, create an async SHA1-digest deploy with draft=true; poll the immutable deploy ID, checkpoint required SHA1 uploads with bounded concurrency, and never blindly create a second deploy. A Draft is still a Netlify upload and cannot be treated as purely offline.
4. When the actual Draft is ready, verify Netlify Edge routing, SEO status, real HTTP, Form registration and actual consultation/email test only if specifically authorized. Confirm no changed canonical or global Draft noindex.
5. Obtain a separate explicit user approval before publishing a verified ready draft to englishpt.kr. Recheck previous live Production ID and backup, then use Netlify's documented Publish/restore flow and verify published deploy ID.
6. Any failure: HOLD and analyze; do not repeat the canceled Production CLI upload or automatically change the live site.

The old one-time Production approval has already been consumed by run 39007687919. No additional Production upload or new Draft upload has been authorized in this diagnostic turn. Using --timeout alone is not a supported fix for root directory count, large individual files or service-side processing.

Netlify docs: https://docs.netlify.com/deploy/deploy-overview/ | https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/ | https://docs.netlify.com/manage/routing/redirects/overview/
