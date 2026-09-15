#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
OUT="$ROOT/_site"
TMP="$(mktemp -d)"
REGION_BASE="https://raw.githubusercontent.com/bokdong0801-ui/korea-region-db/region-pages-release"
trap 'rm -rf "$TMP"' EXIT

rm -rf "$OUT"
mkdir -p "$OUT"

# Preserve the existing EnglishPT static service site, but do not publish source/helper files.
rsync -a ./ "$OUT/" \
  --exclude '.git/' \
  --exclude '_site/' \
  --exclude 'scripts/' \
  --exclude '.github/' \
  --exclude 'README.md' \
  --exclude 'README_*.txt' \
  --exclude 'REMOTE_DEPLOY_STATUS.txt' \
  --exclude 'EXPANSION_NOTES.txt' \
  --exclude 'QA_*.txt'

mkdir -p "$OUT/sitemaps"
if [[ -f "$OUT/sitemap.xml" ]]; then
  cp "$OUT/sitemap.xml" "$OUT/sitemaps/services.xml"
fi

# Pull the audited V5 region release produced by korea-region-db.
curl -fsSL --retry 4 --retry-delay 2 "$REGION_BASE/region-pages.tar.gz" -o "$TMP/region-pages.tar.gz"
curl -fsSL --retry 4 --retry-delay 2 "$REGION_BASE/region-pages.tar.gz.sha256" -o "$TMP/region-pages.tar.gz.sha256"
EXPECTED="$(awk '{print $1}' "$TMP/region-pages.tar.gz.sha256")"
ACTUAL="$(sha256sum "$TMP/region-pages.tar.gz" | awk '{print $1}')"
if [[ -z "$EXPECTED" || "$EXPECTED" != "$ACTUAL" ]]; then
  echo "Region bundle checksum mismatch: expected=$EXPECTED actual=$ACTUAL" >&2
  exit 1
fi

tar -xzf "$TMP/region-pages.tar.gz" -C "$OUT"

# Root sitemap becomes a sitemap index. Existing service URLs remain in services.xml.
cat > "$OUT/sitemap.xml" <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://englishpt.kr/sitemaps/services.xml</loc></sitemap>
  <sitemap><loc>https://englishpt.kr/sitemaps/region-admin.xml</loc></sitemap>
  <sitemap><loc>https://englishpt.kr/sitemaps/region-stations.xml</loc></sitemap>
  <sitemap><loc>https://englishpt.kr/sitemaps/region-newtowns.xml</loc></sitemap>
  <sitemap><loc>https://englishpt.kr/sitemaps/region-districts.xml</loc></sitemap>
</sitemapindex>
XML

cat > "$OUT/robots.txt" <<'TXT'
User-agent: *
Allow: /

Sitemap: https://englishpt.kr/sitemap.xml
TXT

# Deployment gates: region entry points and SEO files must exist.
for f in \
  "$OUT/region/index.html" \
  "$OUT/station/index.html" \
  "$OUT/newtown/index.html" \
  "$OUT/district/index.html" \
  "$OUT/search/index.html" \
  "$OUT/assets/region.css" \
  "$OUT/assets/search-index.json" \
  "$OUT/sitemaps/services.xml" \
  "$OUT/sitemaps/region-admin.xml" \
  "$OUT/sitemaps/region-stations.xml" \
  "$OUT/sitemaps/region-newtowns.xml" \
  "$OUT/sitemaps/region-districts.xml"; do
  test -s "$f" || { echo "Missing deploy file: $f" >&2; exit 1; }
done

# Existing root redirect/legacy redirects must survive the merge.
test -s "$OUT/_redirects" || { echo "Missing _redirects" >&2; exit 1; }
grep -q '^/ /englishpt.html 301!' "$OUT/_redirects" || { echo "Root redirect missing" >&2; exit 1; }

python - <<'PY'
from pathlib import Path
import json, re, xml.etree.ElementTree as ET
root=Path('_site')
idx=ET.parse(root/'sitemap.xml').getroot()
assert idx.tag.endswith('sitemapindex')
for p in [
    'sitemaps/services.xml','sitemaps/region-admin.xml','sitemaps/region-stations.xml',
    'sitemaps/region-newtowns.xml','sitemaps/region-districts.xml'
]:
    ET.parse(root/p)
records=json.loads((root/'assets/search-index.json').read_text(encoding='utf-8'))
assert len(records)==26937, len(records)
for rel in ['region/index.html','station/index.html','newtown/index.html','district/index.html','search/index.html']:
    s=(root/rel).read_text(encoding='utf-8')
    assert 'https://englishpt.kr/' in s
    assert '잉글리시PT' in s
print(f'Netlify deploy QA PASS: search_records={len(records)}')
PY

echo "EnglishPT merged deploy tree ready at $OUT"
