# ENGLISH PT v23.5.2.1 Release Gates (2026-10-17)

## Invariants (stop on any violation)
- Production englishpt.kr, Netlify Production, POST form submission, and search registration require separate explicit user approval.
- Never rerun a failed Draft upload solely to fix the validator. Inspect original JSON and fix one root cause first.
- All build inputs are frozen by GitHub run IDs and SHA256. A previously built candidate is NOT valid after a shared JavaScript fix.
- Only Review site ID `803550a8-03af-4776-bc8a-bd0bae85f5c7` may receive Draft releases.
- Single immutable Draft revision; do not let pushes to validators trigger redeploy.

## Ordered pipeline
1. Static DNS host guard: HTTPS, dedicated Review Netlify alias, each DNS label <= 63 characters, safe ASCII.
2. Immutable source artifact and SHA gate: source run 38902833981, 158,571 generated pages, 21,964 index, 136,607 noindex and sitemap entries.
3. Fix shared JavaScript exactly once: known old SHA `f9e4f7e90de3924281ced3c346491661c5d047fcc34400063ac0145165d039e5`, new SHA `d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede`; Node syntax + 24 viewports/48 CTA + 8 non-tutor regression checks.
4. Static site gate before Netlify upload: 158,573 HTML including index and 404, actual OG alias metadata, 29 PNGs all 1200x630, 6 representative tutor pages, global Draft X-Robots-Tag noindex, canonical englishpt.kr preserved.
5. Isolated Review Draft upload is permitted **once**, only after steps 1-4 PASS.
6. Live read-only gate on immutable deploy URL: 6/6 HTTP, 29/29 OG HTTP 200 PNG, 24/24 viewport cases, 48/48 CTA, 24/24 regional course clicks, new copy/hidden field consistency. No POST.
7. If step 6 fails, preserve deployed Draft and run *read-only diagnosis*, no reupload.
8. Production package gate (separate approval): derive corrected package from **fixed** JS and original production OG host, no Preview alias, remove only global Draft noindex, preserve per-page noindex, verify sitemap/index/canonical; generate new SHA256 and independent report. **Previous production candidate 38903769454 is stale**.
9. Production release requires explicit user authorization, rollback snapshot, actual Netlify capacity, and later separately authorized real form/email test.

## Old release candidate audit
- Archived offline candidate from run 38903769454 predates JS patch, so cannot be used for Production.
- Its packaging used `scripts/v2351_production_release_gate.py`, which requires the OG host `https://englishpt.kr/assets/images/og-pages/` and rejects Netlify Preview hosts. The earlier DNS alias-length problem is specific to Review.
- Rebuild the Production candidate **after** the new Review Draft passes, then compute a fresh SHA256. Never reuse old archive hash.
