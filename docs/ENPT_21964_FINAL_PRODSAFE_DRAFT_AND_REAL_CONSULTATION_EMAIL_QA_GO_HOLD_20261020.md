# ENGLISH PT 21,964 Square OG — Final Production-Safe Draft and Actual Consultation QA

Date: 2026-10-20. **Status: SOURCE PASS / NONPUBLISHED DRAFT READY PASS / LIVE SEO+FORMS SAMPLE PASS / NETLIFY VERIFIED SUBMISSION PASS / NAVER MAILBOX DELIVERY NOT VERIFIED / PRODUCTION HOLD**

## Immutable source
- Original approved site source SHA256: `6d0272d1601a1a47abeccc4d740359af9e7678293ee0a3d257eecd2ca478d884`
- 180,800 original site files + 21,964 already verified square JPEGs = **202,764** assembled production-candidate files.
- 158,571 original SEO URLs. 21,964 indexable routes each with one mapped square OG JPEG/canonical, 136,607 noindex payloads exactly original SHA1.
- 44 original sitemap XML shards (SHA1 unchanged), both Google/Naver ownership meta on both homepage representations.
- Original `robots.txt`, `_headers`, Edge router, Netlify configuration, forms blueprint, 75 redirects remain SHA1-matched. **No review-wide noindex/Disallow /** in assembled production candidate.
- Source offline independent QA: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39399897235

## Exact nonpublished production-safe candidate
- New Draft ID **`6ad7506cdeb778280a54ee2a`**, `READY`.
- Draft URL: https://enptog21964prodsafereview20--englishpt-seo.netlify.app/englishpt.html
- Marker: `ENPT-21964-PRODSAFE-ORIGINAL-ROBOTS-CLI-FULL-NONPUBLISHED-ONCE-20261020`
- Original router bundled by Netlify CLI directly (avoids earlier manual Edge TAR HTTP502 issue).
- GET status HTTP200 for homepage/index, station TOEIC/IELTS, tutor pages, robots, sitemap. Raw `/__pages/23/englishpt.page` retains `X-Robots-Tag: noindex, nofollow`; public HTML has no global preview noindex header.
- Exact source router SHA256 **`5cb224d7693a92b2b65677bec3dbee780e7c30bcc03fcbeebc6842a873344470`**. Source `robots.txt` and `_headers` original SHA1 were checked.
- Netlify site Production unchanged: `6ad5eb4918f9411c4d5e1ba4`. No `--prod`, no publish.
- Actual deploy and HTTP evidence: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39414952403

## Final mixed live URL / browser verification, original production robots semantics
- READY Draft above, **42/42** actual live routes HTTP200 + canonical/robots meta parity: **18 source-indexable, 24 original source-noindex** (6 of 24 are consultation form pages).
- The six form pages have original `englishpt-consultation` markup and essential fields.
- Ten actual square JPEG GET responses have identical signed SHA256 + 1200x1200.
- Google/Naver ownership tags on both home representations; 44 sitemap index URLs; raw `.page` internal noindex protection verified.
- Real Chrome 390px and 1440px clicked `#consultation-preview` and verified form became visible with name/phone/submit UI. GET-only browser smoke submitted no forms.
- Outcome: `PASS_PRODSAFE_DRAFT_MIXED_SEO_EDGE_FORMS_LIVE_BROWSER_NO_POST`.
- Live independent QA: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39416389999

## Actual user-approved consultation test and email notification limitation
- Only ONE synthetic and clearly marked real browser form submission was sent from the production-safe nonpublished Draft.
- Test marker: `ENPT_OG21964_FINAL_QA_SINGLE_20261020`
- Route `/gyeongnam-milyang-naeidong-elem-tutor.html`, `POST` returned HTTP200; browser success text appeared.
- Netlify created submission ID `6ad751390919add0ec06f61c` for registered `englishpt-consultation` form `6ad31619a0da0424ffd54af9`.
- Initial test data (synthetic no-real phone) was classified as spam by Netlify/Akismet. Therefore original `submission_created` email notification may NOT have fired.
- Using documented `PUT /api/v1/submissions/{id}/ham` for this exact ID only, state change returned HTTP204 and subsequent verified submissions GET confirmed the same single test now in **verified** list. No second POST was made.
- Existing form notification hook `type=email`, `event=submission_created` has an email matching **cicada3865@naver.com**. Verified Netlify registration/hook is not independent evidence that the Naver mailbox received the mail after the spam→verified change.
- Naver mailbox read access is **not connected in this conversation**. `naver_inbox_delivered` = **UNVERIFIED**, do not state delivered.
- Form hook audit: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39414278964
- ONE actual POST and initial spam classification: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39415577110
- Exact 1 test spam→verified via single PUT (no second POST): https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39416071957

## Remaining GO/HOLD gates
- **HOLD Production publication** until the user inspects this exact Draft and expressly approves publishing.
- Ask the user to open Naver mail Inbox/Spam and search for the test marker above and/or `formresponses@netlify.com`. Because spam was reclassified after creation, absence of notification does not establish broken legitimate-email delivery.
- If user requires a definitive email-inbox check, connect a supported mailbox or user confirms Naver receipt; do not fabricate an email-delivered result.
- If test email absent, request approval for a separate realistically filled test, ideally with user-controlled true contact details, and keep synthetic test distinguishable. **Do not automatically re-POST the existing marker**.
- Keep immutable original published deploy ID `6ad5eb4918f9411c4d5e1ba4` as rollback reference.
- No live full 158,571-URL network crawl was performed; full SEO/file/content tests were offline with representative live URL checks.
- Nonpublished Draft publicly accessible URL mirrors **production SEO indexing semantics**, without global noindex. Avoid promotion of the Draft URL to search; review and retire it after release.

**Verdict: production-safe candidate file QA PASS, exact new Draft READY, 42 live route + browser QA PASS, Netlify form backend PASS, recipient Naver email webhook config PASS, actual Naver inbox receipt UNCONFIRMED. Production unchanged.**
