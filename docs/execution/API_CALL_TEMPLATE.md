# API Call Template (AUTHORITATIVE)

**Status:** MANDATORY
**Date:** 2025-12-28
**Reference:** SESSION_PLAYBOOK.yaml v1.3, execution_discipline.auth_contract

---

## Rule

Environment variables are NOT credentials until explicitly mapped to HTTP headers.

```
.env file → Shell environment → HTTP header → RBAC middleware
```

Claude must bridge ALL layers explicitly. Stopping at "shell environment" is a failure.

---

## Canonical Pattern (ONLY ALLOWED)

```bash
# Step 0 — Load env with export (set -a exports all sourced vars)
set -a && source /root/agenticverz2.0/.env && set +a

# Step 1 — Verify variable exists
if [ -z "$AOS_API_KEY" ]; then
  echo "AOS_API_KEY missing" && exit 1
fi

# Step 2 — Make call (EXPLICIT HEADER)
curl -s -X POST \
  -H "X-AOS-Key: $AOS_API_KEY" \
  "http://localhost:8000/api/v1/endpoint"
```

---

## Rules

| Rule | Description |
|------|-------------|
| No eval | Never use eval or nested substitution |
| No assumption | source .env does NOT imply auth |
| Explicit header | -H "X-AOS-Key: $VAR" always visible |
| Preflight first | Run check_auth_context.sh before API calls |

---

## Auth Header Format (FROZEN)

```http
X-AOS-Key: <API_KEY>
```

No alternatives. No guessing.

---

## Forbidden Patterns

```bash
# WRONG - Missing header
curl -s http://localhost:8000/api/v1/runs

# WRONG - Assuming auth from env
source .env && curl http://localhost:8000/api/v1/runs

# WRONG - Inline substitution
curl -H "X-AOS-Key: $(grep AOS_API_KEY .env | cut -d= -f2)"
```

---

## Correct Pattern

```bash
# CORRECT - Full explicit chain with export
set -a && source /root/agenticverz2.0/.env && set +a
[ -z "$AOS_API_KEY" ] && echo "Missing key" && exit 1
curl -s -X GET -H "X-AOS-Key: $AOS_API_KEY" "http://localhost:8000/api/v1/runs"
```

---

## When Auth Is NOT Required

Some endpoints are PUBLIC_PATHS (no auth needed):

- `/health`
- `/metrics`
- `/api/v1/auth/`
- `/api/v1/c2/predictions/` (advisory only)
- `/docs`, `/openapi.json`, `/redoc`

For these, header can be omitted. But Claude must KNOW which paths are public, not assume.

---

## Enforcement

This template is enforced by:
1. `scripts/preflight/check_auth_context.sh` — Must pass before API calls
2. `SESSION_PLAYBOOK.yaml` — refusal_policy for missing auth
3. `CLAUDE.md` — Execution Rule (Non-Negotiable)
