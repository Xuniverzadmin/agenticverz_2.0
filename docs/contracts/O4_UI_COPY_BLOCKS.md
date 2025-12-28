# O4 UI Copy Blocks (Pre-Approved, Frozen)

**Status:** FROZEN
**Date:** 2025-12-28
**Reference:** O4_UI_ACCEPTANCE_CRITERIA.md v2

---

## Purpose

These strings are **certified safe**.
Use exactly as written. Anything else requires semantic review.

---

## A. GLOBAL COPY

### Page Subtitle

```
Informational only. Advisory predictions do not affect system behavior.
```

### Empty State

```
No advisory predictions available.
```

### Confidence Tooltip

```
Confidence reflects model uncertainty.
It is not a priority, severity, or action signal.
```

---

## B. PREDICTION TYPE COPY

### Incident Risk

**Card Header:**
```
Incident Risk (Advisory)
```

**Card Body:**
```
Observed patterns may indicate elevated incident likelihood.
```

### Spend Spike

**Card Header:**
```
Spend Spike (Advisory)
```

**Card Body:**
```
Observed spend patterns may indicate a temporary spike.
```

### Policy Drift

**Card Header:**
```
Policy Drift (Advisory)
```

**Card Body:**
```
Observed similarity to patterns seen in prior policy evaluations.
```

---

## C. FOPS CONTAINMENT COPY (REQUIRED)

**Banner Header:**
```
Advisory Signals Only
```

**Banner Body (3 lines, all required):**
```
These are advisory prediction signals.
They do not trigger, justify, or recommend actions.
Use for situational awareness only.
```

---

## D. FILTER LABELS

### Customer Console

```
All
Incident Risk
Spend Spike
Policy Drift
```

### FOPS Console

```
All Tenants
All
Incident
Spend
Policy
```

---

## E. CARD METADATA

### Confidence Display

```
Confidence: {N}%
```

Where `{N}` is the integer percentage (0-100).
Example: `Confidence: 72%`

### Expiry Display

```
Expires in {N} min
```

Where `{N}` is minutes remaining.
Example: `Expires in 24 min`

If expired or <1 min:
```
Expiring soon
```

---

## F. TENANT CONTEXT (FOPS Only)

**Label:**
```
Tenant: {tenant_name}
```

**Not:**
- "Target: {tenant_name}" (implies action)
- "Alert for: {tenant_name}" (implies urgency)
- "{tenant_name}" alone (lacks context framing)

---

## G. FORBIDDEN COPY PATTERNS

| Forbidden | Reason | Alternative |
|-----------|--------|-------------|
| "Warning" | Implies danger | "Advisory" |
| "Alert" | Implies action | "Prediction" |
| "Risk level" | Implies severity | "Confidence" |
| "Action required" | Implies enforcement | Remove entirely |
| "Recommended" | Implies guidance | Remove entirely |
| "Violation" | Implies authority | "Observed similarity" |
| "All clear" | Implies safety | "No advisory predictions available" |
| "No risk" | Implies validation | "No advisory predictions available" |
| "System healthy" | Implies authority | Remove entirely |
| "Urgent" | Implies priority | Remove entirely |
| "Critical" | Implies severity | Remove entirely |
| "High/Medium/Low" | Implies ranking | Remove entirely |

---

## H. ARIA / ACCESSIBILITY LABELS

### Page

```
aria-label="Advisory predictions panel"
```

### Prediction Card

```
aria-label="Advisory prediction: {type}"
```

### Empty State

```
aria-label="No predictions available"
```

### FOPS Banner

```
role="status"
aria-label="Advisory signals disclaimer"
```

---

## I. ERROR STATES

### API Failure

```
Unable to load advisory predictions.
```

**Not:**
- "Error loading predictions" (technical)
- "Something went wrong" (vague)
- "Try again" (implies action)

### Loading State

```
Loading advisory predictions...
```

---

## J. COPY VALIDATION CHECKLIST

Before using any new copy:

- [ ] Contains "advisory" or "informational"
- [ ] Does NOT contain forbidden words
- [ ] Does NOT imply action, urgency, or severity
- [ ] Matches semantic mode (customer vs FOPS)
- [ ] Human review complete

---

## Related Documents

| Document | Purpose |
|----------|---------|
| O4_UI_ACCEPTANCE_CRITERIA.md | Acceptance rules |
| O4_UI_WIREFRAMES.md | Layout structure |
| O4_ADVISORY_UI_CONTRACT.md | Contract |
