# Incidents Domain Architecture

**Status:** ARCHITECTURALLY STABLE
**Locked:** 2026-01-18
**Reference Migration:** YES - Use as template for other domains

---

## Domain Overview

The Incidents domain tracks system failures, violations, and anomalies that require attention or remediation.

### Topic Model (Enforced at Boundary)

| Topic | Endpoint | Semantics |
|-------|----------|-----------|
| ACTIVE | `/api/v1/incidents/active` | Unresolved incidents requiring attention |
| RESOLVED | `/api/v1/incidents/resolved` | Closed incidents with resolution |
| HISTORICAL | `/api/v1/incidents/historical` | Archived incidents (>30 days resolved) |

### Key Principle

> **Topics are boundaries, not filters.**
> Callers cannot request the wrong scope because the endpoint enforces semantics.

---

## Documents in This Directory

| Document | Purpose | Status |
|----------|---------|--------|
| `README.md` | Index and domain status | CURRENT |
| `INCIDENTS_DOMAIN_MIGRATION_PLAN.md` | V1→V2 migration history | LOCKED |
| `INCIDENTS_DOMAIN_SQL.md` | Schema and query patterns | ACTIVE |
| `INCIDENTS_DOMAIN_AUDIT.md` | Capability audit results | REFERENCE |

---

## Architecture Status

### What's Locked (Do Not Change)

| Artifact | Lock Reason |
|----------|-------------|
| Topic-scoped endpoints | Semantic boundaries enforced at API |
| CI guard (`check_incidents_deprecation.py`) | Prevents regression to generic endpoint |
| Registry locks (`REGISTRY_LOCKS.yaml`) | Blocks new capability bindings to `/incidents` |
| Deprecated capabilities (6 total) | Grandfathered, read-only |

### What's Open for Enhancement

| Area | Status | Notes |
|------|--------|-------|
| Schema columns (`contained_at`, `sla_target_seconds`) | ENHANCEMENT | Add via separate migration |
| Metrics fidelity (NULL fields) | ENHANCEMENT | Requires schema columns first |
| New capabilities on topic-scoped endpoints | ALLOWED | Must pass SDSR observation |

---

## API Surface (Current)

### Production Endpoints

| Endpoint | Method | Capability | Status |
|----------|--------|------------|--------|
| `/api/v1/incidents/active` | GET | `incidents.active_list` | OBSERVED |
| `/api/v1/incidents/resolved` | GET | `incidents.resolved_list_v2` | OBSERVED |
| `/api/v1/incidents/historical` | GET | `incidents.historical_list_v2` | OBSERVED |
| `/api/v1/incidents/metrics` | GET | `incidents.metrics_v2` | OBSERVED |
| `/api/v1/incidents/historical/trend` | GET | `incidents.historical_trend` | OBSERVED |
| `/api/v1/incidents/historical/distribution` | GET | `incidents.historical_distribution` | OBSERVED |
| `/api/v1/incidents/historical/cost-trend` | GET | `incidents.historical_cost_trend` | OBSERVED |
| `/api/v1/incidents/{id}` | GET | `incidents.detail` | OBSERVED |
| `/api/v1/incidents/{id}/evidence` | GET | `incidents.evidence` | OBSERVED |
| `/api/v1/incidents/{id}/proof` | GET | `incidents.proof` | OBSERVED |
| `/api/v1/incidents/by-run/{run_id}` | GET | `incidents.by_run` | OBSERVED |
| `/api/v1/incidents/patterns` | GET | `incidents.patterns` | OBSERVED |
| `/api/v1/incidents/recurring` | GET | `incidents.recurring` | OBSERVED |
| `/api/v1/incidents/cost-impact` | GET | `incidents.cost_impact` | OBSERVED |

### Deprecated Endpoint (Do Not Use)

| Endpoint | Method | Status | Replacement |
|----------|--------|--------|-------------|
| `/api/v1/incidents` | GET | DEPRECATED | Use topic-scoped endpoints above |

---

## Migration History

The Incidents domain underwent a **reference-quality migration** from query-param-based topic filtering to endpoint-scoped topic boundaries.

### Migration Phases (All Complete)

| Phase | Description | Date |
|-------|-------------|------|
| Phase 0 | Semantics frozen | 2026-01-18 |
| Phase 1 | 7 topic-scoped endpoints added | 2026-01-18 |
| Phase 2 | Shadow validation passed | 2026-01-18 |
| Phase 3 | Panel rebinding complete | 2026-01-18 |
| Phase 4 | Capability registry updated | 2026-01-18 |
| Phase 5 | Deprecation locked | 2026-01-18 |

### Why This Migration Matters

This migration established four properties that matter in mature systems:

1. **Semantic correctness** - Topics enforced at boundaries, not inferred by callers
2. **Control-plane truthfulness** - Capability registry matches runtime reality
3. **Mechanical enforcement** - CI + registry locks prevent regression
4. **Institutional memory** - Artifacts ensure pattern isn't "optimized away"

**Full details:** See `INCIDENTS_DOMAIN_MIGRATION_PLAN.md`

---

## For Future Maintainers

### Do NOT

- Remove `/incidents` endpoint yet (backward compatibility)
- "Simplify" registry locks
- Merge deprecated capabilities back
- Allow "temporary" bindings to generic endpoints
- Treat CI guards as optional

### DO

- Use topic-scoped endpoints for all new panels
- Run CI guard before merging any incidents-related changes
- Add new capabilities via SDSR observation (DECLARED → OBSERVED)
- Treat this migration as the template for other domains

---

## Related Documents

| Document | Location |
|----------|----------|
| Domain Migration Playbook | `docs/architecture/DOMAIN_MIGRATION_PLAYBOOK.md` |
| Capability Registry | `backend/AURORA_L2_CAPABILITY_REGISTRY/` |
| Registry Locks | `backend/AURORA_L2_CAPABILITY_REGISTRY/REGISTRY_LOCKS.yaml` |
| CI Guard | `scripts/preflight/check_incidents_deprecation.py` |
