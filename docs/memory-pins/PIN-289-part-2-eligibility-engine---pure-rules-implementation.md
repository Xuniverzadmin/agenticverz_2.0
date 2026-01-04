# PIN-289: Part-2 Eligibility Engine - Pure Rules Implementation

**Status:** COMPLETE
**Created:** 2026-01-04
**Category:** Governance / Part-2 Implementation
**Milestone:** Part-2 CRM Workflow System

---

## Summary

Implemented the Part-2 Eligibility Engine (L4), the second domain service in the Part-2 CRM workflow. The Eligibility Engine applies deterministic rules to decide if a validated proposal MAY or MAY_NOT become a System Contract.

---

## Details

### Eligibility Properties

| Property | Description | Enforcement |
|----------|-------------|-------------|
| **DETERMINISTIC** | Same input produces same output (ELIG-001) | Pure function, no side effects |
| **BINARY** | MAY or MAY_NOT, no "maybe" | Enum constraint |
| **AUDITABLE** | Every decision has a reason (ELIG-002) | Required field |
| **PURE** | No side effects, no writes | Protocol-based lookups |

### Invariants Implemented

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| ELIG-001 | Eligibility is deterministic | Pure function design |
| ELIG-002 | Every verdict has a reason | Required field |
| ELIG-003 | MAY_NOT rules take precedence | Evaluation order |
| ELIG-004 | Health degradation blocks all | E-104 evaluated first |
| ELIG-005 | Frozen capabilities are inviolable | E-102 check |

### MAY_NOT Rules (E-100 Series - Evaluated First)

| Rule | Name | Trigger |
|------|------|---------|
| E-104 | Health Degraded | System health != HEALTHY |
| E-100 | Below Minimum Confidence | confidence < 0.30 |
| E-101 | Critical Without Escalation | critical severity without escalate action |
| E-102 | Frozen Capability Target | any capability is frozen |
| E-103 | System Scope Without Pre-Approval | SYSTEM scope without pre-approval |

### MAY Rules (E-001 Series - All Must Pass)

| Rule | Name | Condition |
|------|------|-----------|
| E-001 | Validator Confidence Threshold | confidence >= 0.70 |
| E-002 | Known Capability Reference | all capabilities in registry |
| E-003 | No Blocking Governance Signal | no blocking signals active |
| E-004 | Actionable Issue Type | type in actionable list |
| E-005 | Source Allowlist | source in allowed list |
| E-006 | Not Duplicate | no similar pending contract |

### Rule Evaluation Order

1. MAY_NOT rules (E-100 series) evaluated first
2. If any MAY_NOT triggers → immediate MAY_NOT verdict
3. MAY rules (E-001 series) evaluated in order
4. If all MAY rules pass → MAY verdict
5. If any MAY rule fails → MAY_NOT verdict

### Protocol-Based Lookups

The engine uses protocol-based dependency injection for external data:

| Protocol | Purpose | Default Implementation |
|----------|---------|------------------------|
| `CapabilityLookup` | Check capability existence/frozen status | `DefaultCapabilityLookup` |
| `GovernanceSignalLookup` | Check for blocking signals | `DefaultGovernanceSignalLookup` |
| `SystemHealthLookup` | Get current system health | `DefaultSystemHealthLookup` |
| `ContractLookup` | Check for duplicate contracts | `DefaultContractLookup` |
| `PreApprovalLookup` | Check for system pre-approvals | `DefaultPreApprovalLookup` |

---

## Files Created

```
backend/app/services/governance/eligibility_engine.py (686 lines)
backend/tests/governance/test_eligibility_invariants.py (964 lines)
```

**Updated:**
```
backend/app/services/governance/__init__.py (added exports)
```

**Total:** 1,650 lines (implementation + tests)

---

## Test Coverage

48 invariant tests covering:

| Test Class | Count | Coverage |
|------------|-------|----------|
| TestELIG001Deterministic | 3 | Determinism, no state accumulation |
| TestELIG002ReasonRequired | 4 | Reason presence and content |
| TestELIG003MayNotPrecedence | 3 | Rule precedence |
| TestELIG004HealthBlocks | 4 | Health degradation blocking |
| TestELIG005FrozenInviolable | 3 | Frozen capability protection |
| TestE100BelowMinimumConfidence | 3 | Minimum confidence rule |
| TestE101CriticalWithoutEscalation | 3 | Critical escalation rule |
| TestE001ConfidenceThreshold | 3 | Confidence threshold rule |
| TestE002KnownCapability | 3 | Known capability rule |
| TestE003NoBlockingSignal | 3 | Blocking signal rule |
| TestE004ActionableType | 4 | Actionable type rule |
| TestE005SourceAllowlist | 3 | Source allowlist rule |
| TestE006NotDuplicate | 2 | Duplicate detection rule |
| TestE103SystemScopePreApproval | 3 | System pre-approval rule |
| TestVersionAndConfig | 2 | Version and configuration |
| TestFullPassIntegration | 2 | Full pass scenarios |

All 48 tests passing.

---

## Combined Governance Tests

```
79 tests passing (31 validator + 48 eligibility)
```

---

## CI Guard Compliance

| Guard | Status |
|-------|--------|
| Backend Structure Guard | PASS (STRUCTURE INTACT) |
| Health Lifecycle Coherence Guard | PASS (COHERENT) |

No bypass patterns detected in governance services.

---

## What Eligibility Engine Does NOT Do

| Action | Owner |
|--------|-------|
| Create contracts | Contract Service |
| Modify system state | (forbidden) |
| Validate issues | Validator Service |
| Approve anything | Founder Review |
| Execute jobs | Job Executor |
| Fetch external data | Uses injected lookups |

---

## Configuration

```yaml
eligibility:
  confidence_threshold: 0.70  # E-001
  minimum_confidence: 0.30    # E-100
  allowed_sources:            # E-005
    - crm_feedback
    - support_ticket
    - ops_alert
  actionable_types:           # E-004
    - capability_request
    - configuration_change
    - bug_report
  duplicate_window_hours: 24  # E-006
  rules_version: "1.0.0"
```

---

## Next Step

With Validator and Eligibility implemented, proceed to:
- **Contract Model** (stateful, L4)

Implementation order from here:
1. ~~Validator (pure analysis)~~ DONE (PIN-288)
2. ~~Eligibility engine (pure rules)~~ DONE (PIN-289)
3. Contract model (stateful) ← NEXT
4. Governance services
5. Founder review surface
6. Job execution
7. Audit wiring
8. Rollout projection

---

## References

- Tag: `part2-design-v1`
- PIN-284: Part-2 Design Documentation
- PIN-285: Pass 1 Static CI Guards
- PIN-286: Pass 2 Bootstrap + Semantic Guards
- PIN-287: CRM Event Schema
- PIN-288: Validator Service
- ELIGIBILITY_RULES.md

---

## Related PINs

- [PIN-284](PIN-284-.md)
- [PIN-285](PIN-285-part-2-crm-workflow-enforcement---static-ci-guards.md)
- [PIN-286](PIN-286-part-2-enforcement-pass-2---bootstrap-and-semantic-guards.md)
- [PIN-287](PIN-287-crm-event-schema---part-2-workflow-initiator-schema.md)
- [PIN-288](PIN-288-part-2-validator-service---pure-analysis-implementation.md)
