ENGLISH PT / NETLIFY-READY RELEASE
Updated: 2026-09-14

STATUS
- Content pages: 95
- Legacy permanent redirects: 74
- GitHub repository: bokdong0801-ui/englishpt-seo
- Planned host: Netlify
- Public deployment: PAUSED until the final domain is chosen
- Current domain in canonical / Schema / sitemap / robots: https://englishpt.kr (PLACEHOLDER ONLY)

NETLIFY SETUP
- netlify.toml: publishes the repository root as a static site
- _redirects: contains the root redirect and legacy URL permanent redirects
- No build framework is required; this is a static HTML/CSS/JS site
- Do not publish publicly until the final domain has replaced the placeholder domain

WHEN THE FINAL DOMAIN IS DECIDED
1) Run: python scripts/set-domain.py https://YOUR-DOMAIN
2) Review canonical URLs, JSON-LD URLs, sitemap.xml and robots.txt
3) Commit and push the domain replacement
4) Connect this GitHub repository to Netlify
5) Deploy the main branch
6) Attach the custom domain and HTTPS
7) Verify representative pages, CSS/JS assets, 74 legacy redirects and / -> /englishpt.html
8) Test one real EmailJS lead submission
9) Submit /sitemap.xml to Google Search Console

QA BEFORE HOSTING
- 95 content pages
- Canonical mismatches: 0
- Missing H1: 0
- JSON-LD parse errors: 0
- Broken internal HTML links: 0
- Forbidden phone/video/visit sales splits: 0
- Content similarity >= 0.70: 0 pairs

IMPORTANT
- Visible FAQ content is retained; FAQPage schema is intentionally omitted
- Illustrative cases are labeled as illustrative rather than testimonials
- The original backup folder from the prior project was not modified
- GitHub Pages is not the intended production host because this migration relies on server-side permanent redirects
