# PIN-313: Governance Hardening & Gap Closure

**Status:** COMPLETE
**Created:** 2026-01-05
**Completed:** 2026-01-05
**Category:** Governance / Gap Closure

---

## Summary

Master TODO for governance layer hardening and business-logic fixes for the remaining 4 capability gaps. No frontend. No inference. Pure governance enforcement.

---

## Objective

1. Prevent regression via capability surveyor at bootstrap
2. Enforce capability truth at runtime
3. Close remaining gaps with correct business logic

---

## Global Invariants

**Claude MUST:**
- Treat `CAPABILITY_REGISTRY.yaml` as system of record
- Run capability surveyor before any task
- Stop immediately on unregistered code
- Separate advisory, control, and audit semantics

**Claude MUST NOT:**
- Infer capability intent
- Promote lifecycle without closure
- Add UI
- Create mutation paths in advisory planes

---

## Phase 1 — Governance Layer Additions

| Task | Description | Status |
|------|-------------|--------|
| T1.1 | Add Capability Surveyor to Bootstrap | COMPLETE |
| T1.2 | Add Registry Gate to Session Start | COMPLETE |
| T1.3 | Add Unregistered Code Response Matrix | COMPLETE |
| T1.4 | Reinforce Promotion Gate | COMPLETE |

---

## Phase 2 — Gap-Specific Business Logic Fixes

### GAP A — cost_simulation (PARTIAL → CLOSED)

| Task | Description | Status |
|------|-------------|--------|
| T2.1 | Introduce SimulationRun artifact | COMPLETE (ProvenanceLog exists) |
| T2.2 | Wire audit capture | COMPLETE (provenance_async.py) |
| T2.3 | Update registry to CLOSED | COMPLETE |

### GAP B — policy_proposals (READ_ONLY → COMPLETE)

| Task | Description | Status |
|------|-------------|--------|
| T2.4 | Add origination semantics | COMPLETE (exists in PolicyProposal model) |
| T2.5 | Registry confirmation (stay READ_ONLY) | COMPLETE |

### GAP C — prediction_plane (READ_ONLY → SAFE)

| Task | Description | Status |
|------|-------------|--------|
| T2.6 | Add visibility-only RBAC | COMPLETE (require_predictions_read exists) |
| T2.7 | Registry update (authority_model_defined) | COMPLETE |

### GAP D — cross_project (PLANNED — NO ACTION)

| Task | Description | Status |
|------|-------------|--------|
| T2.8 | Add governance assertion only | COMPLETE |

---

## Phase 3 — Recheck & Lock

| Task | Description | Status |
|------|-------------|--------|
| T3.1 | Re-run surveyor | COMPLETE |
| T3.2 | Update governance records | COMPLETE |

---

## Completion Criteria

- [x] cost_simulation = CLOSED (ProvenanceLog provides audit)
- [x] policy_proposals = READ_ONLY (complete) - origination semantics exist
- [x] prediction_plane = READ_ONLY (gated) - visibility-only RBAC confirmed
- [x] cross_project untouched - governance assertion added
- [x] Surveyor passes on repeat runs

---

## Stop Conditions (Absolute)

Claude MUST STOP if:
- New capability appears
- Any advisory plane gains mutation
- cost_simulation audit is incomplete
- Registry validation fails

---

## Final Results

### Registry State Achieved

| Metric | Before | After |
|--------|--------|-------|
| Total Capabilities | 18 | 18 |
| CLOSED | 14 | 15 |
| PARTIAL | 1 | 0 |
| READ_ONLY | 2 | 2 |
| PLANNED | 1 | 1 |
| Blocking Gaps | 4 | 0 |

### Key Discoveries

1. **cost_simulation (CAP-002):** ProvenanceLog already provides full audit trail with input/output hashes, compressed payloads, version tracking, and DB persistence. Registry was corrected to CLOSED.

2. **policy_proposals (CAP-003):** Origination semantics exist via PolicyProposal model (proposal_type, triggering_feedback_ids, tenant_id). READ_ONLY is the correct final state by design (PB-S4 invariant).

3. **prediction_plane (CAP-004):** Visibility-only RBAC confirmed via require_predictions_read. All access audited. READ_ONLY advisory is correct final state (PB-S5 invariant).

4. **cross_project (CAP-017):** Governance assertion added. PLANNED state is intentional. P0 violation if implemented without registry promotion.

### Files Modified

| File | Changes |
|------|---------|
| `SESSION_PLAYBOOK.yaml` | v2.32 → v2.33, Section 35 added (Capability Registry Governance) |
| `CAPABILITY_REGISTRY.yaml` | cost_simulation CLOSED, policy_proposals complete, prediction_plane RBAC confirmed |
| `GAP_HEATMAP.md` | Regenerated (0 blocking gaps) |

---

## Related PINs

- [PIN-306](PIN-306-capability-registry-governance.md) — Registry governance
- [PIN-312](PIN-312-cap018-approval-registry-stable.md) — CAP-018 approval
