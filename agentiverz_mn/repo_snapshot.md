# Repository Snapshot

**Date:** 2025-12-08
**Milestone:** M10 COMPLETE → M11 Next

---

## Project Status

| Milestone | Status |
|-----------|--------|
| M0-M7 | ✅ COMPLETE |
| M8: Demo + SDK + Auth | ✅ COMPLETE |
| M9: Failure Catalog v2 | ✅ COMPLETE (PIN-048) |
| **M10: Recovery Suggestion Engine** | ✅ **COMPLETE** (PIN-050) |
| M11: Skill Expansion | ⏳ NEXT |
| M12: Beta Rollout | Pending |
| M13: Console UI | Pending |

---

## M10 Deliverables (Just Completed)

| Component | File | Status |
|-----------|------|--------|
| DB Migration | `alembic/versions/017_create_recovery_candidates.py` | ✅ |
| Matcher Service | `app/services/recovery_matcher.py` | ✅ |
| FastAPI Endpoints | `app/api/recovery.py` | ✅ |
| CLI Commands | `cli/aos.py` (recovery subcommands) | ✅ |
| Prometheus Metrics | `app/metrics.py` (4 new metrics) | ✅ |
| Tests | `tests/test_recovery.py` | ✅ |
| Documentation | `docs/memory-pins/PIN-050-*.md` | ✅ |

**CLI Commands:**
```bash
aos recovery candidates --status pending
aos recovery approve --id 5 --by operator --note "verified"
aos recovery stats
```

---

## Running Services

| Service | Container | Port |
|---------|-----------|------|
| Backend | nova_agent_manager | 8000 |
| Worker | nova_worker | - |
| Database | nova_db | 5433 |
| PgBouncer | nova_pgbouncer | 6432 |
| Prometheus | nova_prometheus | 9090 |
| Grafana | nova_grafana | 3000 |
| Keycloak | keycloak | 8080 |

---

## Database Tables (M9-M10)

| Table | Purpose |
|-------|---------|
| failure_matches | M9 - Failure persistence with 12 indexes |
| failure_pattern_exports | M9 - R2 export tracking |
| **recovery_candidates** | M10 - Suggestions with confidence |
| **recovery_candidates_audit** | M10 - Approval audit trail |

---

## Key API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/recovery/suggest` | POST | Generate suggestion |
| `/api/v1/recovery/candidates` | GET | List by status |
| `/api/v1/recovery/approve` | POST | Approve/reject |
| `/api/v1/recovery/stats` | GET | Approval stats |
| `/api/v1/failures/*` | GET/PATCH | M9 failure API |

---

## Quick Commands

```bash
# Check health
curl http://localhost:8000/health

# Test recovery API
curl "http://localhost:8000/api/v1/recovery/candidates?status=all&limit=5"

# CLI test
AOS_API_BASE=http://localhost:8000 AOS_API_KEY=test python3 cli/aos.py recovery stats

# Run M10 tests
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python3 -m pytest tests/test_recovery.py -v

# Rebuild backend
docker compose up -d --build backend
```

---

## M11 Scope (Next)

Per PIN-033, M11 focuses on **Skill Expansion**:
- Production-harden `postgres_query` skill
- Production-harden `calendar_write` skill
- Add email notification skill (`/notify/email`)
- Skill versioning and deprecation workflow

---

## Session Notes

**SQLAlchemy 2.0 Compatibility:**
- All raw SQL must use `text()` wrapper
- Use `CAST(:param AS type)` not `::type` syntax
- JSONB fields may return dict or str depending on driver

**Confidence Scoring:**
- `HALF_LIFE_DAYS = 30`
- `ALPHA = 0.7` (weight for time-decay)
- `NO_HISTORY_CONFIDENCE = 0.20`
- `EXACT_MATCH_CONFIDENCE = 0.95`
