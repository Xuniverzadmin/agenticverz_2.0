# Validator Logic Specification

**Status:** CONSTITUTIONAL DESIGN
**Effective:** 2026-01-04
**Reference:** PART2_CRM_WORKFLOW_CHARTER.md
**Layer:** L4 Domain Service

---

## Purpose

The **Validator** is an L4 domain service that analyzes incoming issues
and produces structured verdicts for the eligibility engine.

The Validator is:
- **Advisory** (produces recommendations, not decisions)
- **Stateless** (no side effects)
- **Deterministic** (same input → same output)
- **Versioned** (verdicts include validator version)

---

## Validator Input

```yaml
ValidatorInput:
  issue_id: UUID
  source: ENUM(crm_feedback, support_ticket, ops_alert, manual)
  raw_payload: JSONB
  received_at: TIMESTAMP
  context:
    tenant_id: UUID (optional)
    affected_capabilities_hint: TEXT[] (optional)
    priority_hint: ENUM (optional)
```

---

## Validator Output (Verdict)

```yaml
ValidatorVerdict:
  issue_type: ENUM(capability_request, bug_report, configuration_change, escalation, unknown)
  severity: ENUM(critical, high, medium, low)
  affected_capabilities: TEXT[]
  recommended_action: ENUM(create_contract, defer, reject, escalate)
  confidence_score: DECIMAL(3,2)  # 0.00 - 1.00
  reason: TEXT
  evidence: JSONB
  analyzed_at: TIMESTAMP
  validator_version: TEXT
```

---

## Issue Type Classification

### capability_request

**Definition:** Request to enable, disable, or modify a capability.

**Indicators:**
- Keywords: "enable", "disable", "turn on", "turn off", "activate"
- Mentions specific capability names
- Requests feature access

**Confidence modifiers:**
- +0.2 if capability name in registry
- +0.1 if clear action verb present
- -0.2 if vague or ambiguous

---

### bug_report

**Definition:** Report of incorrect system behavior.

**Indicators:**
- Keywords: "bug", "broken", "not working", "error", "fails"
- Includes reproduction steps
- References specific behavior

**Confidence modifiers:**
- +0.2 if includes error message
- +0.1 if reproduction steps present
- -0.3 if no specific behavior mentioned

---

### configuration_change

**Definition:** Request to modify system configuration.

**Indicators:**
- Keywords: "configure", "setting", "parameter", "threshold", "limit"
- References specific config keys
- Includes desired values

**Confidence modifiers:**
- +0.2 if config key exists
- +0.1 if valid value format
- -0.2 if invalid value format

---

### escalation

**Definition:** Issue requiring immediate human attention.

**Indicators:**
- Keywords: "urgent", "emergency", "critical", "security"
- Severity indicators
- Safety-related mentions

**Always results in:**
- `recommended_action: escalate`
- Human notification triggered

---

### unknown

**Definition:** Cannot classify with sufficient confidence.

**Triggers:**
- Confidence below 0.3
- No clear indicators
- Conflicting signals

**Always results in:**
- `recommended_action: defer`

---

## Severity Classification

### critical

**Definition:** System-wide impact, immediate action required.

**Indicators:**
- Affects multiple tenants
- Security implications
- Data integrity risk
- Production outage

**Threshold:** confidence > 0.8 for critical classification

---

### high

**Definition:** Significant impact, prompt action required.

**Indicators:**
- Single tenant severely impacted
- Feature completely broken
- Business-critical workflow blocked

**Threshold:** confidence > 0.6 for high classification

---

### medium

**Definition:** Noticeable impact, standard resolution timeline.

**Indicators:**
- Degraded experience
- Workaround available
- Non-critical workflow affected

**Default severity if not classified otherwise**

---

### low

**Definition:** Minor impact, can be deferred.

**Indicators:**
- Cosmetic issues
- Enhancement requests
- Documentation clarifications

---

## Capability Extraction

The Validator extracts affected capabilities using:

1. **Exact match:** Capability name appears in payload
2. **Fuzzy match:** Similar terms with high confidence
3. **Context inference:** Based on described behavior

```python
def extract_capabilities(payload: dict) -> list[str]:
    capabilities = []
    text = extract_text(payload)

    # Exact matches
    for cap in capability_registry:
        if cap.name.lower() in text.lower():
            capabilities.append(cap.name)

    # Fuzzy matches (threshold 0.85)
    for cap in capability_registry:
        if fuzzy_match(cap.name, text) > 0.85:
            capabilities.append(cap.name)

    return deduplicate(capabilities)
```

---

## Recommended Action Logic

```python
def determine_action(issue_type, severity, confidence) -> str:
    # Escalation always escalates
    if issue_type == "escalation":
        return "escalate"

    # Unknown always defers
    if issue_type == "unknown":
        return "defer"

    # Critical bugs escalate
    if issue_type == "bug_report" and severity == "critical":
        return "escalate"

    # Low confidence defers
    if confidence < 0.5:
        return "defer"

    # Low severity can be rejected
    if severity == "low" and confidence < 0.7:
        return "reject"

    # Default: create contract
    return "create_contract"
```

---

## Confidence Score Calculation

Base confidence is calculated from:

```python
def calculate_confidence(input: ValidatorInput) -> float:
    base = 0.5  # Start at neutral

    # Source quality
    source_weights = {
        "ops_alert": 0.2,      # Highest trust
        "support_ticket": 0.1,
        "crm_feedback": 0.05,
        "manual": 0.0
    }
    base += source_weights.get(input.source, 0)

    # Classification confidence
    base += classification_confidence  # From issue type detection

    # Capability confidence
    if all_capabilities_in_registry:
        base += 0.1
    elif some_capabilities_in_registry:
        base += 0.05
    else:
        base -= 0.1

    # Clamp to [0, 1]
    return max(0.0, min(1.0, base))
```

---

## Validator Boundaries

### What the Validator MAY Do

- Read issue payload
- Query capability registry
- Query governance signals (read-only)
- Produce verdicts

### What the Validator MUST NOT Do

- Create contracts
- Modify system state
- Make eligibility decisions
- Approve anything
- Trigger external actions

---

## Error Handling

```yaml
ValidatorError:
  error_type: ENUM(parse_error, registry_unavailable, timeout, unknown)
  message: TEXT
  fallback_verdict:
    issue_type: unknown
    severity: medium
    recommended_action: defer
    confidence_score: 0.0
    reason: "Validator error: {error_type}"
```

On error, the Validator returns a safe fallback verdict that defers to human review.

---

## Versioning

Validator versions follow semantic versioning:

- **Major:** Breaking changes to verdict schema
- **Minor:** New classification rules
- **Patch:** Bug fixes, confidence tuning

Current version included in every verdict for audit trail.

---

## Invariants

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| VAL-001 | Validator is stateless | No writes |
| VAL-002 | Verdicts include version | Required field |
| VAL-003 | Confidence in [0,1] | Clamping |
| VAL-004 | Unknown type defers | Action logic |
| VAL-005 | Escalation always escalates | Action logic |

---

## Attestation

This specification defines the Validator logic for issue analysis.
Implementation must conform to classification and confidence rules.
Changes require version increment.
