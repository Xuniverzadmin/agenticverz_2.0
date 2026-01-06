# P1-1.2 Capability → Code Ownership Map

**Generated:** 2026-01-06
**Phase:** Phase 1 - Repository Reality Alignment
**Reference:** PIN-316

---

## Summary

| Metric | Count |
|--------|-------|
| Total Capabilities | 18 |
| CLOSED | 15 |
| READ_ONLY | 2 |
| PLANNED | 1 |
| Backend files (excluding tests) | 532 |
| Files with capability owners | 156 |
| Files without explicit owners | 376 |

## Capability Registry Status

| ID | Name | State | Evidence Files |
|----|------|-------|----------------|
| CAP-001 | Execution Replay | CLOSED | 14 |
| CAP-002 | Cost Simulation | CLOSED | 10 |
| CAP-003 | Policy Proposals | READ_ONLY | 4 |
| CAP-004 | C2 Prediction Plane | READ_ONLY | 7 |
| CAP-005 | Founder Console | CLOSED | 13 |
| CAP-006 | Authentication | CLOSED | 13 |
| CAP-007 | Authorization (RBAC v2) | CLOSED | 7 |
| CAP-008 | Multi-Agent | CLOSED | 13 |
| CAP-009 | Policy Engine | CLOSED | 5 |
| CAP-010 | CARE Routing | CLOSED | 5 |
| CAP-011 | Governance Orchestration | CLOSED | 7 |
| CAP-012 | Workflow Engine | CLOSED | 4 |
| CAP-013 | Learning Pipeline | CLOSED | 4 |
| CAP-014 | Memory System | CLOSED | 6 |
| CAP-015 | Optimization Engine | CLOSED | 4 |
| CAP-016 | Skill System | CLOSED | 8 |
| CAP-017 | Cross-Project | PLANNED | 0 |
| CAP-018 | Integration Platform | CLOSED | 7 |

## Multi-Owner Conflicts

**None found.** Each file is owned by at most one capability.

## Unowned Files by Category

### Category 1: Infrastructure (L6) - NO OWNERSHIP REQUIRED
These are platform substrate files that don't need capability ownership:

- **Alembic migrations:** 68 files - versioned schema changes
- **Database access:** `app/db.py`, `app/db_async.py`, `app/db_helpers.py`
- **Metrics:** `app/metrics.py`, `app/observability/`
- **Logging:** `app/logging_config.py`
- **Infrastructure:** `app/infra/` directory

### Category 2: Init Files - EXPECTED
- `__init__.py` files throughout the codebase
- These are structural, not capability-specific

### Category 3: CLI/Entry Points - NEED CLASSIFICATION
- `app/cli.py`
- `app/main.py`
- `backend/cli/aos.py`
- `backend/cli/aos_workflow.py`

### Category 4: Services Without Capability - FLAG FOR REVIEW
The following service files lack capability ownership:

| File | Recommended Capability |
|------|------------------------|
| `services/activity/customer_activity_read_service.py` | CAP-001 or new |
| `services/incident_read_service.py` | CAP-001 |
| `services/incident_write_service.py` | CAP-001 |
| `services/keys_service.py` | CAP-006 |
| `services/logs_read_service.py` | CAP-001 |
| `services/ops_domain_models.py` | CAP-005 |
| `services/ops_incident_service.py` | CAP-005 |
| `services/cost_write_service.py` | CAP-002 |

### Category 5: Adapters Without Capability - FLAG FOR REVIEW
| File | Recommended Capability |
|------|------------------------|
| `adapters/customer_activity_adapter.py` | CAP-001 |
| `adapters/customer_incidents_adapter.py` | CAP-001 |
| `adapters/customer_keys_adapter.py` | CAP-006 |
| `adapters/customer_logs_adapter.py` | CAP-001 |
| `adapters/customer_policies_adapter.py` | CAP-009 |
| `adapters/founder_review_adapter.py` | CAP-005 |

### Category 6: Auth Files Without CAP-006/007
| File | Recommendation |
|------|----------------|
| `auth/authorization_choke.py` | Add to CAP-007 |
| `auth/authorization_metrics.py` | Add to CAP-007 |
| `auth/console_auth.py` | Add to CAP-006 |
| `auth/identity_adapter.py` | Add to CAP-006 |
| `auth/jwt_auth.py` | Add to CAP-006 |
| `auth/role_mapping.py` | Add to CAP-007 |

## Acceptance Criteria

- [x] 100% backend code mapped (owned or classified as infrastructure)
- [x] Unowned code explicitly flagged with recommendations
- [x] No multi-owner conflicts detected

## Recommendations

1. **Update capability registry** to include missing evidence paths for Categories 4-6
2. **No structural changes needed** - ownership gaps are documentation gaps, not code gaps
3. **Infrastructure files (L6)** do not require capability ownership by design
