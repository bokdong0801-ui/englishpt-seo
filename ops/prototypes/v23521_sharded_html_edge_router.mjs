/*
  EXPERIMENTAL ONLY: never deployed. Testable illustration of preserving the original
  /slug.html public URL while serving a hash-sharded internal file from /__pages/ab/slug.html.
  Requires separate Preview QA for SEO robots headers, Netlify Forms, redirects and actual Edge runtime.
  Candidate archive MUST remain unchanged until separately approved.
*/
export function fnvBucket(filename) {
  const bytes = new TextEncoder().encode(filename);
  let hash = 2166136261 >>> 0;
  for (const b of bytes) {
    hash = Math.imul(hash ^ b, 16777619) >>> 0;
  }
  return (hash >>> 24).toString(16).padStart(2, "0");
}
export function rewritePath(pathname) {
  if (!/^\/[^/]+\.html$/.test(pathname)) return null;
  const encodedName = pathname.slice(1);
  let name;
  try {
    name = decodeURIComponent(encodedName);
  } catch { return null; }
  if (name === "index.html" || name === "404.html" || name.includes("/") ||
      name.includes("\\") || name.includes("\0")) return null;
  return "/__pages/" + fnvBucket(name) + "/" + encodedName;
}
export default function handler(req) {
  const url = new URL(req.url);
  const path = rewritePath(url.pathname);
  if (path === null) return;
  url.pathname = path; // URL rewrite stays on this site and retains query string
  return url;
}
export const config = { pattern: "^/[^/]+\\.html$" };
