# ENGLISH PT v23.5.2.1 — Actual deploy failure location and safe small diagnostic

Date 2026-10-19. Production remains UNCHANGED. The single approved full Draft attempt #39197077688 FAILED. No new Netlify deployment or Forms submission was attempted in this investigation.

## Evidence: actual GitHub CLI output

Source: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39197077688

- 2026-10-19 03:58:59 to 03:59:01 UTC: Edge bundling completed successfully.
- 03:59:45 UTC: CLI showed "Deploying 180797 files and 3 edge functions".
- 04:00:11 UTC: CLI reported "Found 5 files and 1 edge function to upload".
- 04:00:12 UTC: CLI reported "Finished uploading 6 assets".
- 04:00:12 to 05:25:14 UTC: stuck at "Waiting for deploy to go live".
- 05:25:14 UTC: TimeoutError and deploy canceled.
- Netlify canceled Draft ID: 6ad59585ca10712de65abef7; state error. Old Production published deploy still 6ac4bd517c30220008bb9661.

CONFIRMED: bottleneck was AFTER asset uploads, while Netlify prepared/finalized the new 180k-file deploy. Re-uploading the same 1.18 GB compressed site or merely raising the CLI timeout is not a demonstrated fix. Exact server-side cause still requires Netlify backend logs.

Potential contributing factors NOT proven: 158574 HTML postprocessing, Netlify Forms scanning enabled, 3 Edge metadata functions, large static assets. Netlify officially cautions that tens of thousands of HTML files can take a long time to process and files >10MB are not well supported. Similar official support case: https://answers.netlify.com/t/rangeerror-maximum-call-stack-size-exceeded/49078/9

Official documentation: https://docs.netlify.com/build/configure-builds/troubleshooting-tips/#large-files-or-sites

## Completed smaller real diagnostic candidate — OFFLINE PASS

GitHub build: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39205280906

Actual diagnostic package: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39205280906/artifacts/12165327888

Quality report: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39205280906/artifacts/12165576625

Candidate inner TAR.ZST SHA256: ef22d14e56c28a950dad5fd951d67c32856fef36a176408967e1857b32604d47

Package size 4,799,003 bytes. Total 324 files, 105 HTML (103 preserved original root SEO pages, including six student tutoring examples, plus index and 404), real original Edge JS, 141 images and required CSS/JS assets. SHA1 checked for every included file against original full candidate.

The diagnostic is intentionally globally NOINDEX in response headers with robots.txt disallow; it excludes the full sitemap and the 36.8MB thumbnail JSON. It must NEVER be published as a full website or treated as the 158571-page release.

## Next stage with separate approval

Run exactly ONE SMALL 324-file Draft on the separate Netlify Review site ID 803550a8-03af-4776-bc8a-bd0bae85f5c7. Do not use Production site or published deploy. Use Netlify CLI manual Draft with --no-build, --alias, --site, --timeout=240. Never use --prod, --prod-if-unlocked, or --context. Validate CLI help and flags before upload. Enforce a time cap below 10 minutes and do not retry automatically.

If small Draft succeeds, basic Edge bundling and Netlify deploy capability work, so full 158k HTML postprocessing is the likely limiting factor. Replan the full site into lower-HTML-count deploys or approved dynamic architecture; do NOT silently remove the 136607 noindex URLs from Production.

If even small Draft fails, focus on site-level Netlify errors and Support traces.

The separate Review site's Netlify Forms detection is OFF: static form HTML can be examined, but no Form registration conclusion should be drawn from that site's API.

Netlify Support trace to submit if needed: main site 98d96cc5-f0b7-4d3d-8072-6476d93e55a3, failed Draft 6ad59585ca10712de65abef7, previous failed Production 6ad30d01781992bcb8dd92a1, CLI 27.13.0. File-upload stage completed 04:00:12 UTC, timeout 05:25:14 UTC, Netlify error Deploy canceled, summary unavailable. Please investigate server-side processing stage, Forms HTML scan, Edge/redirect metadata, and platform timeouts before another full-sized deploy.

Status: Small pilot BUILT OFFLINE / No new Draft attempted / Production unchanged.
