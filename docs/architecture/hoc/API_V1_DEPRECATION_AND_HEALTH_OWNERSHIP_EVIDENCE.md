# API v1 Deprecation + Health Ownership — Evidence

**Date:** 2026-02-06
**Status:** COMPLETE

## Goals (User-Directed)

1. `/api/v1/*` is legacy and must not be canonical.
2. DB validation must live in `hoc_spine` and **L2 `/health` is the single owner**.
3. Changes must be evidence-backed (no assumptions).

---

## Evidence Commands (Copy/Paste)

```bash
cd /root/agenticverz2.0/backend

# 0) Definitive route truth (imports the real FastAPI app)
python3 - <<'PY'
from app.main import app

routes = [
    (getattr(r, "path", ""), sorted(getattr(r, "methods", []) or []), getattr(r, "name", ""))
    for r in app.routes
]
v1 = [(p, m, n) for (p, m, n) in routes if p.startswith("/api/v1")]
health = []
for r in app.routes:
    path = getattr(r, "path", "")
    if path == "/health":
        health.append(
            (
                path,
                sorted(getattr(r, "methods", []) or []),
                getattr(r, "name", ""),
                getattr(getattr(r, "endpoint", None), "__module__", ""),
            )
        )

print("total_routes", len(routes))
print("api_v1_routes", len(v1))
for p, m, n in sorted(v1):
    print(",".join(m), p, n)
print("health_routes", len(health))
for p, m, n, mod in health:
    print(",".join(m), p, n, mod)
PY

# 1) No HOC routers define /api/v1 prefixes anymore
rg -n 'prefix="/api/v1' app/hoc/api

# 2) /api/v1 is served only by 410 legacy handlers
rg -n '@router\\.api_route\\(\"/api/v1/\\{path:path\\}\"' app/hoc/api/cus/general/legacy_routes.py

# 3) /health is NOT defined in app.main (single-owner rule)
rg -n '@app\\.get\\(\"/health\"\\)' app/main.py

# 4) /health IS defined in HOC L2 health router
rg -n '@router\\.get\\(\"/health\"\\)' app/hoc/api/cus/general/health.py

# 5) No duplicate (path, method) FastAPI routes
pytest -q tests/hoc_spine/test_no_duplicate_routes.py

# 5b) /api/v1 is legacy-only (never canonical)
pytest -q tests/hoc_spine/test_api_v1_legacy_only.py

# 6) Hygiene scan is green
python3 scripts/ci/check_init_hygiene.py --ci
```

---

## Design Summary (First Principles)

- Canonical HOC routes no longer use `/api/v1`.
- `app/hoc/api/cus/general/legacy_routes.py` provides a `410 Gone` catch-all for `/api/v1/{path:path}` with migration guidance.
- `/health` is owned by L2 (`app/hoc/api/cus/general/health.py`) and delegates DB validation to hoc_spine via `registry.execute("system.health", ...)`.
- DB validation is implemented in hoc_spine L4 handler `app/hoc/cus/hoc_spine/orchestrator/handlers/system_handler.py` (self-contained short-lived session ping).
