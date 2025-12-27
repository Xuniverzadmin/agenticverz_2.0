# PIN-186: Page Order & Drill-Down Invariants

**Status:** LAW (Non-Negotiable)
**Category:** UI / Architecture / Governance
**Created:** 2025-12-26
**Milestone:** Runtime v1 Feature Freeze
**Enforcement:** All UI PRs must comply

---

## Summary

This PIN codifies the page order model for AOS console. It is **normative, not descriptive**. Any UI that violates these invariants is rejected.

---

## Order Definitions

| Order | Name | Cognitive Role | Truth Exposure | UI Pattern |
|-------|------|----------------|----------------|------------|
| **O1** | Dashboard | Situational awareness | Aggregated truth | Cards with metrics |
| **O2** | List | Pattern recognition | Grouped truth | Filterable table |
| **O3** | Detail | Accountability | Single-entity truth | Sectioned detail page |
| **O4** | Related | Causality | Related evidence | Log/list of related entities |
| **O5** | Action | Commitment | Final action | Popup/modal ONLY |

---

## Invariants (Hard Rules)

### INV-1: Maximum Order = 5

**No page may exceed O5.**

Going past O5 means:
- You're browsing internals, not making decisions
- Violating "don't hide failures" by drowning users
- Audit trail becomes unreadable

### INV-2: One O4 Per Entity

**No entity may have more than ONE O4 layer.**

Further drilling must **cross to another entity's O3**, not nest deeper.

```
ALLOWED:
Incidents (O3) → Occurrences (O4) → Click run_id → Runs (O3)

FORBIDDEN:
Incidents (O3) → Occurrences (O4) → Stack Trace (O4) → Token Detail (O4)
```

Why this matters:
- Prevents infinite depth
- Preserves entity accountability
- Keeps breadcrumbs meaningful
- Avoids "log viewer hell"

### INV-3: Cross-Entity Drill = O3

**When crossing from one entity to another, always land on O3.**

Never land on O2 (list) or O4 (related). The user wants the specific entity, not to re-filter.

```
ALLOWED:
Decision (O3) → Click run_id → Run (O3)

FORBIDDEN:
Decision (O3) → Click run_id → Runs List (O2)
```

### INV-4: O5 = Popup/Modal Only

**O5 is reserved exclusively for final actions.**

O5 must:
- Be a popup or modal
- Require explicit confirmation
- Log the action
- Not contain further navigation

Examples of valid O5:
- Freeze confirmation
- Delete confirmation
- Download action
- Policy create form

### INV-5: Breadcrumb Continuity

**Breadcrumbs must reflect the drill path, including cross-entity jumps.**

Format: `Entity > ID > Related > Entity > ID`

Example:
```
Incidents > INC-123 > Occurrences > Runs > RUN-456 > Steps
```

When crossing entities, the breadcrumb continues (not resets).

### INV-6: Value Truncation

**Any data value displayed at O3 or O4 must be truncated by default.**

- Text: First 200 chars + "..."
- JSON: First 5 keys or first 500 chars
- Full value: Only via explicit "View Full" action (O5 popup)

This prevents accidental data leakage.

---

## Entity Order Map

| Entity | O1 | O2 | O3 | O4 | O5 |
|--------|----|----|----|----|----|
| Runs | Dashboard | List | Run Detail | Steps OR Decisions | Step Detail (popup) |
| Incidents | Dashboard | List (grouped) | Incident Detail | Occurrences OR Recovery | Occurrence (popup) |
| Decisions | Timeline | Filtered List | Decision Detail | Related Decisions | - |
| Memory/Pins | Dashboard | Pins List | Pin Detail | Access Log | Actions (popup) |
| Agents | Dashboard | Agents List | Agent Detail | Runs OR Skills | - |
| Skills | Dashboard | Skills List | Skill Detail | Invocations | - |
| Costs | Dashboard | Breakdown | Cost Detail | - | - |
| Policies | Dashboard | Policies List | Policy Detail | Triggers | Edit (popup) |
| Keys | Dashboard | Keys List | Key Detail | Usage Log | Rotate/Revoke (popup) |
| Tenants | Dashboard | Tenants List | Tenant Detail | → Runs O2 / Incidents O2 | - |
| KillSwitch | Status | Frozen List | Frozen Detail | Blocked Log | Freeze/Unfreeze (popup) |
| Alerts | Dashboard | Alerts List | Alert Detail | → Related Entity O3 | Acknowledge (popup) |
| Traces | Dashboard | Traces List | Trace Detail | Step Detail | Download/Compare (popup) |

---

## Cross-Link Map

Primary anchor: **Runs**

All roads lead to Runs:
- Incidents → Runs (via run_id)
- Decisions → Runs (via run_id)
- Costs → Runs (via run_id)
- Traces → Runs (via run_id)
- Agents → Runs (via agent runs)
- Skills → Runs (via skill invocations)

This is intentional. Runs is the "primary key of truth."

---

## PR Review Checklist

Every UI PR must answer:

| # | Question | Pass Criteria |
|---|----------|---------------|
| 1 | What is the **primary entity**? | Named in Entity Order Map |
| 2 | What order is this page? | O1-O5, stated explicitly |
| 3 | Does this introduce a second O4? | NO (INV-2 violation) |
| 4 | If cross-linked, does it land on O3? | YES (INV-3) |
| 5 | Is O5 a popup/modal? | YES (INV-4) |
| 6 | Are values truncated by default? | YES (INV-6) |
| 7 | Is breadcrumb continuous? | YES (INV-5) |

**If any answer is unclear or NO where YES required → REJECT**

---

## Implementation Priority

### Implement Now (O1-O3)
All entities need O1-O3 for accountability.

### Implement On Demand (O4)
Only when users **actually ask** for related data drill-down.

### Implement Last (O5)
Only when an action is **unavoidable** and must be explicit.

**Let usage pull depth, not design ambition.**

---

## Anti-Patterns (Forbidden)

| Anti-Pattern | Why Forbidden | Detection |
|--------------|---------------|-----------|
| O4 → O4 nesting | Infinite depth, audit-hostile | PR review question #3 |
| O5 with navigation | Action pages don't navigate | Has "View X" buttons |
| Cross-link to O2 | User wanted specific entity | Landing on list, not detail |
| Inline full JSON | Accidental data leak | No truncation visible |
| Breadcrumb reset on cross | Context lost | Breadcrumb shows only current entity |
| O1 with actions | Dashboard is read-only | Buttons that mutate state |

---

## Governance

This PIN has **LAW** status. Violations are:

1. **Caught in PR review** → Reject, fix required
2. **Caught post-merge** → Hotfix, incident created
3. **Pattern repeated** → Architectural review required

No exceptions without founder approval and PIN amendment.

---

## Related PINs

- PIN-183: Runtime v1 Feature Freeze
- PIN-184: Founder-Led Beta Criteria
- PIN-185: Phase 5E-5 Contract Surfacing Fixes

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | Created PIN-186 - Page Order & Drill-Down Invariants codified as UI law |
