# ENGLISH PT SEO A — V3.1 separate unpublished Preview GO/HOLD (2026-10-28)

**Decision: HOLD — no new Netlify Preview was created.** The existing Production and V3.1 final ready Draft were preserved.

## User-approved title policy and completed implementation
- GitHub isolated branch: `review/enpt-seo-titles-approved-a-v1-20261028`.
- Separate title registry `scripts/enpt_seo_title_policy_a_v1.py`.
- Station hubs: 911; station specialists: 20,953; **21,864 unique titles**.
- Specialized course intents: exactly 23. Audience terms not repeated on specialist pages; `1:1 맞춤` in aligned context.
- Neighborhood general hub: policy only, no new pages created; mass-generated noindex specialists remain `noindex,follow`.
- QA success: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/40663000685 : 21,864/21,864 distinct titles, 26 HTML samples checked, 0 errors, 0 warnings. Legacy cluster-link QA threshold corrected from 22 to 20 because real navigation has a national student-guide fallback; no link target changed.
- Existing source filenames, Canonical URLs, OG image assets, sitemaps, robots, form delivery and production content were not changed.

## Exact V3.1 source safety checks
- Existing Production ID: `6adafef5f2c6d196833683db` (must remain).
- Existing ready V3.1 unpublished Draft ID: `6ae06963f085b33a5ee903eb` (must remain).
- Frozen static file count: `202786`; indexed signed routes: `21964`; noindex routes: `136607`.
- Original V3.1 7 Byeongmokandong corrections reconstructed from signed files, safely.
- Public station URL maps via Edge router to `/__pages/<bucket>/station-<slug>[-<intent>].page`. Never add 21,864 direct .html files or rerender full HTML without byte-diff proof.
- Direct regeneration with old station generator is NOT SHA-identical to V3.1 frozen HTML; sample SHA test: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/40663745275 .
- Sample source data GET SHA + minimal head patch passed 7 files.

## Full source download and Preview blockers
1. Full SHA-preserving SEO-only patch from currently published exact shards:
   https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/40664047571
   Final **HOLD**, 3,252 of 21,864 processed before failure. One mismatching raw payload path (`/__pages/7c/station-gapcheon-duolingo-academy.page`), followed by multiple GitHub runner `Network is unreachable` failures. No Netlify deploy POST performed.
2. Separate new unpublished Draft job:
   https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/40664769405
   Correctly failed its prerequisite guard **before build, before POST** because the full SHA offline gate did not pass. **No new Draft ID/URL exists.**
3. Historical 2026-10-19 sharded source archive has a different file layout; cannot substitute:
   https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/40665367496 .
4. Historical 2026-10-21 complete `.page` source archive is NOT byte-identical to frozen V3.1: 0/7 matched. It cannot be substituted:
   https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/40665915620 .

## No unauthorized changes
- Netlify Production publishes: 0.
- Existing V3.1 Draft modifications: 0.
- New Preview creates: 0.
- Netlify restore / site-config writes: 0.
- New robots, canonical and sitemap changes: 0.
- Consultation POSTs: 0.
- All new source and CI jobs are isolated in the review branch only.

## Required next technical step to proceed safely
1. Recover the **exact frozen V3.1** 21,864 signed `.page` byte payloads by a reliable **verified SHA1 per file** method. Prefer an authoritative full snapshot from the actual deploy or a deterministic archive assembled from exact SHA-confirmed bytes. Do not substitute an older 2026-10-21 archive or generator render.
2. Reconcile the one bad shard and all other potential SHA mismatches; prevent rate limiting with safe bounded fetches or authenticated export. All 21,864 existing source SHAs must match the signed V3.1 manifest **before changing any metadata**.
3. Apply `<title>`, `og:title`, relevant meta description and WebPage JSON-LD name only; preserve body, forms, Canonical, index policy, router, redirects and 44 sitemap shards byte-identically. Expected 202,786 path names preserved.
4. Complete 21,864/21,864 offline SHA/head/body checks, then and only then run **ONE new nonpublished** Draft API POST using the exact 202,786 path manifest and historical verified Edge TAR. Verify old V3.1 Draft and current Production by GET before/after.
5. Check new Draft Preview sample browser appearance, 44 XML, all 21,964 indexable routes, forms GET-only, mobile/desktop. Obtain explicit separate user Production approval before any publish.

**Do not report draft creation or 21,864 actual HTML pass until Netlify confirms a READY new Draft and the full audit passes.**
