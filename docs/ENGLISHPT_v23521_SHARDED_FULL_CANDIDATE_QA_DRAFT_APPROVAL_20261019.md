# ENGLISH PT v23.5.2.1 — actual sharded candidate and Draft authorization checkpoint

Updated 2026-10-19 KST. This step **did NOT deploy any Netlify Draft or Production** and did not submit Forms or change search registration.

## Newly generated and physically verified release files

- One-time GitHub builder, **SUCCESS, 17/17 steps**: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39194321977
- New actual full site candidate **Artifact ID 12160917768**: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39194321977/artifacts/12160917768
- Contents: ENGLISHPT_v23.5.2.1_SHARDED_EDGE_NEW_CANDIDATE_NOT_DEPLOYED.tar.zst
- **NEW candidate SHA256**: e27ffd3e94687e0f2fc58c3951ee1262bca8fd22bd684cf7b4bdb62d014326b1
- **NEW candidate size**: 1,181,327,378 bytes (inner tar.zst, not GitHub outer ZIP).
- Full all-files QA + source-to-target SHA1 map **Artifact ID 12161620971**: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39194321977/artifacts/12161620971
- Original source candidate SHA256: e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba.

## QA — full original content preserved

| Check | Verified value |
| --- | --- |
| Real packaged files | 180,799, original regular static bytes preserved except netlify.toml amended |
| Generated SEO pages | 158,571/158,571 |
| Total HTML | 158,574 |
| Root file count | 20 instead of 158,591 |
| Largest directory | 21,990 image files; 256 hash buckets, max 687 HTML each |
| Complete bytes | All 180,799 actual package members SHA1 verified against original file map |
| Indexable / noindex | 21,964 / 136,607 |
| Sitemaps | 44 XML shards + sitemap-index.xml; exactly 21,964 canonical URLs |
| Public route Edge rewrite | All 158,571 mapped, 0 routing errors |
| Existing redirects | 75 original 301 rules preserved |
| Tutoring forms | 6/6 original static Netlify form definitions |
| OG PNG | All 29 editorial 1200×630 valid; 21,990 generated OG PNGs preserved |
| Patched JavaScript | SHA256 d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede |
| Draft/Production changes | None |

The actual candidate contains the Netlify Edge code at netlify/edge-functions/shard-router.js with matching netlify.toml Edge declarations. All root .html public addresses remain unchanged through an intended same-site internal rewrite. The old 301 redirect paths are exempt.

## 2026-10-19 — First approved Draft CLI invocation HOLD; NO Netlify Draft created

- User-approved Draft-only run [39196186317](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39196186317): **failed, without creating a deploy ID**.
- Protected pre-upload gates passed: new candidate SHA256, 1,791-file independent old Production ZIP/sha, rollback deploy ready/current, Netlify account credits and Form detection ON; candidate unpack + 256-shard Edge configuration passed.
- Netlify CLI v27.13.0 rejected the command locally before uploading: `Error: --context flag is only available when using the --build flag`.
- The workflow mistakenly used `--no-build` AND `--context=deploy-preview` together. **These flags must not be combined.**
- Netlify GET after the invocation returned exactly **zero Drafts with this marker**, old Production `published_deploy.id=6ac4bd517c30220008bb9661` unchanged, and no new Draft URL. No HTTP, Forms or email testing was possible.
- Correction for the NEXT separately approved one-shot attempt: **remove `--context=deploy-preview` entirely**. Netlify CLI `deploy` without `--prod` creates a nonpublished Draft by default; retain `--no-build`, exact Site ID and SHA gates, unique alias, one-command ceiling, no auto retries.
- DO NOT rerun or edit the one-shot `push` workflow on the approved branch; prepare a new unique fail-closed workflow only after renewed authorization. The previous authorization specified a one-time attempt and automatic retry was expressly disallowed.
- Official CLI docs: https://cli.netlify.com/commands/deploy/ — command default is Draft and `--context` only used with builds.

## Draft approval and safe deployment plan

**NEW explicit permission is REQUIRED for creating exactly ONE Draft deploy.** Earlier approval for one Production attempt is already consumed by the failed Oct 17 workflow. Do not reuse the old Production workflow.

Proposed target: the existing EnglishPT Netlify Production SITE ID 98d96cc5-f0b7-4d3d-8072-6476d93e55a3 as a **nonpublished Draft**, not --prod. This target has Forms detection enabled; the separate Review site has it disabled. Netlify official documentation states manual CLI deploy defaults to Draft and a Draft does not change the currently published deploy.

Required before the Draft: reconfirm current published deploy ID 6ac4bd517c30220008bb9661, available rollback ZIP with SHA b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5, ordinary credits and Form detection. Download ONLY candidate Artifact 12160917768, verify exact new inner archive SHA and unpack. Use an explicitly guarded Netlify CLI Draft command WITHOUT --prod or --prod-if-unlocked; capture CLI progress, deploy ID and failed-run evidence, and do not automatically create another Draft on timeout.

After Draft READY, execute read-only script scripts/v23521_sharded_draft_live_get_only_QA.py to test at least 24 sampled pages plus six tutoring routes, robots/sitemap/JS and all 29 OG. Confirm actual Netlify Edge routing, canonical/noindex, 301 redirect parity, registered Forms and email hooks. Do not submit a real consultation POST without explicit separate authorization. Also verify Draft preview search noindex protection; Netlify provides it for deploy previews but not necessarily all manually generated Draft URLs.

**No new Production publication or Google/Naver sitemap submission** until actual Draft and consultation tests pass and another explicit Production authorization is granted.

### Unresolved Draft risk

Sharding addresses the 54,000-files-per-directory concern, but the new package still has 180,799 regular files (~6.81 GB raw); Netlify upload/API timeouts are still possible. The previous async SHA1 manifest did not contain a Netlify Edge bundle, so do not POST that manifest and assume an operational site. Netlify CLI supports bundling Edge functions in manual deploys, but actual large-scale upload must be validated live.

### Separate Draft approval wording

ENGLISH PT v23.5.2.1의 새로운 분산형 후보(SHA256 e27ffd3e94687e0f2fc58c3951ee1262bca8fd22bd684cf7b4bdb62d014326b1)를 Netlify 운영 프로젝트에 Production 공개 없이 Draft **1회만 생성하고 검증하는 작업**을 승인합니다. 기존 englishpt.kr 운영 배포는 유지하고, 실패하면 자동 재시도하지 마세요.

### Official references

https://docs.netlify.com/api-and-cli-guides/cli-guides/get-started-with-cli/
https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/
https://docs.netlify.com/build/edge-functions/get-started/
https://docs.netlify.com/deploy/compare-preview-options/
