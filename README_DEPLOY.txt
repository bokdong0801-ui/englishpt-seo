ENGLISH PT FINAL RELEASE V3
Generated: 2026-09-14

CONTENT PAGES: 95
EXPANSION PAGES: 26
LEGACY REDIRECTS: 74
DOMAIN IN CANONICAL/SITEMAP: https://englishpt.kr

CURRENT REPOSITORY
- GitHub repository: bokdong0801-ui/englishpt-seo
- Branch: main
- The 95-page production files are uploaded to main.
- Shared assets: assets/styles.css, assets/site.js

DEPLOYMENT
1) Deploy the repository root as the web root.
2) Use the redirect config appropriate for the host:
   - Vercel: vercel.json
   - Netlify / compatible static hosts: _redirects
   - Apache: .htaccess if present in the deployment package
   GitHub Pages does not provide true server-side 301 redirects, so Vercel or another redirect-capable host is recommended.
3) If the final domain is not englishpt.kr, replace https://englishpt.kr in every HTML canonical/OG/schema reference, sitemap.xml and robots.txt before production launch.
4) After the live site is spot-checked, submit /sitemap.xml in Google Search Console.
5) Keep permanent legacy redirects for at least one year.

LEAD FORM
The existing EmailJS production settings from the original site are reused in assets/site.js. Test exactly one real submission after deployment and confirm the message arrives correctly.

QA
- Content pages: 95
- Canonical mismatches: 0
- Missing H1: 0
- JSON-LD parse errors: 0
- Broken internal HTML links: 0
- Forbidden delivery-mode sales terms: 0
- Content similarity >=0.70 pairs: 0

IMPORTANT
- FAQ remains visible user content; FAQPage schema is intentionally not used.
- No phone/video/visit delivery-method SEO split is used in the new architecture.
- Illustrative cases are explicitly labeled as illustrative, not real testimonials.
- The legacy backup folder from the source project was never modified.

EXPANSION V3
- Added university: 7 pages
- Added job seeker: 5 pages
- Added international school: 9 pages
- Added Duolingo English Test: 1 page
- Added academy comparison: 3 pages
- Added English interview: 1 page
- Existing 74 legacy redirects are retained.

NEXT
- Connect this repository to Vercel or another redirect-capable host.
- Verify the final domain before production indexing.
- Run live redirect/canonical/sitemap/form/mobile checks after deployment.
