# PIN-301: L2 Intent Declaration Progress - Semantic Promotion Gate

**Status:** ✅ TIER-2 COMPLETE
**Created:** 2026-01-05
**Category:** Governance / L2 Promotion
**Milestone:** Tech Debt Clearance

---

## Summary

Tracks L2 surface intent declarations per PIN-300. Tier-1 triangle complete (Logs, Activity, Incidents). Tier-2 complete (Policies, AI Console Keys). Analytics domain not yet started.

---

## Details

## Purpose

This PIN tracks the systematic declaration of L2 intent files per PIN-300 (Semantic Promotion Gate). Each customer console surface requires an explicit intent declaration before L1 can safely consume it.

## Progress Status

### Tier-1 Surfaces (COMPLETE)

| Surface | Intent File | Status | Commit |
|---------|-------------|--------|--------|
| `/guard/incidents` | L2_GUARD_INCIDENTS_INTENT.yaml | ✅ APPROVED (Gold Reference) | 6756eaee |
| `/guard/logs` | L2_GUARD_LOGS_INTENT.yaml | ✅ APPROVED | b45f6ef8 |
| `/api/v1/customer/activity` | L2_GUARD_ACTIVITY_INTENT.yaml | ✅ APPROVED | 7aad53d6 |

**Tier-1 Semantic Triangle:**
- **Logs** → Raw emissions ("This was emitted")
- **Activity** → Execution facts ("This executed in X state")
- **Incidents** → Recorded deviations ("This deviation was recorded")

This triangulation prevents performance theater, causal storytelling, and "AI decided" narratives.

### Tier-2 Surfaces (COMPLETE)

| Surface | Intent File | Status | Notes |
|---------|-------------|--------|-------|
| `/guard/policies` | L2_GUARD_POLICIES_INTENT.yaml | ✅ APPROVED | Frozen 2026-01-05 |
| `/guard/keys` | L2_GUARD_AICONSOLE_KEYS_INTENT.yaml | ✅ FROZEN | Frozen 2026-01-05, AI Console Keys |

### Tier-3 Surfaces (NOT STARTED)

| Surface | Risk Profile | Notes |
|---------|--------------|-------|
| `/guard/costs` | Tier-3 | Cost reporting surface |
| Health endpoints | Tier-3 | System health projection |

## Discipline Rules (Constitutional)

1. **One surface → full closure → frozen → next**
2. **Never promote two intents in parallel**
3. **Intent declares meaning, L1 cannot infer**
4. **Structural classification ≠ promotion eligibility**

## Key Semantic Protections by Surface

### Incidents (Gold Reference)
- `forbidden_assumptions`: system_decided, best_action, likely_cause, root_cause_known
- Calm vocabulary: urgent/action/attention/info (not critical/high/medium/low)

### Logs (Tier-1 Highest Risk)
- `explicitly_forbidden`: mutation, redaction, enrichment, correlation, interpretation
- `forbidden_assumptions`: this_log_explains_incident, log_order_is_causal

### Activity (Tier-1)
- `explicitly_forbidden`: mutation, rerun, cancellation, interpretation, aggregation, scoring
- `forbidden_assumptions`: fast_is_good, success_is_health, failure_is_incident

### Policies (Tier-2 Approved)
- `explicitly_forbidden`: mutation, threshold_exposure, effectiveness_scoring, optimization_advice
- `forbidden_assumptions`: policy_explains_incident, policy_is_effective, triggered_is_bad
- Surface-scoped prohibitions (Analytics domain may interpret, correlate, trend separately)

### AI Console Keys (Tier-2 Frozen)
- `explicitly_forbidden`: automated_lifecycle, usage_interpretation, risk_scoring, rotation_advice
- `forbidden_assumptions`: key_is_secure, key_should_rotate, usage_indicates_risk, this_is_provider_key
- `terminology_rules`: "AI Console Key" only (never "LLM key", "provider key", "secret")
- Object identity: Platform-issued credentials (NOT third-party LLM keys, NOT secrets vault)
- Authority: Control surface with manual-only lifecycle (create/revoke/rotate)
- Founder decisions: Metadata only visibility, Terminal revocation, Manual-only rotation

## Files

- `docs/intents/L2_INTENT_TEMPLATE.yaml` — Canonical template
- `docs/intents/L2_GUARD_INCIDENTS_INTENT.yaml` — Gold reference
- `docs/intents/L2_GUARD_LOGS_INTENT.yaml` — APPROVED
- `docs/intents/L2_GUARD_ACTIVITY_INTENT.yaml` — APPROVED
- `docs/intents/L2_GUARD_POLICIES_INTENT.yaml` — APPROVED
- `docs/intents/L2_GUARD_AICONSOLE_KEYS_INTENT.yaml` — FROZEN

## References

- PIN-300: Semantic Promotion Gate (Constitutional)
- PIN-298: Frontend Constitution Survey
- PIN-299: Tech Debt Clearance
- CUSTOMER_CONSOLE_V1_CONSTITUTION.md: Frozen domains

---

## Related PINs

- [PIN-300](PIN-300-.md) — Semantic Promotion Gate (Constitutional)
- [PIN-298](PIN-298-.md) — Frontend Constitution Survey
- [PIN-299](PIN-299-.md) — Tech Debt Clearance
- [PIN-302](PIN-302-tier-2-semantic-closure---policies-and-ai-console-keys.md) — Tier-2 Closure (continuation)
