# Known Gaps: Customer Console v1

**Status:** DESCRIPTIVE (No Fixes Applied)
**Date:** 2025-12-29
**Auditor:** Claude (BL-CONSOLE-001 compliant)
**Reference:** `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`

---

## Purpose

This document consolidates all known gaps between the **frozen Customer Console v1 Constitution** and the **current implementation**.

Gaps are described, not fixed. All remediation requires human approval.

---

## Gap Summary

| Category | Count | Severity Distribution |
|----------|-------|----------------------|
| Missing Pages | 3 | 1 HIGH, 2 MEDIUM |
| Terminology | 4 | 3 HIGH, 1 MEDIUM |
| Structure | 3 | 1 HIGH, 2 MEDIUM |
| Jurisdiction | 8 | 8 HIGH |
| Route Placement | 3 | 3 LOW |
| **Total** | **21** | — |

---

## 1. MISSING PAGES

### GAP-001: Logs Page Missing

| Field | Value |
|-------|-------|
| **ID** | GAP-001 |
| **Category** | Missing Page |
| **Severity** | **HIGH** |
| **Domain** | Logs (Core Lenses) |
| **Constitution Requirement** | "What is the raw truth?" — Traces, Audit, Proof |
| **Current State** | No page exists |
| **Route Expected** | `/guard/logs` |
| **Component Expected** | `CustomerLogsPage.tsx` |

**Impact:** One of five frozen domains has no implementation. Customers cannot access raw execution records.

---

### GAP-002: Integrations Page Missing

| Field | Value |
|-------|-------|
| **ID** | GAP-002 |
| **Category** | Missing Page |
| **Severity** | MEDIUM |
| **Section** | Connectivity |
| **Constitution Requirement** | Integrations in Connectivity section |
| **Current State** | No page exists |
| **Route Expected** | `/guard/integrations` |
| **Component Expected** | `CustomerIntegrationsPage.tsx` |

**Impact:** Connectivity section incomplete. Not blocking for v1 MVP.

---

### GAP-003: Users Page Missing

| Field | Value |
|-------|-------|
| **ID** | GAP-003 |
| **Category** | Missing Page |
| **Severity** | MEDIUM |
| **Section** | Administration |
| **Constitution Requirement** | Users in Administration section |
| **Current State** | No page exists |
| **Route Expected** | `/guard/users` |
| **Component Expected** | `CustomerUsersPage.tsx` |

**Impact:** Administration section incomplete. Team management not available.

---

## 2. TERMINOLOGY GAPS

### GAP-004: "Home" Should Be "Overview"

| Field | Value |
|-------|-------|
| **ID** | GAP-004 |
| **Category** | Terminology |
| **Severity** | **HIGH** |
| **Location** | `GuardLayout.tsx:29` |
| **Current Term** | "Home" |
| **Canonical Term** | "Overview" |
| **Constitution Reference** | Frozen domain: Overview — "Is the system okay right now?" |

**Impact:** Mental model mismatch. "Home" implies navigation, not status assessment.

---

### GAP-005: "Runs" Should Be "Activity"

| Field | Value |
|-------|-------|
| **ID** | GAP-005 |
| **Category** | Terminology |
| **Severity** | **HIGH** |
| **Location** | `GuardLayout.tsx:30` |
| **Current Term** | "Runs" |
| **Canonical Term** | "Activity" |
| **Constitution Reference** | Frozen domain: Activity — "What ran / is running?" |

**Impact:** "Runs" is implementation-specific. "Activity" is user-centric.

---

### GAP-006: "Limits & Usage" Should Be "Policies"

| Field | Value |
|-------|-------|
| **ID** | GAP-006 |
| **Category** | Terminology |
| **Severity** | **HIGH** |
| **Location** | `GuardLayout.tsx:31` |
| **Current Term** | "Limits & Usage" |
| **Canonical Term** | "Policies" |
| **Constitution Reference** | Frozen domain: Policies — "How is behavior defined?" |

**Impact:** "Limits" is a subset of Policies. Broader abstraction needed for future expansion.

---

### GAP-007: "Support" Not In Constitution

| Field | Value |
|-------|-------|
| **ID** | GAP-007 |
| **Category** | Terminology |
| **Severity** | MEDIUM |
| **Location** | `GuardLayout.tsx:36` |
| **Current State** | Support page in sidebar |
| **Constitution State** | Not listed in frozen sidebar structure |

**Impact:** Extra item in sidebar. Not harmful but not constitutional.

---

## 3. STRUCTURE GAPS

### GAP-008: No Sidebar Section Separation

| Field | Value |
|-------|-------|
| **ID** | GAP-008 |
| **Category** | Structure |
| **Severity** | **HIGH** |
| **Location** | `GuardLayout.tsx` NAV_ITEMS |
| **Constitution Requirement** | Three sections: Core Lenses (top), Connectivity (middle), Administration (bottom) |
| **Current State** | Single flat list of 8 items |

**Impact:** Mental model confusion. Users cannot distinguish domain lenses from utilities.

**Constitution Structure:**
```
┌─────────────────────────────┐
│ CORE LENSES                 │  ← Missing
│   Overview                  │
│   Activity                  │
│   Incidents                 │
│   Policies                  │
│   Logs                      │
├─────────────────────────────┤  ← Missing
│ CONNECTIVITY                │  ← Missing
│   Integrations              │
│   API Keys                  │
├─────────────────────────────┤  ← Missing
│ ADMINISTRATION              │  ← Missing
│   Users                     │
│   Settings                  │
│   Billing                   │
│   Account                   │
└─────────────────────────────┘
```

---

### GAP-009: Order O2-O5 Depth Not Formalized

| Field | Value |
|-------|-------|
| **ID** | GAP-009 |
| **Category** | Structure |
| **Severity** | MEDIUM |
| **Constitution Requirement** | Orders O1-O5 for epistemic depth |
| **Current State** | O1 (pages) and O3 (incident detail) exist; O2, O4, O5 implicit |

**Orders Required:**
| Order | Meaning | Current State |
|-------|---------|---------------|
| O1 | Summary / Snapshot | Exists (pages) |
| O2 | List of instances | Implicit in pages |
| O3 | Detail / Explanation | Exists (incident detail) |
| O4 | Context / Impact | Not formalized |
| O5 | Raw records / Proof | Not formalized |

**Impact:** Depth navigation not consistent across domains.

---

### GAP-010: Sidebar Item Order Incorrect

| Field | Value |
|-------|-------|
| **ID** | GAP-010 |
| **Category** | Structure |
| **Severity** | MEDIUM |
| **Location** | `GuardLayout.tsx` NAV_ITEMS order |
| **Current Order** | Home, Runs, Limits, Incidents, Keys, Settings, Account, Support |
| **Constitution Order** | Overview, Activity, Incidents, Policies, Logs, Integrations, Keys, Users, Settings, Billing, Account |

**Impact:** Navigation order doesn't match constitution.

---

## 4. JURISDICTION GAPS

### GAP-011 to GAP-018: Unprotected Founder Routes

These routes are accessible without Founder authentication:

| GAP ID | Route | Should Be |
|--------|-------|-----------|
| GAP-011 | `/traces` | FNDR only |
| GAP-012 | `/traces/:runId` | FNDR only |
| GAP-013 | `/workers` | FNDR only |
| GAP-014 | `/workers/console` | FNDR only |
| GAP-015 | `/integration` | FNDR only |
| GAP-016 | `/integration/loop/:id` | FNDR only |
| GAP-017 | `/recovery` | FNDR only |
| GAP-018 | `/sba` | FNDR only |

| Field | Value |
|-------|-------|
| **Category** | Jurisdiction |
| **Severity** | **HIGH** (all 8) |
| **Constitution Reference** | Section 5 — Jurisdiction Boundaries |
| **Current State** | Routes in ProtectedRoute wrapper (auth required) but not Founder-specific |
| **Required State** | Routes must verify Founder role/audience |

**Impact:** Non-founders could potentially access Founder-only views.

---

## 5. ROUTE PLACEMENT GAPS

### GAP-019: Credits Route Misplaced

| Field | Value |
|-------|-------|
| **ID** | GAP-019 |
| **Category** | Route Placement |
| **Severity** | LOW |
| **Current Route** | `/credits` |
| **Expected Route** | `/guard/billing` |
| **Constitution Reference** | Billing in Administration section |

**Impact:** Route not under `/guard/*` prefix. Inconsistent with Customer Console structure.

---

### GAP-020: Founder Timeline Route Misplaced

| Field | Value |
|-------|-------|
| **ID** | GAP-020 |
| **Category** | Route Placement |
| **Severity** | LOW |
| **Current Route** | `/founder/timeline` |
| **Expected Route** | `/ops/timeline` |

**Impact:** Inconsistent with Founder Console `/ops/*` prefix.

---

### GAP-021: Founder Controls Route Misplaced

| Field | Value |
|-------|-------|
| **ID** | GAP-021 |
| **Category** | Route Placement |
| **Severity** | LOW |
| **Current Route** | `/founder/controls` |
| **Expected Route** | `/ops/controls` |

**Impact:** Inconsistent with Founder Console `/ops/*` prefix.

---

## 6. GAP PRIORITY MATRIX

### Critical (Block v1 Launch)

| GAP ID | Description | Reason |
|--------|-------------|--------|
| GAP-001 | Logs page missing | Frozen domain incomplete |

### High (Should Fix Before Launch)

| GAP ID | Description | Reason |
|--------|-------------|--------|
| GAP-004 | Home → Overview | Terminology violation |
| GAP-005 | Runs → Activity | Terminology violation |
| GAP-006 | Limits → Policies | Terminology violation |
| GAP-008 | No section separation | Structure violation |
| GAP-011 to GAP-018 | Unprotected routes | Jurisdiction violation |

### Medium (Fix After Launch)

| GAP ID | Description | Reason |
|--------|-------------|--------|
| GAP-002 | Integrations missing | Connectivity incomplete |
| GAP-003 | Users missing | Administration incomplete |
| GAP-007 | Support not in constitution | Extra item |
| GAP-009 | O2-O5 not formalized | Depth inconsistent |
| GAP-010 | Sidebar order wrong | Navigation order |

### Low (Nice to Have)

| GAP ID | Description | Reason |
|--------|-------------|--------|
| GAP-019 | Credits route misplaced | Route prefix |
| GAP-020 | Timeline route misplaced | Route prefix |
| GAP-021 | Controls route misplaced | Route prefix |

---

## 7. REMEDIATION DEPENDENCIES

### Must Fix First

```
GAP-008 (Section separation)
    ↓
GAP-004, GAP-005, GAP-006 (Terminology)
    ↓
GAP-010 (Sidebar order)
    ↓
GAP-001 (Add Logs page)
```

### Can Fix Independently

- GAP-011 to GAP-018 (Jurisdiction) — No dependencies
- GAP-019 to GAP-021 (Route placement) — No dependencies
- GAP-002, GAP-003 (Missing pages) — After structure fixed

---

## 8. CONSTITUTION COMPLIANCE SCORE

| Requirement | Score | Notes |
|-------------|-------|-------|
| Frozen Domains Present | 4/5 (80%) | Logs missing |
| Terminology Aligned | 1/5 (20%) | 4 renames needed |
| Sidebar Sections | 0/3 (0%) | No separation |
| Jurisdiction Clean | 0/8 (0%) | 8 violations |
| Route Prefixes | 8/11 (73%) | 3 misplaced |

**Overall Compliance:** ~35%

---

## 9. GAP REGISTER

| GAP ID | Category | Severity | Status |
|--------|----------|----------|--------|
| GAP-001 | Missing Page | HIGH | OPEN |
| GAP-002 | Missing Page | MEDIUM | OPEN |
| GAP-003 | Missing Page | MEDIUM | OPEN |
| GAP-004 | Terminology | HIGH | OPEN |
| GAP-005 | Terminology | HIGH | OPEN |
| GAP-006 | Terminology | HIGH | OPEN |
| GAP-007 | Terminology | MEDIUM | OPEN |
| GAP-008 | Structure | HIGH | OPEN |
| GAP-009 | Structure | MEDIUM | OPEN |
| GAP-010 | Structure | MEDIUM | OPEN |
| GAP-011 | Jurisdiction | HIGH | OPEN |
| GAP-012 | Jurisdiction | HIGH | OPEN |
| GAP-013 | Jurisdiction | HIGH | OPEN |
| GAP-014 | Jurisdiction | HIGH | OPEN |
| GAP-015 | Jurisdiction | HIGH | OPEN |
| GAP-016 | Jurisdiction | HIGH | OPEN |
| GAP-017 | Jurisdiction | HIGH | OPEN |
| GAP-018 | Jurisdiction | HIGH | OPEN |
| GAP-019 | Route Placement | LOW | OPEN |
| GAP-020 | Route Placement | LOW | OPEN |
| GAP-021 | Route Placement | LOW | OPEN |

---

## CONSOLE CONSTITUTION CHECK

```
- Constitution loaded: YES
- Gaps identified: 21
- Gaps documented: 21
- Severity classified: YES
- Dependencies mapped: YES
- Remediation proposed: NO (requires human approval)
- Auto-applied: NO
```

---

**This is a gap identification document only. No fixes have been applied. All remediation requires human approval.**
