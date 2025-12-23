# M28 Route Ownership Lockfile

**Status:** AUTHORITATIVE
**Last Updated:** 2025-12-23
**Milestone:** M28 Unified Console

---

> **Routes define power. Power defines trust. Trust defines your company.**

This file is the **single source of truth** for route ownership.
Every PR touching routing MUST be reviewed against this file.

---

## Persona Definitions

| Persona | Domain | Description |
|---------|--------|-------------|
| **CUSTOMER** | `console.agenticverz.com` | Customer product - status, incidents, billing |
| **FOUNDER** | `fops.agenticverz.com` | Founder ops cockpit - full system visibility |
| **DELETE** | N/A | Route must not exist in production |

---

## Route Ownership Map

### CUSTOMER Routes (`console.agenticverz.com`)

| Route | New Path | Owner | Notes |
|-------|----------|-------|-------|
| `/guard/status` | `/home` | CUSTOMER | Status board (Home tab) |
| `/guard/incidents` | `/guard/incidents` | CUSTOMER | Incident list |
| `/guard/incidents/{id}` | `/guard/incidents/{id}` | CUSTOMER | Incident detail |
| `/guard/replay/{call_id}` | `/guard/replay/{call_id}` | CUSTOMER | Decision replay |
| `/guard/incidents/{id}/export` | `/guard/exports/{id}` | CUSTOMER | Evidence export |
| `/guard/keys` | `/keys` | CUSTOMER | API key management |
| `/guard/killswitch/*` | `/guard/killswitch/*` | CUSTOMER | Emergency controls |
| `/guard/settings` | `/settings` | CUSTOMER | Console settings |
| `/guard/account` | `/account` | CUSTOMER | Organization & team |
| `/guard/support` | `/support` | CUSTOMER | Help & feedback |
| `/credits` | `/billing` | CUSTOMER | Credit/billing view |
| `/guard/snapshot/today` | `/home` (derived) | CUSTOMER | Today's metrics |
| `/costs/summary` | `/costs/summary` | CUSTOMER | Cost summary (derived) |
| `/costs/projection` | `/costs/projection` | CUSTOMER | Cost projections |

### FOUNDER Routes (`fops.agenticverz.com`)

| Route | New Path | Owner | Notes |
|-------|----------|-------|-------|
| `/ops/pulse` | `/pulse` | FOUNDER | 10-second situation awareness |
| `/ops/customers` | `/customers` | FOUNDER | Customer list |
| `/ops/customers/{id}` | `/customers/{id}` | FOUNDER | Customer detail |
| `/ops/customers/at-risk` | `/customers/at-risk` | FOUNDER | At-risk customers |
| `/ops/incidents/patterns` | `/incidents/patterns` | FOUNDER | Failure patterns |
| `/ops/infra` | `/infra` | FOUNDER | Infrastructure status |
| `/ops/playbooks` | `/playbooks` | FOUNDER | Founder playbooks |
| `/traces` | `/traces` | FOUNDER | Execution traces |
| `/traces/{runId}` | `/traces/{runId}` | FOUNDER | Trace detail |
| `/replay` | `/replay` | FOUNDER | Full replay (SDK-level) |
| `/recovery` | `/recovery` | FOUNDER | Recovery suggestions |
| `/integration/*` | `/integration/*` | FOUNDER | M25 integration loop |
| `/sba` | `/governance/sba` | FOUNDER | SBA inspector |
| `/memory` | `/memory` | FOUNDER | Memory PINs viewer |
| `/workers/*` | `/workers/*` | FOUNDER | Worker studio |
| `/infra/timers` | `/infra/timers` | FOUNDER | Systemd timers |
| `/infra/queues` | `/infra/queues` | FOUNDER | Queue status |
| `/infra/limits` | `/infra/limits` | FOUNDER | Rate limits |

### DELETE Routes (Must Not Exist)

| Route | Reason | Deleted In |
|-------|--------|------------|
| `/dashboard` | Shell route, merged into /guard | PIN-145 |
| `/skills` | SDK concept, not customer value | PIN-145 |
| `/simulation` | SDK/CLI tool | PIN-145 |
| `/jobs/*` | Simulation tools | PIN-145 |
| `/metrics` | Grafana mirror | PIN-145 |
| `/blackboard` | Legacy naming | PIN-145 |
| `/operator/*` | Merged into /ops | PIN-145 |
| `/failures` | Duplicates /ops/incidents/patterns | PIN-145 |
| `/agents` | Dead mental model | PIN-145 |
| `/messaging` | Dead feature | PIN-145 |
| `/guard/demo/*` | Demo artifacts | PIN-145 |
| `/v1/demo/*` | Demo artifacts | PIN-145 |

---

## Access Control Matrix

| Route Type | Customer Auth | Founder Auth | Notes |
|------------|---------------|--------------|-------|
| CUSTOMER | ✅ Allowed | ❌ 403 | Founder uses fops, not console |
| FOUNDER | ❌ 403 | ✅ Allowed | Customer never sees ops data |
| DELETE | ❌ 404/410 | ❌ 404/410 | Route does not exist |

---

## Cross-Domain Rules

1. **No shared cookies** between `console.*` and `fops.*`
2. **No redirects** from customer to founder domain
3. **No token reuse** across domains
4. **403 on cross-access** attempts
5. **Separate session stores** per domain

---

## Validation Commands

```bash
# Verify no deleted routes exist
grep -rn "demo\|simulation\|jobs\|operator\|skills\|metrics\|dashboard\|blackboard\|failures\|messaging" \
  --include="*.tsx" --include="*.ts" --include="*.py" \
  backend/app/api/ website/aos-console/console/src/ \
  | grep -v "\.m28_deleted" \
  | grep -v "DELETION\|DELETE\|Removed\|removed"

# Should return empty or only comments
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-23 | Initial lockfile created (PIN-147) |

---

## Review Checklist (for PRs)

Before merging any routing PR:

- [ ] Route is listed in this file
- [ ] Owner matches intended persona
- [ ] Cross-domain access blocked
- [ ] No deleted routes resurrected
- [ ] Auth middleware appropriate for persona
