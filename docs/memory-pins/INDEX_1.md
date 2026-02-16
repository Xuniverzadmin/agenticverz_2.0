# AgenticVerz 2.0 Memory Pins Index

> Last Updated: 2025-12-31
> Current Milestone: M8 Demo + SDK + Auth (⏳ IN PROGRESS)

## Memory Pin Files

| File | Purpose | Status |
|------|---------|--------|
| [CLAUDE.md](./CLAUDE.md) | Main memory pin - project overview, milestones, architecture | Active |
| [M0_FINALIZATION.md](./M0_FINALIZATION.md) | M0 completion report and deliverables | Complete |
| [PIN-009-EXTERNAL-ROLLOUT-PENDING.md](./PIN-009-EXTERNAL-ROLLOUT-PENDING.md) | Pending items for external/production rollout | Active |
| **[PIN-036-EXTERNAL-SERVICES.md](../docs/memory-pins/PIN-036-EXTERNAL-SERVICES.md)** | **External services (Neon, Clerk, etc.) credentials & integration** | Active |
| **[PIN-264-phase-2-3-feature-intent-system.md](./PIN-264-phase-2-3-feature-intent-system.md)** | **Phase-2.3 Feature Intent System (FeatureIntent + RetryPolicy)** | **COMPLETE** |
| **[PIN-265-phase-3-intent-driven-refactoring.md](./PIN-265-phase-3-intent-driven-refactoring.md)** | **Phase-3 Intent-Driven Refactoring (128 violations by blast radius)** | **IN_PROGRESS** |

**Primary Reference:** `docs/memory-pins/INDEX.md` (authoritative)

---

## External Services (M8+)

| Service | Purpose | Credentials |
|---------|---------|-------------|
| **Neon** | PostgreSQL (replaces local PG + PgBouncer) | `secrets/neon.env` |
| **Clerk** | Auth (replaces Keycloak stub) | `secrets/clerk.env` |
| **Resend** | Email delivery (M11 skill) | `secrets/resend.env` |
| **PostHog** | SDK analytics (M12 beta) | `secrets/posthog.env` |
| **Trigger.dev** | Background jobs (M9 aggregation) | `secrets/trigger.env` |
| **Cloudflare** | Workers (M9/M10 edge compute) | `secrets/cloudflare.env` |

**Load all:** `source /root/agenticverz2.0/secrets/load_all.sh`

---

## Project Status Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  AGENTICVERZ 2.0 (NOVA AOS)                                │
├─────────────────────────────────────────────────────────────┤
│  Vision: Deterministic, Replayable, Contract-Driven Runtime │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  M0 Foundations    [████████████████████] 100% FINALIZED   │
│  M1 Runtime        [████████████████████] 100% COMPLETE    │
│  M2 Skills         [████████████████████] 100% COMPLETE    │
│  M3 Integration    [████████████████████] 100% COMPLETE    │
│  M4 Workflow       [████████████████████] 100% SIGNED OFF  │
│  M5 Policy API     [████████████████████] 100% COMPLETE    │
│  M6 CostSim/Drift  [████████████████████] 100% COMPLETE    │
│  M6.5 Webhooks     [████████████████████] 100% VALIDATED   │
│  M7 Memory Pins    [████████████████████] 100% COMPLETE    │
│  M7 RBAC Enforce   [████████████████████] 100% ENFORCED    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## M0 Summary (FINALIZED)

### Deliverables
- 4 JSON Schemas
- 2 Specification Documents
- 6 Golden Files (examples)
- 9 CI Jobs
- 6 Test Files
- 1 Bootstrap Script

### Key Specs
- Determinism & Replay: `backend/app/specs/determinism_and_replay.md`
- Error Taxonomy (42+ codes): `backend/app/specs/error_taxonomy.md`

### CI Guardrails
| Job | Purpose |
|-----|---------|
| replay-smoke | Verify deterministic fields |
| side-effect-order | Verify ordering rules |
| metadata-drift | Warn on skill changes |

---

## M7 RBAC Enablement Status (CURRENT)

**Status:** ✅ ENFORCED (24-48h monitoring in progress)

### Session 1 - RBAC Enforcement Enabled
- ✅ Fixed docker-compose.yml (RBAC_ENFORCE, MACHINE_SECRET_TOKEN)
- ✅ Registered RBACMiddleware in main.py
- ✅ Created one-click enablement script
- ✅ PgBouncer load test: 400 TPS, 0 failures
- ✅ Smoke tests: 12 passed, 0 failed

### Session 2 - Bug Fixes & Tail Work
- ✅ Fixed RBAC audit write errors (generator session handling)
- ✅ Fixed smoke script auth (machine token for RBAC info)
- ✅ Added --non-interactive mode to one-click script
- ✅ Fixed integration tests (18 passed, 2 skipped)
- ✅ Created chaos scripts (kill_child, redis_stall, cpu_spike)
- ✅ Created GitHub Actions nightly smoke workflow
- ✅ Created runbooks (RBAC_INCIDENTS.md, MEMORY_PIN_CLEANUP.md)
- ✅ Created m7_monitoring_check.sh for 24-48h window

### Session 2 Decisions
| Decision | Choice |
|----------|--------|
| Machine role delete permission | NO - Keep least privilege |
| Drift detection in prod | Deferred to post-M8 |

### M7 Tail Work Status
| Task | Status |
|------|--------|
| 24-48h monitoring | In Progress (0h baseline done) |
| Chaos experiments | Pending (after 6h stable) |
| Prod enablement | Pending (after 24h + chaos) |

### Current Metrics (0h Baseline)
```
rbac_audit_writes_total{status="success"}: 22
rbac_audit_writes_total{status="error"}: 0
memory_pins_operations_total{status="success"}: 41
memory_pins_operations_total{status="error"}: 0
```

---

## Milestone Summary

| Milestone | Status | Notes |
|-----------|--------|-------|
| M0 | ✅ FINALIZED | Foundations & Contracts |
| M1-M2.5 | ✅ COMPLETE | Runtime + Skills + Planner |
| M3-M3.5 | ✅ COMPLETE | Core Skills + CLI + Demo |
| M4 | ✅ SIGNED OFF | Workflow Engine (24h shadow run) |
| M5 | ✅ COMPLETE | Policy API & Approval |
| M5.5 | ✅ COMPLETE | Machine-Native APIs |
| M6 | ✅ COMPLETE | CostSim V2 + Drift + Audit |
| M6.5 | ✅ VALIDATED | Webhook Externalization |
| M7 | ✅ COMPLETE | Memory Pins + Audit + Seed + TTL |

---

## Quick Reference

### Paths
```
/root/agenticverz2.0/
├── backend/
│   ├── app/
│   │   ├── schemas/      # JSON schemas
│   │   ├── specs/        # Determinism, errors
│   │   └── worker/       # Runtime (M1 target)
│   └── tests/
├── .github/workflows/    # CI
├── docker-compose.yml
└── memory-pins/          # This folder
```

### Commands
```bash
# Check status
docker ps | grep nova

# Run tests
cd /root/agenticverz2.0 && pytest

# View logs
docker logs nova_agent_manager --tail 50
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | **Phase-3 Refactoring Plan** - PIN-265 created |
| 2025-12-31 | Clustered 128 violations by feature group and blast radius |
| 2025-12-31 | Priority tiers: CRITICAL (12), HIGH (8), MEDIUM (37), LOW (27), MINIMAL (44) |
| 2025-12-31 | **Phase-2.3 Feature Intent System** - PIN-264 created |
| 2025-12-31 | Added FeatureIntent enum, RetryPolicy, @feature decorator |
| 2025-12-31 | Added CI enforcement: check_feature_intent.py |
| 2025-12-31 | Added golden examples: feature_intent_examples.py |
| 2025-12-31 | Updated SESSION_PLAYBOOK to v2.28 with intent hierarchy |
| 2025-12-07 | **External Services Configured** - PIN-036 created |
| 2025-12-07 | Credentials stored: Neon, Clerk, Resend, PostHog, Trigger.dev, Cloudflare |
| 2025-12-07 | Secrets directory secured with load_all.sh helper |
| 2025-12-07 | M8 preparation - ready for Neon/Clerk integration |
| 2025-12-05 | **M7 RBAC Session 2** - Bug fixes and tail work complete |
| 2025-12-05 | Fixed RBAC audit write errors (generator session handling) |
| 2025-12-05 | Fixed smoke script auth, added --non-interactive to one-click |
| 2025-12-05 | Created chaos scripts, nightly CI workflow, runbooks |
| 2025-12-05 | Decision: Machine role keeps least privilege (no delete) |
| 2025-12-05 | Decision: Drift detection deferred to post-M8 |
| 2025-12-05 | 0h monitoring baseline captured, 24-48h window started |
| 2025-12-05 | **M7 RBAC ENFORCED** - Session 1 complete |
| 2025-12-05 | Fixed docker-compose.yml, main.py for RBAC middleware |
| 2025-12-05 | PgBouncer load test: 400 TPS, 0 failures |
| 2025-12-04 | **M7 Memory Integration COMPLETE** - All P0/P1/P2 items done |
| 2025-12-04 | Session 3: Seed script, memory audit, TTL job, DELETE test |
| 2025-12-04 | Session 2: Migration chain, PyJWT dep, SQL binding fixes |
| 2025-12-04 | Verified: POST/GET/LIST/DELETE, RBAC endpoints, Prometheus metrics |
| 2025-12-04 | M6.5 Webhook Externalization validated |
| 2025-12-04 | M6 CostSim V2 + Drift + Audit complete |
| 2025-12-03 | M5 Policy API complete |
| 2025-12-03 | M4 signed off (24h shadow run, 0 mismatches) |
| 2025-12-01 | M0 finalized, memory pins created |
| 2025-12-01 | Ready for M1 implementation |
