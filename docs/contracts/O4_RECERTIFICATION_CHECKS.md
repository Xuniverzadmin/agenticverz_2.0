# O4 Re-Certification Checks (Governance)

**Status:** ACTIVE
**Date:** 2025-12-28
**Purpose:** Convert O4 promises into mechanical enforcement
**Reference:** O4_UI_ACCEPTANCE_CRITERIA.md v2

---

## Principle

> "We promise to behave" → **"The system refuses to drift."**

These checks ensure O4 remains compliant with C2 certification.
Failure of any check **blocks deployment**.

---

## Check Categories

| Category | Type | Enforcement |
|----------|------|-------------|
| RC-1 | Language | CI (grep) |
| RC-2 | Route | CI (grep) |
| RC-3 | Import Isolation | CI (grep) |
| RC-4 | API Method | CI (grep) |
| RC-5 | Containment Banner | CI (AST) + Manual |
| RC-6 | Color Tokens | CI (grep) |
| RC-7 | Ordering | Manual |
| RC-8 | Human Semantic | Manual |

---

## RC-1: Forbidden Language Check

**Type:** CI (automated)
**Scope:** All O4 UI files

### Forbidden Patterns

```bash
# Must NOT appear in O4 components
grep -riE "violation|will happen|risk level|action required|recommended|urgent|warning|alert|critical|all clear|no risk|system healthy" \
  frontend/src/insights/ \
  frontend/src/oversight/
```

### Pass Condition

Zero matches.

### Fail Action

```
O4 BLOCKED: Forbidden language detected in {file}:{line}
  Pattern: {match}
  Fix: Replace with approved copy from O4_UI_COPY_BLOCKS.md
```

---

## RC-2: Route Compliance Check

**Type:** CI (automated)
**Scope:** Router configuration

### Required Routes

```javascript
// Customer consoles MUST use:
/insights/predictions

// FOPS consoles MUST use:
/oversight/predictions
```

### Forbidden Routes

```bash
# Predictions MUST NOT appear on these paths
grep -riE "predictions" frontend/src/routes/ | \
  grep -vE "(insights|oversight)" | \
  grep -vE "\.test\.|\.spec\."
```

### Pass Condition

Predictions only on `/insights/predictions` or `/oversight/predictions`.

### Fail Action

```
O4 BLOCKED: Predictions exposed on forbidden route
  Found: {route}
  Allowed: /insights/predictions, /oversight/predictions
```

---

## RC-3: Import Isolation Check

**Type:** CI (automated)
**Scope:** All non-O4 UI files

### Forbidden Imports

```bash
# O4 components MUST NOT be imported into:
# - Incidents pages
# - Enforcement pages
# - Ops/Actions pages
# - Dashboard

grep -riE "from.*insights|from.*oversight|from.*predictions|PredictionCard|AdvisoryPanel" \
  frontend/src/incidents/ \
  frontend/src/enforcement/ \
  frontend/src/ops/ \
  frontend/src/dashboard/
```

### Pass Condition

Zero matches in forbidden directories.

### Fail Action

```
O4 BLOCKED: Prediction component imported into forbidden area
  Import found in: {file}
  Fix: O4 components must be isolated to /insights or /oversight
```

---

## RC-4: API Method Check

**Type:** CI (automated)
**Scope:** O4 UI files

### Allowed API Calls

```javascript
// ONLY these patterns allowed:
GET /api/v1/c2/predictions
```

### Forbidden API Calls

```bash
# O4 MUST NOT make write calls
grep -riE "\.post\(|\.put\(|\.delete\(|\.patch\(" \
  frontend/src/insights/ \
  frontend/src/oversight/ | \
  grep -i prediction
```

### Pass Condition

Zero POST/PUT/DELETE/PATCH calls to prediction endpoints.

### Fail Action

```
O4 BLOCKED: Write operation detected in O4 UI
  Found: {method} in {file}
  Fix: O4 is read-only. Remove write operation.
```

---

## RC-5: Containment Banner Check (FOPS)

**Type:** CI (AST) + Manual
**Scope:** FOPS oversight pages

### Required Elements

```javascript
// FOPS oversight/predictions MUST contain:
// 1. Banner component at top level
// 2. Exact disclaimer text
// 3. Non-dismissable (no close button)
// 4. Fixed position (no scroll-away)
```

### CI Check (grep)

```bash
# Must find containment banner in FOPS
grep -riE "Advisory Signals Only|do not trigger, justify, or recommend|situational awareness only" \
  frontend/src/oversight/

# Must NOT find dismiss/close on banner
grep -riE "onDismiss|onClose|dismissable|closeable" \
  frontend/src/oversight/ | \
  grep -i banner
```

### Manual Check

| Criterion | Verification |
|-----------|--------------|
| Banner visible | Screenshot |
| Banner non-dismissable | Click test |
| Banner non-scrollable | Scroll test |
| Exact text matches | Visual comparison |

### Pass Condition

- CI: Banner text found, no dismiss handlers
- Manual: All criteria verified

### Fail Action

```
O4 BLOCKED: FOPS containment banner non-compliant
  Issue: {description}
  Fix: Banner must be permanent, fixed, non-dismissable
```

---

## RC-6: Color Token Check

**Type:** CI (automated)
**Scope:** O4 UI styles

### Forbidden Color Patterns

```bash
# O4 MUST NOT use severity colors
grep -riE "red|#ff|#f00|danger|error|warning|amber|yellow|#ff9|critical|severity" \
  frontend/src/insights/ \
  frontend/src/oversight/ | \
  grep -vE "\.test\.|\.spec\.|// forbidden"
```

### Allowed Colors

```css
/* Neutral only */
gray, grey, #6b7280, #9ca3af
blue (light), #3b82f6, #60a5fa
white, #ffffff
black, #000000
```

### Pass Condition

Zero severity color matches.

### Fail Action

```
O4 BLOCKED: Severity color detected in O4 UI
  Found: {color} in {file}
  Fix: Use neutral colors only (gray, light blue)
```

---

## RC-7: Ordering Check (Manual)

**Type:** Manual
**Scope:** Live UI behavior

### Required Ordering

| Console | Default Order |
|---------|---------------|
| Customer | Chronological (newest first) |
| FOPS | Chronological (newest first) |

### Forbidden Ordering

- By confidence (as default)
- By severity
- By "priority"

### Verification Procedure

1. Load O4 page
2. Verify default sort is by time
3. Verify no "sort by confidence" as default
4. Verify no severity-based grouping

### Pass Condition

Default is chronological. Confidence sort is optional, not default.

### Fail Action

```
O4 BLOCKED: Confidence-based ordering as default
  Fix: Change default to chronological
```

---

## RC-8: Human Semantic Verification (Manual)

**Type:** Manual sign-off
**Scope:** Complete O4 implementation

### Checklist

| ID | Check | Verified |
|----|-------|----------|
| HS-1 | Page feels passive, not urgent | [ ] |
| HS-2 | No visual element implies action | [ ] |
| HS-3 | "Advisory" appears redundantly | [ ] |
| HS-4 | Empty state is neutral | [ ] |
| HS-5 | FOPS banner dominates page top | [ ] |
| HS-6 | No confusion with incidents | [ ] |
| HS-7 | Tenant context is "context", not "target" | [ ] |
| HS-8 | Overall impression: informational | [ ] |

### Sign-Off Requirement

Requires **human sign-off** from:
- Engineering lead
- Product owner (if applicable)

### Pass Condition

All HS-* items checked and signed.

### Fail Action

```
O4 BLOCKED: Human semantic verification incomplete
  Missing: {unchecked items}
  Fix: Complete verification and obtain sign-off
```

---

## CI Pipeline Integration

### Workflow: `.github/workflows/o4-recertification.yml`

```yaml
name: O4 Re-Certification

on:
  pull_request:
    paths:
      - 'frontend/src/insights/**'
      - 'frontend/src/oversight/**'

jobs:
  recertification:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: RC-1 Language Check
        run: ./scripts/ci/o4_checks/rc1_language.sh

      - name: RC-2 Route Check
        run: ./scripts/ci/o4_checks/rc2_routes.sh

      - name: RC-3 Import Isolation
        run: ./scripts/ci/o4_checks/rc3_imports.sh

      - name: RC-4 API Method Check
        run: ./scripts/ci/o4_checks/rc4_api.sh

      - name: RC-5 Containment Banner (CI portion)
        run: ./scripts/ci/o4_checks/rc5_banner.sh

      - name: RC-6 Color Token Check
        run: ./scripts/ci/o4_checks/rc6_colors.sh
```

---

## Re-Certification vs Normal Changes

### Changes That REQUIRE Re-Certification

| Change | Trigger |
|--------|---------|
| New route for predictions | RC-2 |
| New language in cards | RC-1 |
| New color in O4 | RC-6 |
| New component import | RC-3 |
| API call changes | RC-4 |
| Banner modification | RC-5 |
| Ordering logic changes | RC-7 |

### Changes That Do NOT Require Re-Certification

| Change | Reason |
|--------|--------|
| Bug fixes (no semantic change) | No drift risk |
| Performance improvements | No user-facing change |
| Refactoring (same behavior) | No semantic change |
| Test additions | Safety improvement |

### When in Doubt

If uncertain whether a change requires re-certification:
**Assume YES and run all checks.**

---

## Enforcement

### Pre-Merge Gate

All RC-* checks must pass before merge to main.
Manual checks (RC-7, RC-8) must be documented in PR.

### Post-Deploy Gate

After O4 deployment, re-run manual checks on live environment.
Document results in deployment ticket.

### Violation Response

If O4 violation detected in production:

1. **Immediate:** Revert or feature-flag O4
2. **Within 24h:** Root cause analysis
3. **Before re-enable:** All RC-* checks pass

---

## Related Documents

| Document | Purpose |
|----------|---------|
| O4_UI_ACCEPTANCE_CRITERIA.md | What O4 must be |
| O4_UI_WIREFRAMES.md | How O4 should look |
| O4_UI_COPY_BLOCKS.md | What O4 should say |
| C2_CERTIFICATION_STATEMENT.md | Why this matters |
