# O4 UI ACCEPTANCE CRITERIA (AUTHORITATIVE, v2)

**Status:** FROZEN
**Date:** 2025-12-28
**Prerequisite:** C2 Certification Statement (CERTIFIED)
**Reference:** O4_ADVISORY_UI_CONTRACT.md v2

---

## Binding Contract

These criteria are **binding**.
If any fail, O4 is **non-compliant with C2 certification**.

---

## A. GLOBAL O4 RULES (Apply Everywhere)

### G-1. Read-Only

* No POST / PUT / DELETE from UI
* No "acknowledge", "resolve", "act", "export"

### G-2. Advisory Redundancy

* "Advisory" must appear:
  * In page header
  * In each prediction card
  * In tooltip or helper text

### G-3. Absence ≠ Safety

* Empty state must say:
  > "No advisory predictions available."
* Must NOT say "All clear", "No risk", "Healthy"

### G-4. No Urgency Encoding

* No red/amber colors
* No severity badges
* No ranking by confidence by default

### G-5. API Scope

* UI may only call:
  ```
  GET /api/v1/c2/predictions
  ```
* No joins with incidents, enforcement, replay

---

## B. CUSTOMER-SEMANTIC O4 (CS-*)

**Applies to:**
* `console.agenticverz.com`
* `preflight-console.agenticverz`

### CS-1. Route

```
/insights/predictions
```

### CS-2. Tenant Context

* Tenant ID **implicit**
* Tenant name **hidden**
* No cross-tenant visibility

### CS-3. Language Constraints

**Allowed:**
* "Advisory"
* "Observed pattern"
* "May indicate"

**Forbidden:**
* "Violation"
* "Risk level"
* "Action required"

### CS-4. Interaction

**Allowed:**
* Filter by type
* Sort by time

**Forbidden:**
* Dismiss (server-side)
* Escalate
* Comment
* Share

### CS-5. Card Content

Each card shows:
* Prediction type
* Short advisory sentence
* Confidence (as percentage, small text)
* Expiry time

---

## C. OVERSIGHT-SEMANTIC O4 (FS-*)

**Applies to:**
* `fops.agenticverz.com`
* `preflight-fops.agenticverz`

### FS-1. Route

```
/oversight/predictions
```

### FS-2. Mandatory Containment Banner (TOP OF PAGE)

> **These are advisory prediction signals.**
> **They do not trigger, justify, or recommend actions.**
> **Use for situational awareness only.**

This banner:
* Cannot be dismissed
* Cannot be collapsed
* Appears on every load

### FS-3. Tenant Visibility

* Tenant ID and name visible
* Clearly labeled as "Context", not "Target"

### FS-4. No Action Gravity

**Forbidden:**
* Links to FOPS actions
* Deep links to enforcement
* Inline ops shortcuts

### FS-5. Framing Language

Every section must reinforce:
> "Observational view of advisory signals"

---

## D. ACCEPTANCE GATE (BINARY)

O4 is **ACCEPTED** only if:

| Gate | Requirement |
|------|-------------|
| G-* | All global rules pass |
| CS-* | All customer-semantic rules pass on customer consoles |
| FS-* | All oversight-semantic rules pass on FOPS consoles |
| API | No new API endpoints introduced |
| CI | C2 CI remains green |

Otherwise: **BLOCKED**

---

## E. VERIFICATION PROCEDURE

```
1. Deploy O4 UI to preflight environment
2. Run through all G-*, CS-*, FS-* criteria
3. Document any failures
4. Fix and re-verify
5. Human semantic verification (manual review)
6. Promote to production only after acceptance gate passes
```

---

## F. RE-CERTIFICATION TRIGGERS

Any of the following **invalidates O4 acceptance**:

1. Route changes
2. Containment banner removed (FOPS)
3. Action buttons added
4. Language contract violated
5. Predictions shown inline with truth/enforcement
6. Redis dependency introduced
7. Aggregation or interpretation added (FOPS)

---

## Related Documents

| Document | Purpose |
|----------|---------|
| O4_ADVISORY_UI_CONTRACT.md | Contract and rules |
| O4_UI_WIREFRAMES.md | ASCII wireframes |
| O4_UI_COPY_BLOCKS.md | Pre-approved language |
| C2_CERTIFICATION_STATEMENT.md | C2 certification |
