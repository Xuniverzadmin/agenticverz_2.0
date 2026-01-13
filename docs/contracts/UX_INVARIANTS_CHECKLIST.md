# UX Invariants Checklist (FROZEN)

**Status:** FROZEN
**Effective:** 2026-01-13
**Scope:** Customer Console, Preflight Console
**Reference:** PIN-412 (Domain Design)

---

## Purpose

This checklist enforces cognitive coherence across all domains. It must be satisfied before any UI implementation begins.

**Principle:**
> Implementation without UX invariants leads to rework.
> Lock the mental model first. Code follows.

---

## 1. Terminology Lock (GLOBAL)

### Frozen Terms

| Concept | Locked Term | FORBIDDEN Variants |
|---------|-------------|-------------------|
| Execution instance | **LLM Run** | Run, Job, Task, Execution |
| Governance rule | **Policy Rule** | Policy, Guard, Constraint, Guardrail |
| Quantitative cap | **Limit** | Rule, Budget (alone), Threshold (alone) |
| Failure event | **Incident** | Alert, Error, Issue, Problem |
| Raw audit record | **Proof** | Logs, Details, Debug, Raw |
| Cross-domain context | **Evidence** | Metadata, Context, Related |
| Change request | **Proposal** | Draft, Suggestion, Request |

### Sidebar Labels (Exact)

| Position | Label | Route Prefix |
|----------|-------|--------------|
| 1 | Overview | `/precus/overview` |
| 2 | Activity | `/precus/activity` |
| 3 | Incidents | `/precus/incidents` |
| 4 | Policies | `/precus/policies` |
| 5 | Logs | `/precus/logs` |

**Invariant:** Sidebar labels MUST match domain names exactly. No abbreviations.

---

## 2. Breadcrumb Grammar

### Pattern

```
Domain › Subdomain › Topic › Entity ID
```

### Direction

LEFT → RIGHT = CAUSAL → SPECIFIC

### Locked Examples

| Page | Breadcrumb |
|------|------------|
| LLM Runs list (Live) | `Activity › LLM Runs › Live` |
| LLM Run detail | `Activity › LLM Runs › Live › run_7f3e2a1b` |
| Active incidents | `Incidents › Events › Active` |
| Incident detail | `Incidents › Events › Active › inc_9a8b7c6d` |
| Policy rules | `Policies › Governance › Active Rules` |
| Rule detail | `Policies › Governance › Active Rules › PR-042` |
| Budget limits | `Policies › Limits › Budget` |
| Limit detail | `Policies › Limits › Budget › LIM-001` |

### Forbidden Patterns

| Pattern | Why Wrong |
|---------|-----------|
| `Active › Governance › PR-042` | Topic before subdomain |
| `Rules › Policies › Details` | Backwards hierarchy |
| `PR-042` (alone) | No context |
| `Policies / Governance / Rules` | Wrong separator (use ›) |

---

## 3. Drill-Depth Rules

### Visibility Matrix

| Order | Customer Console | Preflight Console | UI Behavior |
|-------|------------------|-------------------|-------------|
| O1 | ✅ Visible | ✅ Visible | Navigation panels |
| O2 | ✅ Visible | ✅ Visible | List/Table views |
| O3 | ✅ Visible | ✅ Visible | Detail pages |
| O4 | ❌ HIDDEN | ✅ Visible | Evidence panels |
| O5 | ❌ HIDDEN | ✅ Visible | Proof panels |

### Enforcement Rules

| Rule ID | Rule | Description |
|---------|------|-------------|
| NO-TEASE-001 | No O4/O5 CTAs | Customer Console MUST NOT show O4/O5 CTAs that 403 |
| NO-TEASE-002 | No Evidence/Proof labels | Customer Console MUST NOT show "Evidence" or "Proof" sections |
| NO-TEASE-003 | No disabled buttons | Customer Console MUST NOT show disabled O4/O5 buttons |
| NATURAL-004 | Natural continuation | Preflight O4/O5 appears as natural continuation, not "debug mode" |
| GATE-005 | Render-time check | O4/O5 components check console_type before render, not after |

### Customer Console O3 Content

| Show | Hide |
|------|------|
| Summary | Evidence section |
| Status | Proof section |
| Timeline | Hash verification |
| Linked entities | "Upgrade to see more" |

---

## 4. Topic Symmetry

### Each Topic Answers ONE Question

| Domain | Subdomain | Topic | Question |
|--------|-----------|-------|----------|
| Activity | LLM Runs | Live | "What is currently executing?" |
| Activity | LLM Runs | Completed | "What finished recently?" |
| Activity | LLM Runs | Risk Signals | "What crossed a threshold?" |
| Incidents | Events | Active | "What is currently broken?" |
| Incidents | Events | Resolved | "What was fixed?" |
| Incidents | Events | Historical | "What patterns exist?" |
| Policies | Governance | Active Rules | "What rules are enforcing?" |
| Policies | Governance | Proposals | "What changes are pending?" |
| Policies | Governance | Retired | "What was deprecated?" |
| Policies | Limits | Budget | "What cost caps exist?" |
| Policies | Limits | Rate | "What throughput caps exist?" |
| Policies | Limits | Threshold | "What quality caps exist?" |

### Violation Test

If a topic answers TWO questions → split it.

---

## 5. O1 Panel Intent Test

### The Test

For every O1 panel, ask:

> "If I remove this panel, does NAVIGATION become worse?"

| Answer | Verdict |
|--------|---------|
| "Yes, I lose a navigation path" | ✅ Valid |
| "Yes, I lose information" | ❌ Move to O2 |
| "No difference" | ❌ Delete |

### O1 Must Be

- Orientation
- Framing
- Entry points

### O1 Must NOT Be

- Data display
- Counts
- Metrics
- Loading states

---

## 6. Empty State Rules

### Required States

| State | Message Pattern | CTA |
|-------|-----------------|-----|
| No data ever | "No {entity_plural} yet" | None or "Learn more" |
| No filter match | "No {entity_plural} match your filters" | "Clear filters" |
| Loading | Skeleton (not spinner) | None |
| Error | "Failed to load {entity_plural}" | "Retry" |

### Forbidden States

| Pattern | Why Wrong |
|---------|-----------|
| Blank table | User thinks broken |
| "0 results" header | Confusing with filters |
| Spinner > 2s | Use skeleton |

---

## 7. CTA Label Rules

### Verb Patterns

| Action | Verb | Example |
|--------|------|---------|
| Navigate to list | "View" | "View Active Incidents" |
| Navigate to detail | "Inspect" | "Inspect Rule" |
| Filter | "Show" | "Show Failed Only" |
| Action | Imperative | "Retry", "Approve", "Reject" |

### Forbidden Labels

| Label | Why Wrong | Correct |
|-------|-----------|---------|
| "Click here" | No information | "View Details" |
| "Details" | Noun | "View Details" |
| "More" | Ambiguous | "View All" |
| "Go" | Generic | "View {Entity}" |

---

## 8. Cross-Domain Links

### Link Format

```
{Relationship}: {Entity ID}
```

### Examples

| From | To | Label |
|------|-----|-------|
| LLM Run | Incident | "Caused Incident: inc_xxx" |
| LLM Run | Policy Rule | "Triggered Rule: PR-xxx" |
| Incident | LLM Run | "Source LLM Run: run_xxx" |
| Incident | Policy Rule | "Violated Rule: PR-xxx" |
| Policy Rule | LLM Runs | "Affected LLM Runs (N)" |
| Policy Rule | Incidents | "Caused Incidents (N)" |

---

## 9. Table Column Headers

### Frozen Headers

| Concept | Header | NOT |
|---------|--------|-----|
| Primary ID | "ID" or "{Entity} ID" | "Identifier", "Key" |
| Status | "Status" | "State", "Condition" |
| Severity | "Severity" | "Priority", "Level" |
| Risk classification | "Risk" | "Risk Level", "Danger" |
| Creation time | "Created" | "Created At", "Timestamp" |
| Last update | "Updated" | "Modified", "Changed" |
| Scope | "Scope" | "Level", "Applies To" |

---

## 10. Incident Lifecycle Display (PIN-412)

### ACKED State Handling (FROZEN)

| DB State | UX Topic | Display |
|----------|----------|---------|
| ACTIVE | Active | Default row |
| ACKED | Active | Row with "Acknowledged" badge |
| RESOLVED | Resolved | Default row |

**Invariants:**
- ACKED is never a separate topic/tab
- ACKED shown as badge inside Active topic
- API returns `lifecycle_state` field for badge rendering
- `topic=ACTIVE` query returns both ACTIVE and ACKED states

**API Mapping:**
```
GET /api/v1/runtime/incidents?topic=ACTIVE   → ACTIVE + ACKED states
GET /api/v1/runtime/incidents?topic=RESOLVED → RESOLVED state only
```

---

## 11. Column Label Mapping (PIN-412)

### Frozen Labels

| API Field | UI Label |
|-----------|----------|
| `max_value` | Limit Value |
| `integrity_status` | Integrity |
| `integrity_score` | Integrity Score |
| `trigger_count_30d` | Triggers (30d) |
| `breach_count_30d` | Breaches (30d) |
| `lifecycle_state` | Status |
| `enforcement_mode` | Enforcement |
| `limit_category` | Category |

---

## 12. Pre-Implementation Checklist

Before implementing ANY domain UI, verify:

- [ ] Sidebar label matches frozen term
- [ ] All breadcrumbs follow LEFT → RIGHT pattern
- [ ] O4/O5 HIDDEN in Customer Console (not disabled)
- [ ] Every topic answers exactly ONE question
- [ ] Every O1 panel passes navigation value test
- [ ] Empty states defined for all O2 lists
- [ ] CTA labels use correct verb patterns
- [ ] Cross-domain links use `{Relationship}: {Entity ID}` format
- [ ] Column headers match frozen terms
- [ ] No forbidden variants appear anywhere

---

## Enforcement

This checklist is enforced by:

1. **Design review** — Before implementation
2. **Code review** — During implementation
3. **UI hygiene check** — Post-implementation

Violations block merge.

---

## References

- PIN-412: Domain Design — Incidents & Policies
- PIN-411: Activity Domain (closed)
- `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`
