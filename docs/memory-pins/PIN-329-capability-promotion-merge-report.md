# PIN-329: Capability Promotion & Merge Report

**Status:** COMPLETE
**Created:** 2026-01-06
**Category:** Governance / Capability Registry Transformation
**Scope:** All 103 DORMANT capabilities from PIN-326
**Prerequisites:** PIN-327 (Registration), PIN-328 (Decision Framework)

---

## Executive Summary

PIN-329 executes the governance decisions from PIN-328, transforming 103 DORMANT capabilities into a stable, minimal FIRST_CLASS set while internalizing agent autonomy as SUBSTRATE.

| Metric | Before (PIN-327) | After (PIN-329) | Delta |
|--------|------------------|-----------------|-------|
| FIRST_CLASS | 18 | 21 | +3 |
| DORMANT | 103 | 0 | -103 |
| SUBSTRATE | 7 | 20 | +13 |
| **Total Registered** | 128 | 41 | Consolidated |

**Key Outcome:** 100% of DORMANT capabilities processed. Zero shadow capabilities remain.

---

## Section 1: Agent Autonomy Internalization Summary

### Decision

Agent Autonomy capabilities (LCAP-001 to LCAP-010) are internal system behavior that should never be user-invokable. They are reclassified as SUBSTRATE.

### Transformation

| Previous ID | New ID | Name | Justification |
|-------------|--------|------|---------------|
| LCAP-001 | SUB-008 | Agent Lifecycle Management | Internal system behavior |
| LCAP-002 | SUB-009 | Agent Goal Submission | Internal system behavior |
| LCAP-003 | SUB-010 | Agent Run Monitoring | Internal system behavior |
| LCAP-004 | SUB-011 | Agent Memory Operations | Internal system behavior |
| LCAP-005 | SUB-012 | Agent Message Queue | Internal system behavior |
| LCAP-006 | SUB-013 | Blackboard Shared State | Internal system behavior |
| LCAP-007 | SUB-014 | Agent Job Distribution | Internal system behavior |
| LCAP-008 | SUB-015 | Agent Registration | Internal system behavior |
| LCAP-009 | SUB-016 | Agent Credits Management | Internal system behavior |
| LCAP-010 | SUB-017 | Agent Coordination Primitives | Internal system behavior |

### Worker Internalization

Worker capabilities were also internalized as SUBSTRATE:

| Previous ID | New ID | Name | Justification |
|-------------|--------|------|---------------|
| LCAP-WKR-001 | SUB-018 | Run Execution & Dispatch | System plumbing |
| LCAP-WKR-002 | SUB-019 | Failure Recovery Processing | System plumbing |
| LCAP-WKR-003 | SUB-020 | External Delivery & Outbox | System plumbing |

**Total Internalized:** 13 capabilities (10 agent autonomy + 3 workers)

### SUBSTRATE Invariants

All internalized capabilities have:
- `status: SUBSTRATE`
- `invocable: false`
- `console_scope: NONE`
- Cannot be promoted to FIRST_CLASS

---

## Section 2: LCAP to Existing CAP Merges

### Merge Principle

Capabilities were merged by **power equivalence** (what question they answer), not by route/endpoint similarity.

### Merge Summary

| Target CAP | Merged LCAPs | Count | Power |
|------------|--------------|-------|-------|
| CAP-001 (Replay & Activity) | LCAP-020 to LCAP-027, LCAP-049, LCAP-050, LCAP-058 | 11 | Observation of execution |
| CAP-002 (Cost Simulation) | LCAP-011 to LCAP-015 | 5 | Cost observation & simulation |
| CAP-004 (Prediction Plane) | LCAP-052, LCAP-053 | 2 | ML predictions |
| CAP-005 (Founder Console) | LCAP-033 to LCAP-040 | 8 | Founder operations |
| CAP-009 (Policy Engine) | LCAP-016 to LCAP-019, LCAP-051 | 5 | Policy evaluation |
| CAP-011 (Governance) | LCAP-059 | 1 | Governance review |
| CAP-014 (Memory System) | LCAP-054, LCAP-055 | 2 | Memory & embeddings |
| CAP-016 (Skill System) | LCAP-041 to LCAP-045 | 5 | Runtime APIs |
| CAP-018 (Integration) | LCAP-028 to LCAP-032, LCAP-056, LCAP-057 | 7 | Integration & recovery |

**Total Merged:** 46 LCAPs into 9 existing CAPs

### Merge Details

#### CAP-001: Execution Replay & Activity

Merged capabilities expand observation powers:
- Incident listing, search, aggregation (LCAP-020, LCAP-021, LCAP-023)
- Trace observation and determinism (LCAP-024, LCAP-025)
- Replay analysis (LCAP-027)
- Guard status and keys (LCAP-049, LCAP-050)
- Failure observation (LCAP-058)

#### CAP-002: Cost Simulation V2

Merged capabilities complete cost intelligence:
- Cost tracking and visibility (LCAP-011)
- Cost simulation V2 (LCAP-012)
- Cost anomaly detection (LCAP-013)
- Cost control (LCAP-014) - FOUNDER_ONLY
- Cost feature configuration (LCAP-015)

#### CAP-005: Founder Console

Merged capabilities expand founder operations:
- Tenant control (LCAP-033)
- Incident override (LCAP-034)
- API key management (LCAP-035)
- Ops dashboard (LCAP-036, LCAP-037)
- Timeline and controls (LCAP-038, LCAP-039)
- Explorer (LCAP-040)

#### CAP-009: Policy Engine

Merged capabilities complete policy governance:
- Policy evaluation (LCAP-016)
- Policy administration (LCAP-017) - FOUNDER_ONLY
- Policy versioning (LCAP-018)
- Conflict resolution (LCAP-019)
- Guard policies (LCAP-051)

#### CAP-016: Skill System

Merged capabilities complete runtime API:
- Simulation (LCAP-041)
- Query (LCAP-042)
- Capabilities (LCAP-043)
- Skills (LCAP-044)
- Resource contracts (LCAP-045)

#### CAP-018: Integration Platform

Merged capabilities complete integration:
- Recovery candidates (LCAP-028)
- Recovery approval (LCAP-029)
- Recovery statistics (LCAP-030)
- Recovery ingest (LCAP-031) - FORBIDDEN for customer
- Recovery checkpoints (LCAP-032)
- Integration status (LCAP-056)
- Integration webhooks (LCAP-057) - FOUNDER_ONLY

---

## Section 3: New FIRST_CLASS Capabilities Created

### Promotion Criteria

New FIRST_CLASS capabilities were created only when:
1. Unique power exists (not coverable by existing CAP)
2. Distinct governance model required
3. Execution vector requires separate tracking

### CAP-019: Run Management

**Previous IDs:** LCAP-046, LCAP-047, LCAP-048

**Uniqueness Justification:**
> Run Management introduces unique lifecycle semantics:
> - Direct run creation bypasses agent-mediated execution
> - Run control (cancel/pause/resume) is distinct power from observation
> - Cannot be merged into CAP-001 (observation) or CAP-012 (workflow engine)
> - Requires its own authority model for SDK access

**Routes:**
- `POST /api/v1/runs` - Create run
- `GET /api/v1/runs/{id}` - Get run status
- `GET /api/v1/runs` - List runs
- `POST /api/v1/runs/{id}/cancel` - Cancel run
- `POST /api/v1/runs/{id}/pause` - Pause run
- `POST /api/v1/runs/{id}/resume` - Resume run

**Console Scope:** SDK

---

### CAP-020: CLI Execution

**Previous IDs:** LCAP-CLI-001 to LCAP-CLI-010

**Uniqueness Justification:**
> CLI paths require distinct governance because:
> - CLI bypasses L2 API governance (operates at L7)
> - Client-provided parameters (--by) create impersonation risks
> - Budget and ownership validation not enforced uniformly
> - Requires umbrella capability to track all CLI authority

**Commands:**
| Command | API Endpoint | Power |
|---------|--------------|-------|
| `aos simulate --plan` | POST /api/v1/runtime/simulate | READ_ONLY |
| `aos query <type>` | POST /api/v1/runtime/query | READ_ONLY |
| `aos skills` | GET /api/v1/runtime/skills | READ_ONLY |
| `aos skill <id>` | GET /api/v1/runtime/skills/{id} | READ_ONLY |
| `aos capabilities` | GET /api/v1/runtime/capabilities | READ_ONLY |
| `aos recovery candidates` | GET /api/v1/recovery/candidates | READ_ONLY |
| `aos recovery approve/reject` | POST /api/v1/recovery/approve | WRITE |
| `aos recovery stats` | GET /api/v1/recovery/stats | READ_ONLY |
| `aos version` | GET /version | READ_ONLY |
| `aos quickstart` | GET /health | READ_ONLY |

**Implicit Authority Gaps (Carried Forward):**
- Budget checking not enforced on simulation
- No ownership validation on queries
- `--by` parameter allows impersonation on approval
- Cross-run visibility on recovery candidates

**Console Scope:** NONE (CLI-specific)

---

### CAP-021: SDK Execution

**Previous IDs:** LCAP-SDK-PY-001 to LCAP-SDK-PY-015, LCAP-SDK-JS-001 to LCAP-SDK-JS-016

**Uniqueness Justification:**
> SDK paths require distinct governance because:
> - SDK operates at L1 (client-side), bypasses L2 API governance
> - force_skill parameter bypasses planning
> - Plan injection possible via create_run
> - No agent/user ownership validation
> - Audit fields not in hash (tamperable traces)
> - Single CAP for both Python and JS (hash parity ensures same power)

**SDK Methods:**
| Method | API Endpoint | Power |
|--------|--------------|-------|
| `AOSClient.simulate()` | POST /api/v1/runtime/simulate | READ_ONLY |
| `AOSClient.query()` | POST /api/v1/runtime/query | READ_ONLY |
| `AOSClient.list_skills()` | GET /api/v1/runtime/skills | READ_ONLY |
| `AOSClient.describe_skill()` | GET /api/v1/runtime/skills/{id} | READ_ONLY |
| `AOSClient.get_capabilities()` | GET /api/v1/runtime/capabilities | READ_ONLY |
| `AOSClient.create_agent()` | POST /agents | EXECUTE |
| `AOSClient.post_goal()` | POST /agents/{id}/goals | EXECUTE |
| `AOSClient.poll_run()` | GET /agents/{id}/runs/{id} | READ_ONLY |
| `AOSClient.create_run()` | POST /api/v1/runs | EXECUTE |
| `RuntimeContext.*` | N/A | EXECUTE |
| `Trace.*` | N/A | WRITE |

**Implicit Authority Gaps (Carried Forward):**
- No agent validation on creation
- force_skill bypasses planning
- Plan parameter allows injection
- No rate limiting on polls
- Memory scoping assumed, not enforced
- Audit fields not in hash (tamperable)
- Global idempotency tracking with collision risk

**Console Scope:** NONE (SDK-specific)

---

## Section 4: Remaining DORMANT Capabilities

**Count: 0**

All 103 DORMANT capabilities from PIN-326 have been processed:

| Action | Count | Destination |
|--------|-------|-------------|
| Internalized as SUBSTRATE | 13 | SUB-008 to SUB-020 |
| Merged into existing CAPs | 46 | CAP-001 to CAP-018 |
| Promoted to new CAPs | 44 | CAP-019, CAP-020, CAP-021 |
| **Total Processed** | **103** | **0 remaining** |

---

## Section 5: Layer Violations Carried Forward

### Principle

Layer violations are **documented, not fixed** in PIN-329. This is a governance action, not an engineering refactor.

### Violations

| Capability | Violation | Status |
|------------|-----------|--------|
| SUB-018 (Run Execution) | L5 → L6 (expected by design) | DOCUMENTED |
| SUB-019 (Recovery Processing) | AUTO_EXECUTE without capability gate | DOCUMENTED |

### SUB-019 Critical Note

```
CRITICAL: Auto-execution at confidence >= 0.8 has no explicit capability gate.
This is a known authority gap carried forward for human decision.

Current behavior:
1. Worker polls recovery_candidates table
2. Claims candidates with FOR UPDATE SKIP LOCKED
3. If confidence >= 0.8 → AUTO_EXECUTE
4. No human approval required
5. No capability check
6. No audit of auto-execution decision

This is NOT fixed in PIN-329. Human decision required per PIN-328 Decision 4.
```

---

## Section 6: Final Capability Universe Summary

### Registry Statistics

| Category | Count |
|----------|-------|
| FIRST_CLASS capabilities | 21 |
| SUBSTRATE capabilities | 20 |
| DORMANT capabilities | 0 |
| **Total Registered** | **41** |

### By Execution Vector

| Vector | Count | Capabilities |
|--------|-------|--------------|
| HTTP | 18 | CAP-001 to CAP-019 |
| SDK | 2 | CAP-008, CAP-021 |
| CLI | 1 | CAP-020 |
| Worker | 1 | CAP-012 |
| None | 19 | SUBSTRATE + internal |

### By Console Scope

| Scope | Count |
|-------|-------|
| CUSTOMER | 8 |
| FOUNDER | 3 |
| SDK | 3 |
| NONE | 27 |

### Coverage

| Entry Point Type | Registered |
|------------------|------------|
| HTTP routes | 365+ |
| Workers | 9 |
| CLI commands | 10 |
| SDK methods | 31 |
| SUBSTRATE components | 20 |

### Governance Status

| Metric | Value |
|--------|-------|
| Shadow capabilities | 0 |
| DORMANT capabilities | 0 |
| Unregistered paths | 0 |
| FIRST_CLASS governed | 21 |
| **Registry Coverage** | **100%** |

---

## Negative Assertion

**Question:** Is there any executable capability NOT registered in this registry?

| PIN | Answer |
|-----|--------|
| PIN-325 | YES (92% shadow) |
| PIN-326 | NO (0% shadow, 100% dormant) |
| PIN-327 | NO (100% registered, 103 dormant) |
| **PIN-329** | **NO (100% processed, 0 dormant)** |

**Evidence:**
- 21 CAP registered with routes/methods
- 20 SUB registered with components
- 0 DORMANT remaining
- 436+ execution paths mapped

**Caveat:** This registry covers statically-discoverable capabilities. Runtime-generated routes, event-driven handlers, and plugin-loaded skills are NOT covered and require separate discovery mechanisms.

---

## Artifacts

| Artifact | Path |
|----------|------|
| Unified Registry | `docs/capabilities/CAPABILITY_REGISTRY_UNIFIED.yaml` |
| This Report | `docs/memory-pins/PIN-329-capability-promotion-merge-report.md` |
| Decision Framework | `docs/memory-pins/PIN-328-dormant-promotion-decisions.md` |
| DORMANT List | `l2_1/evidence/pin_326/LATENT_CAPABILITIES_DORMANT.yaml` |

---

## Hard Constraints Verified

| Constraint | Verified |
|------------|----------|
| No code deletion | YES |
| No refactoring | YES |
| No runtime behavior changes | YES |
| No new UI | YES |
| No new authority models | YES |
| No fragmentation per route/SDK method | YES |
| All capabilities remain registered | YES |
| Agent autonomy is INTERNAL-ONLY | YES |
| Merge by power & intent | YES |
| Layer violations carried forward | YES |

---

## Attestation

```yaml
attestation:
  date: "2026-01-06"
  pin_reference: "PIN-329"
  status: "COMPLETE"
  by: "claude"

  transformations_verified:
    agent_autonomy_internalized: 10
    workers_internalized: 3
    merged_into_existing_caps: 46
    promoted_to_new_caps: 44
    total_dormant_processed: 103
    dormant_remaining: 0

  registry_state:
    first_class: 21
    substrate: 20
    dormant: 0
    total: 41
```

---

## References

- PIN-325: Shadow Capability Forensic Audit
- PIN-326: Dormant Capability Elicitation
- PIN-327: Capability Registration Finalization
- PIN-328: DORMANT Promotion Decisions
- CAPABILITY_REGISTRY_UNIFIED.yaml

---

## Next Steps (Human Decision Required)

1. **Review implicit authority gaps** on CAP-020 (CLI) and CAP-021 (SDK)
2. **Decide on SUB-019 auto-execute** per PIN-328 Decision 4
3. **Consider RBAC definitions** for new CAPs (CAP-019, CAP-020, CAP-021)
4. **Update INDEX.md** with PIN-329 reference
