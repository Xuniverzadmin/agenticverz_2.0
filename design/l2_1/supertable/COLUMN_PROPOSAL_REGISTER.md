# L2.1 Column Proposal Register

**Status:** PHASE 2.1 OUTPUT
**Created:** 2026-01-07
**Purpose:** Track proposed new columns not in the base schema

---

## Base Schema Columns (NON-REMOVABLE)

```
Domain
Subdomain
Topic
Topic ID
Panel ID
Panel Name
Order
Ranking Dimension
Nav Required
Filtering
Selection Mode
Read
Download
Write
Write Action
Activate
Activate Action
Action Layer
Confirmation Required
Control Set (Explicit)
Visible by Default
Replay
Notes
```

---

## Proposed Columns

| proposed_column | purpose | example_values | derived_from | risk_of_overlap |
|-----------------|---------|----------------|--------------|-----------------|
| `danger_level` | Indicate destructive potential of actions | NONE, LOW, MEDIUM, HIGH, CRITICAL | Repeated pattern in Notes for actions requiring confirmation | Low — orthogonal to Confirmation Required |
| `export_format_hint` | Specify preferred export format for DOWNLOAD | JSON, CSV, PDF, NONE | EXPORT_PDF proposal suggests format matters | Medium — could overlap with Write Action |
| `bulk_limit_hint` | Suggested max items for bulk operations | 10, 50, 100, UNLIMITED | O2 lists with SELECT_MULTI need guidance | Low — purely advisory |
| `requires_interpreter` | Surface requires IR interpreter for rendering | YES, NO | Direct from seed o3+o4+o5 patterns | Low — structural |
| `terminal_order` | Is this the deepest order for this topic? | YES, NO | O5 rows are always terminal | Low — derivable but useful |
| `entry_point` | Can user arrive here directly or only via navigation? | DIRECT, NAV_ONLY | Nav Required = YES implies NAV_ONLY | High — duplicates Nav Required |

---

## Analysis

### danger_level

**Observation:** Multiple rows have actions that require confirmation. But "confirmation required" is binary, while destructive potential varies:

| Action | Current | Proposed danger_level |
|--------|---------|----------------------|
| ACKNOWLEDGE | Confirmation = YES | LOW (reversible via REOPEN?) |
| RESOLVE | Confirmation = YES | MEDIUM (harder to undo) |
| ACTIVATE policy | Confirmation = YES | MEDIUM |
| DEACTIVATE policy | Confirmation = YES | HIGH (stops enforcement) |

**Proposal:** Add `danger_level` to provide UI with graduated warning strength.

**Recommendation:** ACCEPT — provides UX value without semantic overlap.

---

### export_format_hint

**Observation:** DOWNLOAD appears in 15 rows but format requirements differ:
- Logs: JSON or CSV
- Incidents Proof: PDF (legal grade)
- Activity: CSV

**Proposal:** Add `export_format_hint` to specify expected format.

**Alternative:** Keep in Notes column.

**Recommendation:** DEFER — evaluate if EXPORT_PDF control is accepted first.

---

### bulk_limit_hint

**Observation:** SELECT_MULTI appears in 8 rows. Some operations (bulk download, bulk acknowledge) may have practical limits not expressed in the schema.

**Proposal:** Add `bulk_limit_hint` to provide L1 with guidance.

**Recommendation:** REJECT — this is implementation detail, not UI intent.

---

### requires_interpreter

**Observation:** The L2.1 seed has `requires_interpreter` flag per surface. This affects rendering but is not in the supertable.

**Proposal:** Add `requires_interpreter` column.

**Recommendation:** ACCEPT — directly derived from seed, affects L1 rendering.

---

### terminal_order

**Observation:** O5 rows are always terminal (no further navigation). This could be explicit.

**Proposal:** Add `terminal_order` column.

**Recommendation:** REJECT — derivable from Order column (O5 always terminal, or max Order for topic).

---

### entry_point

**Observation:** `Nav Required = YES` means user must navigate from another panel. The inverse (`DIRECT`) means the panel is an entry point.

**Proposal:** Add `entry_point` column for clarity.

**Recommendation:** REJECT — duplicates Nav Required (just inverted).

---

## Summary

| Column | Status | Recommendation | Action Required |
|--------|--------|----------------|-----------------|
| danger_level | PROPOSED | ACCEPT | Human review |
| export_format_hint | PROPOSED | DEFER | Depends on EXPORT_PDF control decision |
| bulk_limit_hint | PROPOSED | REJECT | N/A |
| requires_interpreter | PROPOSED | ACCEPT | Human review |
| terminal_order | PROPOSED | REJECT | N/A |
| entry_point | PROPOSED | REJECT | N/A |

---

## Recommended New Columns (If Accepted)

1. **danger_level** — Values: NONE, LOW, MEDIUM, HIGH, CRITICAL
2. **requires_interpreter** — Values: YES, NO (from seed)

---

## Review Required

Before Phase 2.2, human must:
1. Accept or reject `danger_level`
2. Accept or reject `requires_interpreter`
3. Decide on `export_format_hint` after EXPORT_PDF control decision
