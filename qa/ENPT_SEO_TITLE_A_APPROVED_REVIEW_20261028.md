# ENGLISH PT — Approved SEO title policy A (review-only)

Date: 2026-10-28 (Asia/Seoul)
Status: **Implementation in isolated GitHub review branch; not deployed**
Branch: `review/enpt-seo-titles-approved-a-v1-20261028`

## User-approved policy — THREE categories

1. **Station general hub**: `반월당역 영어회화 영어과외 | 1:1 맞춤 직장인 학생 주부`.
   Change title and meta description of the 911 existing station hubs. Preserve H1.
2. **Neighborhood general hub**: `송현동 영어회화 영어과외 | 1:1 맞춤 직장인 학생 주부`.
   This is a **template/policy ONLY**; the release builder has no automatically generated 5,149-neighborhood general hub class. Do NOT create routes, index, or sitemap entries merely to apply this rule. For a real neighborhood hub in a later approved project, check its actual content and same-name place disambiguation before using this template. Regional /regions/ provincial hubs are **not** neighborhood hubs.
3. **Specialist course pages**: region/station + focused intent + relevant 1:1 tailored phrase. 23 course types exactly; do not add other audiences, duplicate 왕초보/초보/기초 keywords, or require 잉글리시PT in each title. `scripts/enpt_seo_title_policy_a_v1.py` is the authoritative registry of titles for both station and mass-generated neighborhood specialties.

### Examples
- `반월당역 직장인 영어회화 | 1:1 맞춤 비즈니스 영어`
- `송현동 직장인 영어회화 | 1:1 맞춤 비즈니스 영어`
- `사직동 왕초보 영어회화 | 기초부터 1:1 맞춤`
- `송현동 오픽 과외 | 1:1 맞춤 말하기`
- `반월당역 토익학원 비교 | 1:1 맞춤 수업 선택` (do not imply a physical ENGLISH PT academy or office)

### Scope and safety
- Existing **911 station hubs + 911 x 23 station specialists**: generator change.
- Existing mass-produced neighborhood specialist pages: generator change for all 23 supported intents, **their existing noindex,follow is deliberately preserved**. Titles alone will not make them indexable.
- Existing legacy preserved pages and national / provincial hubs are NOT silently rewritten. Inspect and approve separately before later extensions.
- Existing station hub description includes 왕초보, 기초, 직장인, 학생, 주부, 시험영어 in natural prose; generic specialists retain their already reviewed descriptions instead of stuffing keywords.
- No robots.txt, sitemap, canonical, OG images, links, forms, site deployments or search-collection submissions are changed. OG title and WebPage JSON-LD name should match changed title upon rerender by existing pipeline.
- Station names can be long; search engines may truncate/rewrite. Title uniqueness != content uniqueness or higher search volume.
- **NO** Production deploy, Netlify Draft creation, V3.1 mutation/merge, or future indexing-policy change authorized by this approval.

### Release gates before any publication
1. All 23 intent keys match generator; 911 station names + 23 x 911 distinct title strings.
2. Sample generated HTML (station hub; station specialty; neighborhood specialty) H1/title/OG/schema consistency, canonical, robots and links.
3. Full site-generated title/content and unchanged indexability audit, subject to available build source artifacts.
4. In the later release window: a fresh unpublished Preview with sitewide QA and final separate approval.

### Pending caveats
- A common suffix repeated over thousands of pages may trigger title rewriting. Monitor search performance; do not claim ranking gains.
- Same-name neighborhood localities in different jurisdictions need jurisdiction-aware uniqueness verification. The title policy is keyed by visible locality name but does not yet prove locality-wide title uniqueness.
- Historical preserved special pages may need independent migration; they are outside the mass renderer source and currently unchanged.
