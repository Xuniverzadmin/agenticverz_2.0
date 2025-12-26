# PIN-177: Phase 5E - Visibility & Surfacing Matrix

**Status:** ACTIVE
**Category:** Operations / Final Review / Visibility Audit
**Created:** 2025-12-26
**Milestone:** Post-WRAP (Internal) - Pre-Beta Visibility Pass

---

## Scope Lock

> **This is NOT a build phase.**
> This is a **systematic visibility pass** across Founder Console and Customer Console.
>
> No behavior changes.
> No new features.
> Only **exposing what already exists**.

---

## Executive Summary

Phase 5E answers one question:

> **Can the founder and customer see everything the system already does?**

If capability exists but is not visible:
1. **Founder-only visibility gap** → goes to Founder Console
2. **Customer visibility gap** → goes to Customer Console
3. **Intentionally invisible** → document *why*

Anything else = ambiguity = bug.

---

## Visibility Rules (Non-Negotiable)

### Rule 1: Founder First

> **Founder sees everything before customers see anything.**

The Founder Console must show:
- Decision timelines (all decision_records)
- Routing decisions (CARE, baseline vs optimized)
- Recovery attempts (R1/R2/R3 classification)
- Budget enforcement (hard halts)
- Policy blocks (pre-check failures)
- CARE optimization decisions
- Run attempts + retries
- Kill-switch state

If the founder cannot answer *"what happened and why?"* — we are not ready for beta.

### Rule 2: Customer Effects Only

Customer Console rules:
- Sees **effects**, not mechanics
- Sees **warnings**, not decisions
- Sees **outcomes**, not governance
- Sees **predictability**, not internals

Example:
- Founder sees: `RECOVERY_EVALUATION → R2 suggested`
- Customer sees: `Execution could not proceed automatically`

Same truth, different abstraction.

---

## M0-M27 Visibility Matrix

### Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Visible and working |
| ❌ | Capability exists but NOT visible |
| ⚠️ | Partially visible |
| 🔒 | Intentionally invisible (internal only) |
| N/A | Not applicable for this audience |

---

### Core Infrastructure (M0-M4)

| Milestone | Capability | Founder Can See | Customer Can See | Gap Type |
|-----------|-----------|-----------------|------------------|----------|
| **M0 Auth/Identity** | API key validation | ⚠️ (indirect) | ❌ | UI: Key status display |
| **M0 Auth/Identity** | Tenant isolation | 🔒 | 🔒 | Intentional |
| **M1 Runtime** | Run execution | ✅ (timeline) | ✅ (status) | OK |
| **M1 Runtime** | Query API | ✅ | ❌ | Customer: Queryable status |
| **M2 Skills** | Skill inventory | ❌ | ❌ | UI: Skill browser |
| **M2 Skills** | Skill execution | ✅ (in timeline) | ⚠️ (outcome only) | OK |
| **M3 Integration** | Webhook delivery | ⚠️ (logs) | ❌ | UI: Webhook status |
| **M3 Integration** | External API calls | ⚠️ (traces) | ❌ | Founder: Call log |
| **M4 Workflow** | Workflow execution | ✅ (timeline) | ⚠️ (outcome) | OK |
| **M4 Workflow** | Checkpoint/resume | 🔒 | 🔒 | Intentional |
| **M4 Workflow** | Deterministic seed | 🔒 | 🔒 | Intentional |

---

### Safety & Governance (M5-M7)

| Milestone | Capability | Founder Can See | Customer Can See | Gap Type |
|-----------|-----------|-----------------|------------------|----------|
| **M5 Policy** | Policy evaluation | ✅ | ⚠️ (blocked msg) | OK |
| **M5 Policy** | Pre-check results | ✅ (decision_records) | ❌ | OK (mechanics hidden) |
| **M5 Policy** | Violations list | ✅ | ❌ | OK (internal) |
| **M6 Cost** | Token usage | ✅ | ✅ | OK |
| **M6 Cost** | Cost per run | ✅ | ✅ | OK |
| **M6 Cost** | Budget limits | ✅ | ⚠️ (warning only) | OK |
| **M6 Cost** | Hard halt events | ✅ (decision_records) | ⚠️ (halted msg) | OK |
| **M7 Memory** | Memory injection | ✅ | 🔒 | Intentional |
| **M7 RBAC** | Permission checks | ⚠️ (denied msg) | ⚠️ (denied msg) | OK |
| **M7 RBAC** | Role assignments | ❌ | N/A | UI: Role manager |

---

### Operational Intelligence (M8-M14)

| Milestone | Capability | Founder Can See | Customer Can See | Gap Type |
|-----------|-----------|-----------------|------------------|----------|
| **M8 Rate Limits** | Rate limit status | ⚠️ (429 error) | ⚠️ (429 error) | UI: Rate display |
| **M8 Mismatch** | Mismatch events | ❌ | N/A | UI: Mismatch log |
| **M9 Failure Catalog** | Failure classification | ✅ (in timeline) | ❌ | OK (mechanics hidden) |
| **M10 Recovery** | Recovery evaluation | ✅ (decision_records) | ❌ | OK (mechanics hidden) |
| **M10 Recovery** | R1/R2/R3 classification | ✅ | 🔒 | Intentional |
| **M10 Recovery** | Recovery suggestions | ✅ (decision_records) | ❌ | OK (founder only) |
| **M11 Skills** | Skill registry | ❌ | ❌ | UI: Skill catalog |
| **M11 Skills** | Store factories | 🔒 | 🔒 | Intentional |
| **M12 Multi-Agent** | Agent spawning | ✅ (timeline) | ⚠️ (outcome) | OK |
| **M12 Multi-Agent** | Blackboard state | ❌ | 🔒 | Founder: Blackboard view |
| **M13 Cost Calc** | Iterations costing | ✅ | ✅ | OK |
| **M14 Prompt Cache** | Cache hit rate | ❌ | 🔒 | Founder: Cache stats |

---

### Governance Layer (M15-M20)

| Milestone | Capability | Founder Can See | Customer Can See | Gap Type |
|-----------|-----------|-----------------|------------------|----------|
| **M15 BudgetLLM** | A2A cost governance | ⚠️ (cost totals) | ⚠️ (cost totals) | UI: Detailed breakdown |
| **M15.1 SBA** | Strategy cascade | ❌ | N/A | UI: SBA Inspector |
| **M15.1 SBA** | Fulfillment metrics | ❌ | N/A | UI: Heatmap |
| **M16 Governance** | SBA Inspector page | ❌ | N/A | UI: Already built (surface) |
| **M17 CARE** | Routing decisions | ✅ (decision_records) | 🔒 | OK |
| **M17 CARE** | Agent selection | ✅ (in decision) | 🔒 | Intentional |
| **M17 CARE** | Confidence scores | ❌ | 🔒 | Founder: Confidence display |
| **M18 CARE-L** | Learning signals | 🔒 | 🔒 | Intentional |
| **M18.3 Metrics** | Dashboard metrics | ❌ | ❌ | UI: Metrics dashboard |
| **M19 Policy Layer** | Constitutional rules | ✅ (policy state) | 🔒 | OK |
| **M19 Policy Layer** | Risk ceilings | ✅ (policy API) | 🔒 | OK |
| **M20 Policy Compiler** | Compiled policies | 🔒 | 🔒 | Intentional |

---

### Product Consoles (M21-M28)

| Milestone | Capability | Founder Can See | Customer Can See | Gap Type |
|-----------|-----------|-----------------|------------------|----------|
| **M21 Tenant/Auth** | Tenant management | ⚠️ (API only) | N/A | UI: Tenant admin |
| **M21 Billing** | Usage billing | ❌ | ❌ | UI: Billing dashboard |
| **M22 KillSwitch** | Kill-switch state | ❌ | N/A | UI: Kill-switch toggle |
| **M22 KillSwitch** | Emergency stop | ⚠️ (API only) | N/A | UI: Emergency button |
| **M23 Guard Console** | Incident list | ✅ | ✅ | OK |
| **M23 Guard Console** | Evidence packs | ✅ | ⚠️ (limited) | OK |
| **M24 Ops Console** | System pulse | ✅ | N/A | OK |
| **M24 Ops Console** | At-risk customers | ✅ | N/A | OK |
| **M24 Ops Console** | Feature stickiness | ✅ | N/A | OK |
| **M25 Integration** | Integration status | ⚠️ (API) | ❌ | UI: Integration panel |
| **M26 Cost Intel** | Cost attribution | ✅ | ⚠️ (summary) | OK |
| **M27 Cost Loop** | Cost enforcement | ✅ (decision_records) | ⚠️ (warning) | OK |
| **M28 Unified Console** | Consolidated view | ⚠️ (in progress) | ⚠️ (in progress) | UI: Complete |

---

## Phase 5D Decisions (Newly Added)

| Decision Type | Founder Can See | Customer Can See | Gap Type |
|--------------|-----------------|------------------|----------|
| `BUDGET_ENFORCEMENT` | ✅ (decision_records) | ⚠️ (halted message) | OK |
| `POLICY_PRE_CHECK` | ✅ (decision_records) | ⚠️ (blocked message) | OK |
| `RECOVERY_EVALUATION` | ✅ (decision_records) | ❌ | OK (mechanics hidden) |
| `CARE_ROUTING_OPTIMIZED` | ✅ (decision_records) | 🔒 | Intentional |

---

## Gap Summary

### Founder Console Gaps (Priority)

| Gap ID | Capability | Current | Needed |
|--------|-----------|---------|--------|
| F-01 | Skill browser | API only | UI catalog |
| F-02 | Blackboard state | Not visible | UI view |
| F-03 | Cache hit rate | Not visible | Stats panel |
| F-04 | SBA Inspector | Built but not linked | Surface in nav |
| F-05 | Confidence scores | In decision_records | Display in timeline |
| F-06 | Metrics dashboard | Built but not linked | Surface |
| F-07 | Kill-switch toggle | API only | UI button |
| F-08 | Role manager | Not visible | Admin UI |
| F-09 | Integration panel | API only | UI panel |
| F-10 | Decision timeline | decision_records exist | Unified timeline view |

### Customer Console Gaps (Secondary)

| Gap ID | Capability | Current | Needed |
|--------|-----------|---------|--------|
| C-01 | API key status | Not visible | Status indicator |
| C-02 | Webhook status | Not visible | Delivery status |
| C-03 | Rate limit display | 429 only | Usage meter |
| C-04 | Billing dashboard | Not visible | Usage/billing view |

### Intentionally Invisible (Documented)

| Capability | Why Invisible |
|-----------|---------------|
| Tenant isolation | Internal infrastructure |
| Checkpoint/resume | Internal mechanics |
| Deterministic seed | Internal determinism |
| Memory injection details | Privacy boundary |
| R1/R2/R3 classification | Internal recovery logic |
| Store factories | Internal abstraction |
| CARE learning signals | Internal optimization |
| Policy compiler | Internal compilation |
| CARE agent selection | Internal routing |

---

## Surfacing Priority

### Phase 5E-1: Founder Timeline (Critical for Beta)

**Objective:** Unified decision timeline in Founder Console

Surface these in order:
1. `decision_records` query → founder timeline
2. All 5 decision types visible
3. Explainability fields displayed
4. Chronological order with causal links

### Phase 5E-2: Kill-Switch & Emergency Controls

**Objective:** Instant access to safety controls

Surface:
1. Kill-switch toggle (CARE optimization)
2. Emergency stop button
3. Rate limit status

### Phase 5E-3: Existing UIs (Link Only)

**Objective:** Surface already-built UIs

Link in navigation:
1. SBA Inspector (already built)
2. Metrics dashboard (already built)
3. Guard Console (already active)

### Phase 5E-4: Customer Essentials

**Objective:** Customer sees effects without mechanics

Add:
1. API key status indicator
2. Usage/rate limit meter
3. Billing summary

---

## Validation Checklist

Before beta:

- [ ] Founder can see all decision_records in timeline
- [ ] Founder can activate kill-switch from UI
- [ ] Founder can see recovery evaluations
- [ ] Founder can explain any run outcome
- [ ] Customer sees final status (not mechanics)
- [ ] Customer sees cost/usage summary
- [ ] Customer sees rate limit status

---

## Next Steps

1. **Phase 5E-1:** Implement founder decision timeline (read API + UI)
2. **Phase 5E-2:** Add kill-switch UI toggle
3. **Phase 5E-3:** Link existing UIs in navigation
4. **Phase 5E-4:** Customer essentials (post-founder)

---

## Why This Step Is Non-Optional

Without this audit:
- Beta users report "missing features" that actually exist
- You debug **perception**, not systems
- Trust erodes before market feedback begins

With this audit:
- Beta feedback is about **value**, not **visibility**
- You learn faster
- You control the narrative

---

## Completion Criteria

Phase 5E is complete when:
1. All gaps are classified (founder/customer/intentional)
2. Founder timeline shows all decisions
3. Kill-switch is accessible from UI
4. Customer sees effects without mechanics
5. This matrix is marked COMPLETE
