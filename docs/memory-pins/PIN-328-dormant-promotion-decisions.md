# PIN-328: DORMANT Promotion Decisions

**Status:** AWAITING_HUMAN_DECISION
**Created:** 2026-01-06
**Category:** Governance / Capability Promotion
**Scope:** 103 DORMANT + 67 Authority Gaps + 41 Ungoverned + 1 Critical
**Prerequisites:** PIN-327 (Capability Registration Finalization)

---

## Objective

Provide structured decision framework for human governance of all pending capability decisions identified in PIN-327.

**Operating Mode:** DECISION CAPTURE — Claude presents options, humans decide.

---

## Executive Summary

| Decision Area | Scope | Priority | Status |
|---------------|-------|----------|--------|
| 1. DORMANT Promotion | 103 capabilities | HIGH | PENDING |
| 2. Authority Gaps | 67 capabilities | HIGH | PENDING |
| 3. CLI/SDK Governance | 41 capabilities | MEDIUM | PENDING |
| 4. Auto-Execute Gate | 1 capability | CRITICAL | PENDING |

---

## Decision 1: DORMANT Capability Promotion

### Question

> "What should happen to the 103 DORMANT capabilities discovered in PIN-326?"

### Options

| Option | Description | Implications |
|--------|-------------|--------------|
| **A** | Promote all to FIRST_CLASS | Requires authority declaration for each |
| **B** | Promote selectively | Human review of each category |
| **C** | Merge into existing CAP | Expand `allowed_routes` on existing CAP-XXX |
| **D** | Declare some FORBIDDEN | Remove code paths entirely |
| **E** | Accept as internal-only | Document but don't govern |

### Categories Requiring Decision

| Category | Count | Recommendation | Decision |
|----------|-------|----------------|----------|
| Agent Autonomy System | 10 | Promote (new CAP-019?) | `[ ]` |
| Cost Intelligence | 5 | Merge into CAP-002 | `[ ]` |
| Policy Governance | 4 | Merge into CAP-009 | `[ ]` |
| Incident Management | 4 | Merge into CAP-001 | `[ ]` |
| Trace & Replay | 4 | Merge into CAP-001 | `[ ]` |
| Recovery System (M10) | 5 | Merge into CAP-018 | `[ ]` |
| Founder Actions | 3 | Merge into CAP-005 | `[ ]` |
| Ops Console | 5 | Merge into CAP-005 | `[ ]` |
| Runtime API | 5 | Merge into CAP-016 | `[ ]` |
| Run Management | 3 | Promote (new CAP-020?) | `[ ]` |
| Guard System | 3 | Merge into CAP-001 | `[ ]` |
| Predictions | 2 | Merge into CAP-004 | `[ ]` |
| Memory System | 2 | Merge into CAP-014 | `[ ]` |
| Integration Platform | 2 | Merge into CAP-018 | `[ ]` |
| Failures & Logs | 2 | Merge into CAP-001 | `[ ]` |
| Workers | 3 | Accept as internal | `[ ]` |
| CLI | 10 | See Decision 3 | `[ ]` |
| Python SDK | 15 | See Decision 3 | `[ ]` |
| JavaScript SDK | 16 | See Decision 3 | `[ ]` |

### Human Decision Record

```yaml
decision_1:
  decided_by:
  decided_on:
  option_selected:
  notes:
```

---

## Decision 2: Authority Gaps (67 capabilities)

### Question

> "How should authority be declared for the 67 capabilities with no CAP-XXX mapping?"

### What "Authority Missing" Means

These capabilities execute power but have no:
- RBAC permissions defined
- Tenant isolation rules
- Audit trail configuration

### High-Priority Authority Gaps

| LCAP | Name | Power | Risk |
|------|------|-------|------|
| LCAP-001 | Agent Lifecycle Management | EXECUTE | Who can create/delete agents? |
| LCAP-006 | Blackboard Shared State | WRITE | Multi-agent state coordination |
| LCAP-007 | Agent Job Distribution | EXECUTE | Job queue access control |
| LCAP-046 | Run Creation | EXECUTE | Direct run (bypasses agent) |
| LCAP-048 | Run Control | CONTROL | Cancel/pause/resume runs |

### Options

| Option | Description | Implications |
|--------|-------------|--------------|
| **A** | Define RBAC for each | Full governance, maximum work |
| **B** | Batch by category | Group similar capabilities |
| **C** | Founder-only default | All ungoverned = FOUNDER scope |
| **D** | Accept as internal | Document as known limitation |

### Authority Declaration Template

For each capability requiring authority:

```yaml
capability_id: LCAP-XXX
authority_declaration:
  rbac_permissions:
    - permission_name:
      roles: []
  tenant_isolation: true/false
  audit_enabled: true/false
  console_scope: CUSTOMER/FOUNDER/SDK/NONE
```

### Human Decision Record

```yaml
decision_2:
  decided_by:
  decided_on:
  option_selected:
  notes:
```

---

## Decision 3: CLI/SDK Governance (41 capabilities)

### Question

> "How should CLI and SDK paths be governed when they bypass L2 API governance?"

### CLI Commands (10)

| LCAP | Command | Implicit Authority Issue |
|------|---------|-------------------------|
| LCAP-CLI-001 | `aos simulate --plan` | Budget checking not enforced |
| LCAP-CLI-002 | `aos query <type>` | Can query any agent (no ownership) |
| LCAP-CLI-004 | `aos skill <id>` | Exposes failure mode probabilities |
| LCAP-CLI-005 | `aos capabilities` | Reveals rate limits |
| LCAP-CLI-006 | `aos recovery candidates` | Cross-run visibility |
| **LCAP-CLI-007** | `aos recovery approve/reject` | **--by parameter impersonation** |
| LCAP-CLI-008 | `aos recovery stats` | Recovery metrics |
| LCAP-CLI-009 | `aos version` | Version info |
| LCAP-CLI-010 | `aos quickstart` | Health endpoint |

### SDK Methods (31)

| Category | Count | Key Issues |
|----------|-------|------------|
| Python SDK | 15 | No agent validation, `force_skill` bypass, plan injection |
| JavaScript SDK | 16 | Mirror Python issues, hash parity |

### Specific Risks

| Risk | LCAP | Description |
|------|------|-------------|
| **Impersonation** | LCAP-CLI-007 | `--by` parameter is client-provided |
| **Planning Bypass** | LCAP-SDK-PY-008 | `force_skill` skips planning |
| **Plan Injection** | LCAP-SDK-PY-011 | Plan parameter allows injection |
| **Hash Tampering** | LCAP-SDK-PY-014 | Audit fields not in hash |

### Options

| Option | Description | Implications |
|--------|-------------|--------------|
| **A** | Create CAP-019 (CLI Governance) | Umbrella capability for all CLI |
| **B** | Create CAP-020 (SDK Governance) | Umbrella capability for all SDK |
| **C** | Consider L1/L7 as proxies to L2 | CLI/SDK inherit L2 governance |
| **D** | Document as known limitations | Accept ungoverned for internal use |
| **E** | Fix specific risks only | Address impersonation, injection |

### Human Decision Record

```yaml
decision_3:
  decided_by:
  decided_on:
  option_selected:
  cli_governance: CAP-019 / proxy / accept
  sdk_governance: CAP-020 / proxy / accept
  fix_impersonation: true/false
  fix_plan_injection: true/false
  notes:
```

---

## Decision 4: Auto-Execute Gate (CRITICAL)

### Question

> "Should LCAP-WKR-002 (Recovery Auto-Execute) require an explicit capability gate?"

### What This Is

The M10 Recovery system (`recovery_claim_worker.py`, `recovery_evaluator.py`) automatically executes recovery actions:

```yaml
trigger: confidence >= 0.8
action: AUTO_EXECUTE recovery action
approval: NONE REQUIRED
capability_gate: NONE
```

### Current Behavior

1. Worker polls `recovery_candidates` table
2. Claims candidates with `FOR UPDATE SKIP LOCKED`
3. If confidence >= 0.8 → AUTO_EXECUTE
4. No human approval
5. No capability check
6. No audit of auto-execution decision

### Options

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | Add CAP-021 `recovery:auto_execute` | Explicit gate, full audit | More governance overhead |
| **B** | Require human approval for all recovery | No auto-execute | Slower recovery, bottleneck |
| **C** | Raise confidence threshold to 0.95 | Fewer auto-executions | Still ungated |
| **D** | Accept as designed | Document implicit authority | No change, known risk |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Incorrect auto-recovery | MEDIUM | HIGH | Option A or B |
| Recovery loop | LOW | CRITICAL | Existing rate limits |
| Audit gap | HIGH | MEDIUM | Option A |

### Human Decision Record

```yaml
decision_4:
  decided_by:
  decided_on:
  option_selected:
  create_cap_021: true/false
  confidence_threshold: 0.8/0.9/0.95
  notes:
```

---

## Summary: Quick Decision Form

Mark your decisions:

```yaml
# PIN-328 Decision Record
# Date:
# Decided By:

decision_1_dormant_promotion:
  approach: A/B/C/D/E
  create_new_caps: [CAP-019, CAP-020, ...]
  merge_into_existing: [CAP-002, CAP-009, ...]
  declare_forbidden: []
  accept_internal: [workers]

decision_2_authority_gaps:
  approach: A/B/C/D
  priority_capabilities: [LCAP-001, LCAP-006, LCAP-046, LCAP-048]
  default_scope: FOUNDER/CUSTOMER/NONE

decision_3_cli_sdk_governance:
  approach: A/B/C/D/E
  create_cap_019_cli: true/false
  create_cap_020_sdk: true/false
  fix_impersonation: true/false
  fix_plan_injection: true/false

decision_4_auto_execute:
  approach: A/B/C/D
  create_cap_021: true/false
  new_confidence_threshold: 0.8/0.9/0.95
```

---

## Artifacts

| Artifact | Path |
|----------|------|
| Unified Registry | `docs/capabilities/CAPABILITY_REGISTRY_UNIFIED.yaml` |
| DORMANT List | `l2_1/evidence/pin_326/LATENT_CAPABILITIES_DORMANT.yaml` |
| Schema V2 | `docs/capabilities/CAPABILITY_REGISTRY_SCHEMA_V2.yaml` |
| This PIN | `docs/memory-pins/PIN-328-dormant-promotion-decisions.md` |

---

## References

- PIN-325: Shadow Capability Forensic Audit
- PIN-326: Dormant Capability Elicitation
- PIN-327: Capability Registration Finalization
- CAPABILITY_REGISTRY_UNIFIED.yaml

---

## Updates

### 2026-01-06: PIN Created

- 4 decision areas documented
- Decision templates provided
- Awaiting human governance decisions

---

## Next Steps

After decisions are recorded:

1. **Execute promotions** → Update CAPABILITY_REGISTRY_UNIFIED.yaml
2. **Declare authority** → Add RBAC rules to promoted capabilities
3. **Create new CAPs** → If CAP-019, CAP-020, CAP-021 approved
4. **Fix specific risks** → If impersonation/injection fixes approved
5. **Create PIN-329** → Document execution of decisions
