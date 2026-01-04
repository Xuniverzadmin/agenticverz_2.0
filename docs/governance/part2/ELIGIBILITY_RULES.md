# Eligibility Rules Specification

**Status:** CONSTITUTIONAL DESIGN
**Effective:** 2026-01-04
**Reference:** SYSTEM_CONTRACT_OBJECT.md
**Layer:** L4 Domain Logic

---

## Purpose

Eligibility rules define **what MAY and MAY_NOT become a System Contract**.

Eligibility is:
- Deterministic (same input → same output)
- Machine-evaluated (no human judgment)
- Binary (MAY or MAY_NOT, no "maybe")
- Auditable (every decision has a reason)

---

## The Eligibility Engine

```
ValidatedProposal → EligibilityEngine → EligibilityVerdict
```

The engine applies rules in order. First failing rule terminates evaluation.

---

## MAY Become Contract (All Must Pass)

### Rule E-001: Validator Confidence Threshold

```yaml
rule: E-001
name: Validator Confidence Threshold
condition: validator_verdict.confidence_score >= threshold
threshold: 0.70 (configurable)
failure_reason: "Validator confidence too low"
```

**Rationale:** Low-confidence proposals require manual triage, not automation.

---

### Rule E-002: Known Capability Reference

```yaml
rule: E-002
name: Known Capability Reference
condition: ALL(affected_capabilities) IN capability_registry
failure_reason: "Unknown capability referenced: {name}"
```

**Rationale:** Cannot act on capabilities that don't exist.

---

### Rule E-003: No Blocking Governance Signal

```yaml
rule: E-003
name: No Blocking Governance Signal
condition: NOT EXISTS blocking_signal FOR scope
query: |
  SELECT * FROM governance_signals
  WHERE scope IN (affected_capabilities + 'SYSTEM')
  AND decision = 'BLOCKED'
  AND superseded_at IS NULL
failure_reason: "Blocked by governance signal: {signal_type}"
```

**Rationale:** Active blocks must be respected.

---

### Rule E-004: Actionable Issue Type

```yaml
rule: E-004
name: Actionable Issue Type
condition: validator_verdict.issue_type IN actionable_types
actionable_types:
  - capability_request
  - configuration_change
  - bug_report (with recommended_action != escalate)
failure_reason: "Issue type {type} requires manual handling"
```

**Rationale:** Some issue types cannot be automated.

---

### Rule E-005: Source Allowlist

```yaml
rule: E-005
name: Source Allowlist
condition: source IN allowed_sources
allowed_sources:
  - crm_feedback
  - support_ticket
  - ops_alert
failure_reason: "Source {source} not in allowlist"
```

**Rationale:** Only trusted sources may initiate contracts.

---

### Rule E-006: Not Duplicate

```yaml
rule: E-006
name: Not Duplicate
condition: NOT EXISTS similar_contract
query: |
  SELECT * FROM system_contracts
  WHERE affected_capabilities && $capabilities
  AND status NOT IN ('REJECTED', 'EXPIRED', 'FAILED', 'COMPLETED')
  AND created_at > NOW() - INTERVAL '24 hours'
failure_reason: "Similar contract already pending: {contract_id}"
```

**Rationale:** Prevent duplicate work.

---

## MAY_NOT Become Contract (Any Triggers Rejection)

### Rule E-100: Below Minimum Confidence

```yaml
rule: E-100
name: Below Minimum Confidence
condition: validator_verdict.confidence_score < minimum_confidence
minimum_confidence: 0.30
verdict: MAY_NOT
reason: "Confidence below minimum threshold"
```

---

### Rule E-101: Critical Without Escalation

```yaml
rule: E-101
name: Critical Without Escalation
condition: |
  validator_verdict.severity = 'critical'
  AND validator_verdict.recommended_action != 'escalate'
verdict: MAY_NOT
reason: "Critical issues must be escalated"
```

---

### Rule E-102: Frozen Capability Target

```yaml
rule: E-102
name: Frozen Capability Target
condition: ANY(affected_capabilities) IN frozen_capabilities
query: |
  SELECT capability_name FROM capability_registry
  WHERE frozen = true
verdict: MAY_NOT
reason: "Cannot modify frozen capability: {name}"
```

---

### Rule E-103: System Scope Without Founder Pre-Approval

```yaml
rule: E-103
name: System Scope Without Founder Pre-Approval
condition: |
  'SYSTEM' IN affected_capabilities
  AND NOT pre_approved_system_change
verdict: MAY_NOT
reason: "System-wide changes require pre-approval"
```

---

### Rule E-104: Health Degraded

```yaml
rule: E-104
name: Health Degraded
condition: system_health != HEALTHY
query: |
  SELECT status FROM platform_health_status
  WHERE scope = 'SYSTEM'
  ORDER BY recorded_at DESC LIMIT 1
verdict: MAY_NOT
reason: "System health degraded - no new contracts"
```

---

## Eligibility Verdict Schema

```yaml
eligibility_verdict:
  decision: ENUM(MAY, MAY_NOT)
  reason: TEXT
  rules_evaluated: INTEGER
  first_failing_rule: TEXT (nullable)
  blocking_signals: TEXT[]
  missing_prerequisites: TEXT[]
  evaluated_at: TIMESTAMP
  rules_version: TEXT
```

---

## Rule Evaluation Order

1. MAY_NOT rules (E-100 series) evaluated first
2. If any MAY_NOT triggers → immediate MAY_NOT verdict
3. MAY rules (E-001 series) evaluated in order
4. If all MAY rules pass → MAY verdict
5. If any MAY rule fails → MAY_NOT verdict

---

## Configuration

Rules are configurable via `governance_config`:

```yaml
eligibility:
  confidence_threshold: 0.70
  minimum_confidence: 0.30
  allowed_sources:
    - crm_feedback
    - support_ticket
    - ops_alert
  actionable_types:
    - capability_request
    - configuration_change
    - bug_report
  duplicate_window_hours: 24
  rules_version: "1.0.0"
```

---

## Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| ELIG-001 | Eligibility is deterministic | Pure function, no side effects |
| ELIG-002 | Every verdict has a reason | Required field |
| ELIG-003 | MAY_NOT rules take precedence | Evaluation order |
| ELIG-004 | Health degradation blocks all | E-104 priority |
| ELIG-005 | Frozen capabilities are inviolable | E-102 check |

---

## Attestation

This specification defines the eligibility rules for System Contracts.
Implementation must evaluate rules in specified order.
Rule changes require version increment and configuration update.
