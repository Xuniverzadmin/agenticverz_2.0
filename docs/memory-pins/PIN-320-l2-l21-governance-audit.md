# PIN-320: L2 → L2.1 Governance Audit (Part 1)

**Status:** COMPLETE
**Created:** 2026-01-06
**Category:** Governance / Architecture Audit
**Scope:** Backend (L2) to Frontend (L2.1) binding governance

---

## Summary

Comprehensive governance audit to discover what structures exist for binding L2 backend capabilities to L2.1 frontend execution. This audit is Part 1 of the L2↔L2.1 binding layer design effort.

---

## Objective

Extract reality about ALL existing governance mechanisms relevant to:
- Capability declaration and registration
- Frontend legitimacy to invoke backend routes
- Feedback loop governance
- Enforcement surfaces

**Constraint:** Discovery only, no new governance invented.

---

## Governance Mechanisms Inventory

### Authoritative (Enforced)

| Mechanism | Source of Truth | Enforcement |
|-----------|-----------------|-------------|
| Capability Registry | `/docs/capabilities/CAPABILITY_REGISTRY.yaml` | CI + Bootstrap |
| BLCA Layer Validator | `/scripts/ops/layer_validator.py` | CI + Session |
| Permission Taxonomy | `/docs/governance/PERMISSION_TAXONOMY_V1.md` | Runtime (authority.py) |
| System Contracts | `/docs/contracts/INDEX.md` | Runtime (decision records) |
| Page Registry (BIT) | `/website/app-shell/tests/bit/page-registry.yaml` | CI |

### Declarative Only (Not Enforced)

| Mechanism | Source of Truth | Status |
|-----------|-----------------|--------|
| Codebase Registry | `/docs/codebase-registry/artifacts/*.yaml` | Survey-state |
| Visibility Contract | `/docs/contracts/visibility_contract.yaml` | Phase B |
| Signal Registry | `/docs/architecture/SIGNAL_REGISTRY_COMPLETE.md` | Frozen baseline |
| Visibility Lifecycle | `/docs/contracts/visibility_lifecycle.yaml` | Design only |

---

## Capability Visibility Status

### Registration

- **18 capabilities** registered in CAPABILITY_REGISTRY.yaml
- States: PLANNED (1), READ_ONLY (2), CLOSED (15)
- Manual registration process (Claude + Founder)

### What is EXPLICIT

| Attribute | Location |
|-----------|----------|
| Capability planes (engine, l2_api, client, ui, authority, audit_replay) | Registry |
| Lifecycle state | Registry |
| UI expansion permission | Registry `governance.ui_expansion_allowed` |
| Evidence paths | Registry |
| Founder approval requirement | Registry |

### What is INFERRED (UNGOVERNED)

| Attribute | Impact |
|-----------|--------|
| API input schemas | Frontend cannot type-check |
| API output shapes | Frontend type safety unknown |
| Side-effect classification | Cannot distinguish safe/mutating |
| Error response shapes | Error handling unpredictable |

---

## Frontend Legitimacy Status

### Partial Governance Exists

The Capability Registry has `ui_expansion_allowed` flag:
- **BLOCKED (7):** cross_project, care_routing, authorization, workflow_engine, learning_pipeline, optimization_engine, skill_system
- **ALLOWED (11):** replay, prediction_plane, cost_simulation, policy_proposals, founder_console, memory_system, policy_engine, governance_orchestration, authentication, multi_agent, integration_platform

### Critical Gap

**No L2.1-to-L2 binding contract exists.**

The system governs *whether* UI can be built, but NOT:
- Which specific L2 endpoints can be called from which frontend client
- Which API client files are authorized for which routes
- Per-endpoint invocation legitimacy

---

## Gap Ledger

| Gap ID | Missing Capability | Severity |
|--------|-------------------|----------|
| G-001 | No L2.1-to-L2 binding registry | HIGH |
| G-002 | No API input/output schema registry | HIGH |
| G-003 | No explicit side-effect classification per endpoint | MEDIUM |
| G-004 | Codebase Registry is declarative only | MEDIUM |
| G-005 | No frontend capability discovery mechanism | HIGH |
| G-006 | Visibility Contract Phase B (not runtime-enforced) | MEDIUM |
| G-007 | No error response shape contract | LOW |
| G-008 | No explicit human-vs-system action classification | LOW |

---

## Key Finding

The system has **vertical governance** (L1→L2→L4→L6 layer discipline via BLCA) but **no horizontal binding** (L2 backend routes ↔ L2.1 frontend clients).

**No governance today explicitly answers:**
> "Can this frontend API client file invoke this backend route?"

---

## Frontend API Client Inventory

26 API client files exist in `/website/app-shell/src/api/`:

```
agents.ts, auth.ts, blackboard.ts, client.ts, costsim.ts,
credits.ts, explorer.ts, failures.ts, guard.ts, health.ts,
integration.ts, jobs.ts, killswitch.ts, memory.ts, messages.ts,
metrics.ts, operator.ts, ops.ts, recovery.ts, replay.ts,
runtime.ts, sba.ts, scenarios.ts, timeline.ts, traces.ts, worker.ts
```

None of these files are linked to Capability Registry capabilities via governance contract.

---

## Enforcement Surface Summary

| Location | Hard Block | Warning | Ignored |
|----------|------------|---------|---------|
| CI | Capability Registry, BLCA, Page Registry | Visibility Contract | Codebase Registry |
| Runtime | Permission Taxonomy (403) | - | Signal Registry |
| Session Bootstrap | BLCA, Capability Surveyor | - | - |

---

## Next Steps (Part 1.5)

This audit provides the before-state for binding strategy design:

1. **Identify what can be reused** from existing governance
2. **Determine what must be extended** (e.g., Capability Registry)
3. **Decide what must be added** - explicitly and minimally

---

## References

- PIN-306: Capability Registry Governance
- PIN-240: Seven-Layer Codebase Mental Model
- PIN-252: Backend Signal Registry Complete
- PIN-237: Codebase Registry Survey
- PIN-245: Integration Integrity System (Architecture Governor)

---

## Files

- This PIN
- `/docs/capabilities/CAPABILITY_REGISTRY.yaml`
- `/docs/contracts/visibility_contract.yaml`
- `/docs/contracts/visibility_lifecycle.yaml`
- `/scripts/ops/layer_validator.py`
- `/website/app-shell/src/api/*.ts` (26 files)
