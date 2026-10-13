from __future__ import annotations

"""Legacy guard.

This script previously generated 26,937 public DB-entity pages under /region,
/station, /newtown, /district and /search. That deployment direction is retired.

The V5 dataset is still authoritative and will be reused by the new Region
Resolver, but this legacy page generator must never run as part of production
builds again.
"""

import sys

MESSAGE = """
[legacy-region-deploy] BLOCKED

The 26,937 DB-entity public page generator has been retired.
ENGLISH PT now uses a service-first rollout:
1) normalize nationwide current dong data,
2) create/approve dong-level English service landing hubs,
3) expand only after QA to gu -> si -> newtown -> village -> district.

Use scripts/validate-service-site.py for the current production build.
Do not re-enable this file without an explicit project-direction change.
""".strip()

print(MESSAGE, file=sys.stderr)
raise SystemExit(2)
