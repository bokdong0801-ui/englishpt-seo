# ENGLISH PT v23.5.2.1 — Exact Production Candidate DRAFT READY, Publication approval checkpoint

2026-10-19 KST. **No Production publication, no test Forms POST, no Google or Naver search submission.**

## Verified Production-project Draft

- Successful one-shot workflow: [GitHub Actions #39217626687](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39217626687). **SUCCESS: 21 successful steps, zero failed.**
- Immutable Draft ID: `6ad5ca0f1f2051f04bdd9287`; `state=ready`, `published_at=null`.
- Actual Draft URL: https://enpt23521prodfinaldraft1--englishpt-seo.netlify.app
- Target Netlify Production project ID: `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`.
- **Current Production remains old published deploy** `6ac4bd517c30220008bb9661`. No live-site publication occurred.
- Exact previously frozen Production-ready input archive SHA256: `0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8`.
- Original independently verified 1,791-file Production rollback ZIP SHA256: `b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5`.
- [Actual CLI log, source SHA proof, Netlify state, mixed-route/OG HTTP QA report, Artifact 12170760676](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39217626687/artifacts/12170760676).

## Real Draft QA outcomes

| Gate | Verified |
| --- | --- |
| Published Production untouched | YES |
| Immutable Draft READY, no deploy error | YES |
| 62 GET-only tests with zero errors | PASS |
| Indexable source page-level meta robots | 12 live routes PASS |
| Intentional noindex source page-level meta robots | 18 live routes PASS |
| Canonical URL and HTML content-type | 30 live public routes PASS |
| Six real consultation HTML forms | 6/6 PASS, static markup only |
| Netlify Form already registered | `englishpt-consultation` form name confirmed in site API |
| OG editorial 1200x630 images | 29/29 PASS |
| Robots.txt and sitemap-index.xml | PASS, Production-oriented directives |
| pilot.js patched SHA256 | PASS |
| Release source page set and byte-integrity | Previous full SHA1 180,800/180,800, 158,571 routes, 21,964 indexable + 136,607 noindex, 44 XML sitemap shards + index, static Form blueprint, 22,088 PNG PASS on prelaunch run #39216417010 |
| Header-based Draft noindex | **Not observed** on public sample responses; the Draft alias URL is accessible and must NOT be treated as search-engine protected. Do not widely distribute/link this temporary Draft URL. |
| Real Forms submission/email | **NOT TESTED**, requires separately authorized POST and inbox check |
| Actual new `englishpt.kr` published headers | **NOT TESTED** until Production publish |
| Google Search Console / Naver | **NOT SUBMITTED** |

## Release recommendation and remaining authorization

The originally planned **nonpublished Draft verification is DONE**. It is not necessary to re-upload this ~180k-file site in order to publish. Netlify officially supports **Publish Deploy** on any successful deploy from the site's Deploy list; the existing immutable READY Draft can be selected. The corresponding API is `POST /api/v1/sites/{site_id}/deploys/{deploy_id}/restore`, but do NOT invoke this without separate explicit user approval. Official docs: https://docs.netlify.com/deploy/manage-deploys/manage-deploys-overview/#rollbacks

Proposed one-time publication **after approval**:

1. GET-only immediately before action: compare exact Netlify site ID, domain englishpt.kr, current published ID `6ac4bd517c30220008bb9661`, target ready deploy ID `6ad5ca0f1f2051f04bdd9287`; require original ZIP backup intact and account limits clear.
2. **Exactly one** publish/restore for the exact target READY draft, not another CLI upload. Abort and request fresh approval if anything changed.
3. Immediately GET site API and immutable deploy: only claim success after `published_deploy.id=6ad5ca0f1f2051f04bdd9287`.
4. Run GET-only new englishpt.kr tests for main, 12 indexable + 12 noindex, six tutors, OG, robots, sitemap, patched JS; ensure public indexable URLs do **not** have global X-Robots noindex and noindex pages remain blocked.
5. Confirm Netlify Forms and email-hook metadata; real test submission/email delivery needs user authorization and a suitable verified recipient/consent. Do not invent user lead details or send repeated test form submissions.
6. On failure, stop and, subject to explicit preauthorization for rollback, restore previous production deploy `6ac4bd517c30220008bb9661`; do not delete immutable deploy snapshots.
7. Only after live site and Forms QA pass, handle Google Search Console and Naver Search Advisor sitemap and URL collection where connected official access exists, else provide exact UI steps.

### Wording for exact Production publication authorization

"ENGLISH PT v23.5.2.1의 `englishpt.kr` Production 게시 1회를 승인합니다. **새 파일을 재업로드하지 말고**, 검증된 Netlify Draft `6ad5ca0f1f2051f04bdd9287`만 게시하세요. 기존 배포 `6ac4bd517c30220008bb9661`과 백업을 보존하고, 오류 시 게시를 중단하여 보고하세요. 정상 게시 후 실제 홈페이지·SEO·상담폼 등록을 검사하세요."

**This documentation change itself performs no Netlify write or publication.**
