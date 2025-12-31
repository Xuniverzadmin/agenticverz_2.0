# PIN-261: Product Development Contract v3 — Stabilization → Productization

**Serial:** PIN-261
**Title:** Product Development Contract v3 — Stabilization → Productization
**Category:** Governance / Product Strategy
**Status:** RATIFIED
**Created:** 2025-12-31
**Authority:** Human-approved governance contract

---

## Executive Summary

This PIN ratifies the Product Development Contract v3, which establishes:

> **You are now in stabilization → productization, not invention.**
> **CI is the spine. Consoles are the skin. Lifecycle is the muscle.**

The contract defines 6 phases with strict dependency ordering, ensuring:
- No missed work
- No premature scaling
- No erosion of governance
- Clear session start point

---

## Why This Contract Exists

Previous sessions exhibited:
1. Proposing "new products" that were existing domains (fixed by PIN-260)
2. Underweighting CI stabilization as "side work"
3. Unclear starting points for new sessions
4. Phase-skipping temptations

This contract eliminates ambiguity about:
- What phase we're in
- What work is allowed
- What must complete before moving forward

---

## Supremacy Order

```
Governance → CI → Product → UX
```

This means:
1. Governance rules cannot be overridden by CI needs
2. CI stability cannot be sacrificed for product features
3. Product correctness takes precedence over UX polish
4. UX improvements come last

---

## Phase Summary

| Phase | Name | Status | Blocking |
|-------|------|--------|----------|
| 0 | Architecture & Governance | DONE / FROZEN | - |
| 1 | CI Signal Rediscovery & Stabilization | **ACTIVE** | Highest priority |
| 2 | Console & Product Surface Completion | BLOCKED | Awaiting Phase 1 |
| 3 | Customer Lifecycle & RBAC | BLOCKED | Awaiting Phase 2 |
| 4 | Commercialization & Product CI | BLOCKED | Awaiting Phase 3 |
| 5 | Support, GTM & Operability | BLOCKED | Awaiting Phase 4 |
| 6 | Optional Polish | OPTIONAL | Post-launch |

---

## Current State

```yaml
current_phase: 1
current_phase_name: "CI Signal Rediscovery & Stabilization"
phase_status: ACTIVE
next_phase_blocked_until: "Phase 1 completion criteria met"
```

---

## Phase 1 Completion Criteria

CI Signal Rediscovery & Stabilization is complete when:

- [ ] All existing CI checks inventoried in `CI_SIGNAL_REGISTRY.md`
- [ ] Each signal classified (Structural/Semantic/Behavioral/Product)
- [ ] Each signal has enforcement level (BLOCKING/ADVISORY/INFORMATIONAL)
- [ ] Each signal has owner and failure meaning
- [ ] Flaky signals resolved or removed
- [ ] Same commit = same CI result (deterministic)
- [ ] CI trusted enough to block releases
- [ ] No manual overrides except via governance ratification
- [ ] CI outcomes feed governance artifacts

---

## Console Constitution (Frozen)

| Domain | Audience | Purpose |
|--------|----------|---------|
| `console.agenticverz.com` | aos-customer | Customer trust & control |
| `fops.agenticverz.com` | aos-founder | Founder Ops control plane |
| `preflight-console.agenticverz.com` | aos-internal | Customer UX verification |
| `preflight-fops.agenticverz.com` | aos-internal | Founder ops verification |

**Hard Rules:**
- No audience crossover
- No cookie reuse
- No feature ships without preflight

---

## Governance Hard Rules

| Rule | Enforcement |
|------|-------------|
| No federated agent identity | BLOCKED (intentionally deferred) |
| No new runtime authority | BLOCKED (architecture frozen) |
| No cross-console privilege leaks | BLOCKING |
| No CI overrides without ratification | BLOCKING |
| No Phase N+1 work until Phase N complete | BLOCKING |

---

## Session Integration

### Bootstrap Question

Every session should answer:

> "Which phase are we in, and what specific work item within that phase?"

If unclear → read `PRODUCT_DEVELOPMENT_CONTRACT_V3.md` first.

### Phase Transition Protocol

To move from Phase N to Phase N+1:
1. All completion criteria for Phase N checked
2. Human ratification obtained
3. Contract updated with new `current_phase`
4. PIN created documenting transition

---

## Artifacts Created

| Artifact | Location | Purpose |
|----------|----------|---------|
| Contract | `docs/contracts/PRODUCT_DEVELOPMENT_CONTRACT_V3.md` | Full contract |
| CI Registry | `docs/ci/CI_SIGNAL_REGISTRY.md` | Signal inventory template |
| This PIN | `docs/memory-pins/PIN-261-...` | Ratification record |

---

## Final Truth

> **CI is the spine. Consoles are the skin. Lifecycle is the muscle.**

This contract ensures we never wonder "where do we start" again.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `PRODUCT_DEVELOPMENT_CONTRACT_V3.md` | Full contract |
| `PIN-260` | Product Architecture Clarity |
| `PIN-259` | Phase G Steady-State Governance |
| `CUSTOMER_CONSOLE_V1_CONSTITUTION.md` | Frozen console structure |
| `CI_SIGNAL_REGISTRY.md` | CI signal inventory |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | PIN-261 created and ratified |
