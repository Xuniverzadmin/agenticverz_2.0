# O4 — ADVISORY UI CONTRACT (AUTHORITATIVE)

**Status:** DRAFT v2
**Date:** 2025-12-28
**Prerequisite:** C2 Certification Statement (CERTIFIED)
**Reference:** PIN-223, C2_CERTIFICATION_STATEMENT.md

---

## Purpose

Expose C2 predictions **only to humans**, in a way that:

* does not resemble truth
* does not resemble enforcement
* does not invite action

The rule for O4 is simple and brutal:

> **UI must make it harder to misinterpret predictions than to ignore them.**

---

## Console Semantics (Corrected)

### `console.agenticverz.com`

| Attribute | Value |
|-----------|-------|
| Audience | aos-customer |
| Meaning | Actual customer reality |
| Role | Ground truth *experience* |
| Risk profile | Medium (misinterpretation by customers) |

### `preflight-console.agenticverz`

| Attribute | Value |
|-----------|-------|
| Audience | aos-internal (founder-developer) |
| Meaning | TestFlight view of customer experience |
| Role | Preview / QA / validation |
| Risk profile | Low (internal, but mirrors customer semantics) |

### `fops.agenticverz.com`

| Attribute | Value |
|-----------|-------|
| Audience | aos-founder |
| Meaning | God's view / system-level observability |
| Role | Oversight, diagnosis, intervention |
| Risk profile | **High** (anything shown here feels authoritative) |

### `preflight-fops.agenticverz`

| Attribute | Value |
|-----------|-------|
| Audience | aos-internal (founder-developer) |
| Meaning | Staging/promoter layer for FOPS |
| Role | Validate founder-level visibility before prod |
| Risk profile | Same as FOPS (authority gravity) |

---

## O4 Semantic Modes

O4 exists in **two semantic modes** based on console context:

### Mode A — Customer-Semantic O4

**Applies to:**
* `console.agenticverz.com`
* `preflight-console.agenticverz`

**Characteristics:**
* Advisory
* Passive
* No sense of responsibility
* "You may look, you may ignore"

This is the **pure C2 meaning**.

### Mode B — Oversight-Semantic O4

**Applies to:**
* `fops.agenticverz.com`
* `preflight-fops.agenticverz`

**Characteristics:**
* Still **non-authoritative**
* But **explicitly contextualized as observational**
* Framed as *system introspection*, not guidance

**REQUIRED framing text at page top:**

> "These are advisory prediction signals.
> They do not trigger, justify, or recommend actions.
> Use for situational awareness only."

This is **semantic containment**, not UX fluff.

---

## O4 Linkage Table (Authoritative v2 — FROZEN)

| Subdomain | Allowed O4 | Semantic Mode | Page Route | Notes |
|-----------|------------|---------------|------------|-------|
| `console.agenticverz.com` | ✅ YES | Customer-Semantic | `/insights/predictions` | Primary O4 |
| `preflight-console.agenticverz` | ✅ YES | Customer-Semantic | `/insights/predictions` | TestFlight mirror |
| `fops.agenticverz.com` | ✅ YES | Oversight-Semantic | `/oversight/predictions` | **Different framing** |
| `preflight-fops.agenticverz` | ✅ YES | Oversight-Semantic | `/oversight/predictions` | Promoter/staging |

### Forbidden Everywhere

* Inline with incidents
* Inline with enforcement
* Inline with controls
* Pop-ups, banners, alerts

---

## API Usage Rules

All O4 variants call the **same API**:

```http
GET /api/v1/c2/predictions
```

### Customer / Preflight-Console

* Filtered to tenant scope
* No system-wide aggregation

### FOPS / Preflight-FOPS

* May aggregate across tenants
* Must add **explicit disclaimer** (see Oversight-Semantic O4 above)

**No write endpoints from UI anywhere.**

---

## 1. Placement Rules (Non-Negotiable)

### Allowed

* Dedicated **Insights / Advisory** area only (customer consoles)
* Dedicated **Oversight** area only (FOPS consoles)
* Clearly separated from:
  * incidents
  * enforcement
  * controls
  * operations

### Forbidden

* Inline with O1 (truth)
* Inline with O2 (metrics)
* Inline with O3 (ops/actions)
* Pop-ups, banners, alerts

---

## 2. Structural Layout

### Customer-Semantic Layout (`/insights/predictions`)

```
Insights (O4)
────────────
[ Advisory Predictions ]

• Incident Risk (advisory)
• Spend Spike (advisory)
• Policy Drift (advisory)
```

### Oversight-Semantic Layout (`/oversight/predictions`)

```
Oversight (O4)
────────────
┌─────────────────────────────────────────────────────────────┐
│ These are advisory prediction signals.                      │
│ They do not trigger, justify, or recommend actions.         │
│ Use for situational awareness only.                         │
└─────────────────────────────────────────────────────────────┘

[ System Advisory Predictions ]

• Incident Risk (advisory) — tenant: xxx
• Spend Spike (advisory) — tenant: yyy
• Policy Drift (advisory) — tenant: zzz
```

No sorting by severity by default.
No highlighting that implies urgency.

---

## 3. Mandatory Visual Semantics

Every prediction must include **redundant advisory cues**:

| Element | Value |
|---------|-------|
| Label | **ADVISORY** |
| Subtitle | "Informational only" |
| Tooltip | "Does not affect system behavior" |

Redundancy is intentional.

---

## 4. Language Contract (Strict)

### Allowed Language

| Word/Phrase | Context |
|-------------|---------|
| "Advisory" | Label, badge |
| "Observed pattern" | Description |
| "May indicate" | Explanation |
| "Similarity noted" | Comparison |
| "Informational" | Subtitle |
| "Situational awareness" | FOPS framing |

### Forbidden Language

| Word/Phrase | Reason |
|-------------|--------|
| "Violation" | Implies authority |
| "Will happen" | Implies certainty |
| "Risk level" | Implies severity ranking |
| "Action required" | Implies enforcement |
| "Recommended" | Implies guidance |
| "Urgent" | Implies priority |
| "Warning" | Implies danger |
| "Alert" | Implies action |

Any forbidden word = UI contract violation.

---

## 5. Interaction Rules

### Allowed

| Action | Behavior |
|--------|----------|
| View | Read-only display |
| Filter | Client-side filtering |
| Dismiss | Client-side only, no persistence |

### Forbidden

| Action | Reason |
|--------|--------|
| Acknowledge | Implies tracking |
| Resolve | Implies workflow |
| Escalate | Implies action path |
| Act | Implies enforcement |
| Link to controls | Implies authority |

Predictions must feel **passive**.

---

## 6. Ranking & Ordering

| Ordering | Status |
|----------|--------|
| Chronological | Default |
| By type | Optional |
| By confidence alone | **FORBIDDEN** |

Confidence is informational, not priority.

---

## 7. Failure & Absence States

### When No Predictions Exist

Display:
> "No advisory predictions available."

### Forbidden Alternatives

| Text | Reason |
|------|--------|
| "All clear" | Implies safety |
| "No risk detected" | Implies authority |
| "System healthy" | Implies validation |

**Absence ≠ safety.**

---

## 8. Visual Styling Rules

### Colors

| Use | Color Guidance |
|-----|----------------|
| Advisory badge | Neutral (gray, light blue) |
| Background | Same as rest of UI |
| Text | Standard, no bold for emphasis |

### Forbidden Colors/Styles

| Style | Reason |
|-------|--------|
| Red | Implies danger |
| Yellow | Implies warning |
| Bold emphasis | Implies importance |
| Pulsing/animation | Implies urgency |

---

## 9. Data Display Rules

### Shown

| Field | Display | Customer | FOPS |
|-------|---------|----------|------|
| Prediction type | Text label | ✅ | ✅ |
| Subject | Identifier only | ✅ | ✅ |
| Confidence | Number (0-1), no interpretation | ✅ | ✅ |
| Expires at | Timestamp | ✅ | ✅ |
| Observed pattern | Raw text | ✅ | ✅ |
| Tenant ID | Identifier | ❌ | ✅ |

### Hidden (Never Expose)

| Field | Reason |
|-------|--------|
| Internal ID | Implementation detail |
| Contributing factors | Not yet defined |

---

## 10. Re-Certification Trigger

Any of the following **requires C2 re-certification**:

1. Predictions shown outside O4 routes
2. Actionable UI elements added
3. Language implying authority
4. Redis used for UI decisions
5. Predictions influence navigation
6. Predictions trigger notifications
7. Semantic containment removed from FOPS

---

## 11. Implementation Checklist

Before O4 UI is deployed:

### Customer-Semantic O4

- [ ] Route is `/insights/predictions`
- [ ] Placement verified (dedicated area)
- [ ] Language audit complete (no forbidden words)
- [ ] Interactions verified (read-only)
- [ ] Ordering verified (no confidence ranking)
- [ ] Absence states verified (no false safety)
- [ ] Visual styling verified (neutral)
- [ ] Human semantic verification complete

### Oversight-Semantic O4 (FOPS)

- [ ] Route is `/oversight/predictions`
- [ ] Semantic containment banner present
- [ ] Tenant context visible
- [ ] Language audit complete (no forbidden words)
- [ ] Interactions verified (read-only)
- [ ] Ordering verified (no confidence ranking)
- [ ] Absence states verified (no false safety)
- [ ] Visual styling verified (neutral)
- [ ] Human semantic verification complete

---

## 12. Acceptance Criteria

### Shared (All Consoles)

| ID | Criterion | Requirement |
|----|-----------|-------------|
| A1 | Advisory Label | All predictions labeled "ADVISORY" |
| A2 | Language Compliance | Zero forbidden language detected |
| A3 | Read-Only | No action buttons present |
| A4 | Ordering | Chronological ordering default |
| A5 | Absence States | "No advisory predictions available" |
| A6 | Separation | Visually separated from O1/O2/O3 |
| A7 | Human Verification | Manual semantic check complete |

### Customer-Semantic O4 Only

| ID | Criterion | Requirement |
|----|-----------|-------------|
| C1 | Route | `/insights/predictions` |
| C2 | Scope | Tenant-filtered only |
| C3 | No Tenant ID | Tenant ID hidden |

### Oversight-Semantic O4 Only (FOPS)

| ID | Criterion | Requirement |
|----|-----------|-------------|
| F1 | Route | `/oversight/predictions` |
| F2 | Containment Banner | Disclaimer visible at page top |
| F3 | Tenant Context | Tenant ID visible |
| F4 | Aggregation Safe | No interpretation of aggregated data |

---

## 13. Related Documents

| Document | Purpose |
|----------|---------|
| C2_CERTIFICATION_STATEMENT.md | C2 certification |
| PIN-221 | C2 Semantic Contract |
| PIN-222 | C2 Implementation Plan |
| PIN-223 | C2-T3 Completion |

---

**Status:** DRAFT v2 — Linkage table frozen, pending UI implementation
**Next:** Acceptance criteria document, then ASCII wireframes
