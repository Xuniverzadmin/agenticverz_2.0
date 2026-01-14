# INTENT_LEDGER.md Grammar Specification

**Version:** 1.0.0
**Status:** LOCKED
**Authority:** PIN-419

---

## Overview

This document defines the **exact Markdown grammar** for `INTENT_LEDGER.md`.
The ledger is the **only human-edited source of truth** for UI structure and capability verification.
All YAMLs are generated from this ledger.

---

## Document Structure

```
# Intent Ledger — {Console Name}

## Metadata
Authority: Human
Generated: {timestamp}
Status: {ACTIVE | FROZEN}

---

## Domains

### Domain: {DomainName}
...panels...

---

## Capabilities

### Capability: {capability_id}
...verification binding...
```

---

## Panel Entry Grammar

Each panel is a Markdown section under its domain.

### Required Format

```markdown
### Panel: {panel_id}
Domain: {Domain}
Subdomain: {SUBDOMAIN_ID}
Topic: {TOPIC_ID}
Order: {O1|O2|O3|O4|O5}
Class: {interpretation|execution|evidence}
State: {EMPTY|UNBOUND|DRAFT|BOUND|DEFERRED}

Purpose:
{Free text description of what this panel shows/does}

Capability: {capability_id | null}
```

### Field Rules

| Field | Required | Type | Values |
|-------|----------|------|--------|
| `panel_id` | YES | string | `XXX-XX-XX-O{N}` format |
| `Domain` | YES | string | Overview, Activity, Incidents, Policies, Logs |
| `Subdomain` | YES | string | SCREAMING_SNAKE_CASE |
| `Topic` | YES | string | SCREAMING_SNAKE_CASE |
| `Order` | YES | string | O1, O2, O3, O4, O5 |
| `Class` | YES | string | interpretation, execution, evidence |
| `State` | YES | string | EMPTY, UNBOUND, DRAFT, BOUND, DEFERRED |
| `Purpose` | YES | text | Multi-line description |
| `Capability` | YES | string | capability_id or `null` |

### Example

```markdown
### Panel: INC-AI-SUM-O1
Domain: Incidents
Subdomain: ACTIVE_INCIDENTS
Topic: SUMMARY
Order: O1
Class: interpretation
State: BOUND

Purpose:
Summary of active incidents with severity breakdown.
Shows attention reasons and total counts by lifecycle state.

Capability: summary.incidents
```

---

## Capability Entry Grammar

Each capability binding links a capability to its verification.

### Required Format

```markdown
### Capability: {capability_id}
Panel: {panel_id}
Status: {DECLARED|OBSERVED|TRUSTED}

Verification:
Scenario: {SDSR scenario_id | NONE}
Acceptance:
- {criterion 1}
- {criterion 2}

Observed: {YYYY-MM-DD | null}
```

### Field Rules

| Field | Required | Type | Values |
|-------|----------|------|--------|
| `capability_id` | YES | string | dot-notation or SCREAMING_SNAKE |
| `Panel` | YES | string | panel_id |
| `Status` | YES | string | DECLARED, OBSERVED, TRUSTED |
| `Scenario` | YES | string | SDSR-* or NONE |
| `Acceptance` | YES | list | Markdown bullet list |
| `Observed` | CONDITIONAL | date | Required if Status=OBSERVED |

### Example (OBSERVED)

```markdown
### Capability: summary.incidents
Panel: INC-AI-SUM-O1
Status: OBSERVED

Verification:
Scenario: SDSR-HIL-INC-SUM-001
Acceptance:
- Summary reflects actual incident counts
- Lifecycle states sum to total
- Attention count matches active incidents

Observed: 2026-01-14
```

### Example (DECLARED)

```markdown
### Capability: summary.activity
Panel: ACT-EX-SUM-O1
Status: DECLARED

Verification:
Scenario: NONE
Acceptance:
- Activity summary shows run counts
- Time window is configurable

Observed: null
```

---

## Domain Section Grammar

Domains group panels for navigation.

### Required Format

```markdown
## Domains

### Domain: {DomainName}
Question: {What question does this domain answer?}
Primary: {Primary object type}
Secondary: {Comma-separated secondary objects}

#### Subdomain: {SUBDOMAIN_ID}

##### Topic: {TOPIC_ID}
- Panel: {panel_id} → {brief description}
- Panel: {panel_id} → {brief description}
```

### Example

```markdown
### Domain: Incidents
Question: What went wrong?
Primary: Incident
Secondary: Violation, Failure, Alert

#### Subdomain: ACTIVE_INCIDENTS

##### Topic: SUMMARY
- Panel: INC-AI-SUM-O1 → Interpretation panel for incident summary

##### Topic: OPEN_INCIDENTS
- Panel: INC-AI-OI-O1 → List of open incidents
- Panel: INC-AI-OI-O2 → Open incident details
```

---

## Parsing Rules

1. **Section Headers** determine context:
   - `## Domains` → domain section
   - `### Domain:` → new domain
   - `### Panel:` → panel entry
   - `### Capability:` → capability binding

2. **Field Lines** are `Key: Value` format (single line)

3. **Multi-line Fields** follow a colon on its own line:
   ```
   Purpose:
   This is a multi-line
   description that continues
   until the next field or section.
   ```

4. **List Fields** use Markdown bullets:
   ```
   Acceptance:
   - First criterion
   - Second criterion
   ```

5. **Null Values** are explicit: `Capability: null`, `Observed: null`

---

## Generator Contract

The `sync_from_intent_ledger.py` script will:

1. Parse this grammar exactly
2. Generate `ui_plan.yaml` from Domain/Panel entries
3. Generate capability registry YAMLs from Capability entries
4. Generate SDSR scenario stubs from Capability.Scenario fields

**Non-goals:**
- No inference
- No defaults (all fields explicit)
- No status promotion (that's observation's job)

---

## Validation Rules

The `coherency_gate.py` script will:

1. **CG-001:** Every Panel entry must have valid Domain/Subdomain/Topic
2. **CG-002:** Every Capability entry must reference existing Panel
3. **CG-003:** If Capability.Scenario != NONE, scenario file must exist
4. **CG-004:** If Capability.Status = OBSERVED, Observed date required
5. **CG-005:** Panel.State must match Capability.Status per binding rules

### Binding Rules

| Capability.Status | Panel.State |
|-------------------|-------------|
| (no capability) | EMPTY or UNBOUND |
| DECLARED | DRAFT |
| OBSERVED | BOUND |
| TRUSTED | BOUND |

---

## Migration Notes

When bootstrapping from existing artifacts:
- Panel entries extracted from `ui_plan.yaml`
- Capability entries extracted from `capability_registry/*.yaml`
- Status/Observed from capability metadata
- Scenario from capability `observed_by` field
