# L2.2 Capability Binding Draft Summary

**Status:** PHASE 2.2 OUTPUT (DRAFT)
**Created:** 2026-01-07
**Purpose:** Map L2.1 UI Intent rows to Phase 1 capabilities for thin UI implementation

---

## Binding Methodology

### Binding Rules Applied

1. **READ-only bindings first** — prefer capabilities with `mode=READ` and `mutates_state=NO`
2. **WRITE/ACTIVATE as hypotheses** — only bind if capability exists, flag unknowns
3. **Safe for thin UI** — YES if READ/DOWNLOAD only OR clearly guarded mutations
4. **UNBINDABLE** — mark if no Phase 1 capability can service the row

### Confidence Levels

| Level | Definition | Count |
|-------|------------|-------|
| **HIGH** | Capability exists, semantics clear, no blockers | 35 |
| **MEDIUM** | Capability exists but has risk flags or unknowns | 11 |
| **LOW** | Capability missing, has major blockers, or UNBINDABLE | 6 |

---

## Binding Statistics

### By Domain

| Domain | Total Rows | HIGH | MEDIUM | LOW | UNBINDABLE |
|--------|------------|------|--------|-----|------------|
| Overview | 3 | 0 | 0 | 3 | 0 |
| Activity | 10 | 10 | 0 | 0 | 0 |
| Incidents | 11 | 7 | 4 | 0 | 0 |
| Policies | 15 | 7 | 0 | 3 | 5 |
| Logs | 13 | 8 | 5 | 0 | 0 |
| **TOTAL** | **52** | **32** | **9** | **6** | **5** |

### By Safe Status

| Status | Count | Percentage |
|--------|-------|------------|
| **YES** (safe for thin UI) | 39 | 75% |
| **YES*** (safe with caveats) | 2 | 4% |
| **NO** (not safe for thin UI) | 11 | 21% |

---

## ROWS SAFE FOR WIREFRAME CONSOLE (39 + 2 with caveats)

### Activity Domain — 10/10 SAFE

| Panel ID | Panel Name | Order | Capability | Notes |
|----------|------------|-------|------------|-------|
| ACT-EX-AR-O1 | Active Runs Summary | O1 | CAP-ACT-LIST | READ-only |
| ACT-EX-AR-O2 | Active Runs List | O2 | CAP-ACT-LIST | READ-only |
| ACT-EX-CR-O1 | Completed Runs Summary | O1 | CAP-ACT-LIST | READ-only |
| ACT-EX-CR-O2 | Completed Runs List | O2 | CAP-ACT-LIST | READ + DOWNLOAD |
| ACT-EX-CR-O3 | Completed Run Detail | O3 | CAP-ACT-DETAIL | READ + DOWNLOAD |
| ACT-EX-RD-O1 | Run Details Summary | O1 | CAP-ACT-DETAIL | READ-only |
| ACT-EX-RD-O2 | Run Steps List | O2 | CAP-ACT-DETAIL | READ-only |
| ACT-EX-RD-O3 | Run Step Detail | O3 | CAP-ACT-DETAIL | READ + DOWNLOAD |
| ACT-EX-RD-O4 | Run Context | O4 | CAP-ACT-DETAIL | READ-only |
| ACT-EX-RD-O5 | Run Proof | O5 | CAP-ACT-DETAIL | READ + DOWNLOAD |

### Incidents Domain — 9/11 SAFE (2 with caveats)

| Panel ID | Panel Name | Order | Capability | Notes |
|----------|------------|-------|------------|-------|
| INC-AI-OI-O1 | Open Incidents Summary | O1 | CAP-INC-LIST | READ-only |
| INC-AI-OI-O2 | Open Incidents List | O2 | CAP-INC-LIST + ACK | READ + bulk ACK (caveat: ACK irreversibility unknown) |
| INC-AI-ID-O1 | Incident Summary | O1 | CAP-INC-GET | READ-only |
| INC-AI-ID-O2 | Incident Timeline | O2 | CAP-INC-GET | READ-only |
| INC-AI-ID-O3 | Incident Detail | O3 | CAP-INC-GET + ACK + RESOLVE | READ + mutations (caveat: reversibility unknown) |
| INC-AI-ID-O4 | Incident Impact | O4 | CAP-INC-GET | READ-only |
| INC-HI-RI-O1 | Resolved Incidents Summary | O1 | CAP-INC-LIST | READ-only |
| INC-HI-RI-O2 | Resolved Incidents List | O2 | CAP-INC-LIST | READ + DOWNLOAD |
| INC-HI-RI-O3 | Resolved Incident Detail | O3 | CAP-INC-GET | READ + DOWNLOAD |
| INC-HI-RI-O4 | Resolved Incident Context | O4 | CAP-INC-GET | READ-only |
| INC-HI-RI-O5 | Resolved Incident Proof | O5 | CAP-INC-GET + EXPORT | READ + DOWNLOAD (latency risk) |

### Policies Domain — 7/15 SAFE (READ-only surfaces)

| Panel ID | Panel Name | Order | Capability | Notes |
|----------|------------|-------|------------|-------|
| POL-AP-BP-O1 | Budget Policies Summary | O1 | CAP-POL-CONSTRAINTS | READ-only |
| POL-AP-BP-O2 | Budget Policies List | O2 | CAP-POL-CONSTRAINTS | READ-only (toggle disabled) |
| POL-AP-RL-O1 | Rate Limits Summary | O1 | CAP-POL-CONSTRAINTS | READ-only |
| POL-AP-RL-O2 | Rate Limits List | O2 | CAP-POL-CONSTRAINTS | READ-only (toggle disabled) |
| POL-AP-AR-O1 | Approval Rules Summary | O1 | CAP-POL-GUARDRAIL | READ-only |
| POL-AP-AR-O2 | Approval Rules List | O2 | CAP-POL-GUARDRAIL | READ-only (toggle disabled) |
| POL-AP-AR-O4 | Approval Rule Impact | O4 | CAP-POL-GUARDRAIL | READ-only |

### Logs Domain — 13/13 SAFE

| Panel ID | Panel Name | Order | Capability | Notes |
|----------|------------|-------|------------|-------|
| LOG-AL-SA-O1 | System Audit Summary | O1 | CAP-LOG-LIST | READ-only |
| LOG-AL-SA-O2 | System Audit List | O2 | CAP-LOG-LIST | READ + DOWNLOAD (CSV risk mitigated) |
| LOG-AL-SA-O3 | System Audit Detail | O3 | CAP-LOG-DETAIL | READ + DOWNLOAD |
| LOG-AL-SA-O5 | System Audit Proof | O5 | CAP-LOG-DETAIL | READ + DOWNLOAD |
| LOG-AL-UA-O1 | User Audit Summary | O1 | CAP-LOG-LIST | READ-only |
| LOG-AL-UA-O2 | User Audit List | O2 | CAP-LOG-LIST | READ + DOWNLOAD (CSV risk mitigated) |
| LOG-AL-UA-O3 | User Audit Detail | O3 | CAP-LOG-DETAIL | READ + DOWNLOAD |
| LOG-AL-UA-O5 | User Audit Proof | O5 | CAP-LOG-DETAIL | READ + DOWNLOAD |
| LOG-ET-TD-O1 | Trace Summary | O1 | CAP-LOG-LIST | READ-only |
| LOG-ET-TD-O2 | Trace List | O2 | CAP-LOG-LIST | READ + DOWNLOAD (CSV risk mitigated) |
| LOG-ET-TD-O3 | Trace Detail | O3 | CAP-LOG-DETAIL | READ + DOWNLOAD |
| LOG-ET-TD-O4 | Trace Context | O4 | CAP-LOG-DETAIL | READ-only |
| LOG-ET-TD-O5 | Trace Proof | O5 | CAP-LOG-DETAIL | READ + DOWNLOAD |

---

## ROWS NOT SAFE FOR WIREFRAME CONSOLE (11 rows)

### Overview Domain — 3/3 NOT SAFE

| Panel ID | Panel Name | Blocking Reason |
|----------|------------|-----------------|
| OVW-SH-CS-O1 | System Status Summary | NO Customer Console API; ADAPTER BYPASSED; Founder-only |
| OVW-SH-HM-O1 | Health Metrics Summary | NO Customer Console API; ADAPTER BYPASSED |
| OVW-SH-HM-O2 | Health Metrics List | NO Customer Console API; ADAPTER BYPASSED |

**Recommendation:** Show "Coming Soon" placeholder or defer Overview domain.

### Policies Domain — 8/15 NOT SAFE

| Panel ID | Panel Name | Blocking Reason |
|----------|------------|-----------------|
| POL-AP-BP-O3 | Budget Policy Detail | GC_L NOT IMPLEMENTED; mutations blocked |
| POL-AP-RL-O3 | Rate Limit Detail | GC_L NOT IMPLEMENTED; mutations blocked |
| POL-AP-AR-O3 | Approval Rule Detail | GC_L NOT IMPLEMENTED; mutations blocked |
| POL-PA-PC-O1 | Policy Changes Summary | UNBINDABLE — no capability exists |
| POL-PA-PC-O2 | Policy Changes List | UNBINDABLE — no capability exists |
| POL-PA-PC-O3 | Policy Change Detail | UNBINDABLE — no capability exists |
| POL-PA-PC-O4 | Policy Change Context | UNBINDABLE — no capability exists |
| POL-PA-PC-O5 | Policy Change Proof | UNBINDABLE — no capability exists |

**Recommendation:**
- O3 panels: Show read-only view with "Configuration coming soon" for mutations
- Policy Changes (5 rows): Defer to post-v1 or implement new capability

---

## CAPABILITY COVERAGE ANALYSIS

### Capabilities Used (12 of 38)

| Capability ID | Capability Name | L2.1 Rows Served |
|---------------|-----------------|------------------|
| CAP-ACT-LIST | List Activities | 5 |
| CAP-ACT-DETAIL | Get Activity Detail | 7 |
| CAP-INC-LIST | List Incidents | 5 |
| CAP-INC-GET | Get Incident Detail | 9 |
| CAP-INC-ACK | Acknowledge Incident | 2 |
| CAP-INC-RESOLVE | Resolve Incident | 1 |
| CAP-INC-TIMELINE | Get Decision Timeline | 1 |
| CAP-INC-EXPORT | Export Evidence Report | 1 |
| CAP-POL-CONSTRAINTS | Get Policy Constraints | 6 |
| CAP-POL-GUARDRAIL | Get Guardrail Detail | 4 |
| CAP-LOG-LIST | List Logs | 6 |
| CAP-LOG-DETAIL | Get Log Detail | 8 |
| CAP-LOG-EXPORT | Export Logs | 5 |

### Capabilities NOT Used (26 of 38)

| Category | Capability IDs | Reason |
|----------|---------------|--------|
| Overview (5) | CAP-OVW-* | No Customer Console API |
| Connectivity (6) | CAP-KEY-* | Secondary nav, not in Core Lenses |
| Account (12) | CAP-AUTH-*, CAP-TENANT-*, CAP-SETTINGS-* | Secondary nav, not in Core Lenses |
| Incidents (3) | CAP-INC-SEARCH, CAP-INC-NARRATIVE | Partial alignment, may add later |

---

## BLOCKING UNKNOWNS REQUIRING ELICITATION

| Unknown | Affected Rows | Elicitation Question |
|---------|---------------|---------------------|
| ACK reversibility | INC-AI-OI-O2, INC-AI-ID-O3 | "Can acknowledged incidents be un-acknowledged?" |
| RESOLVE reversibility | INC-AI-ID-O3 | "Can resolved incidents be reopened?" |
| GC_L implementation | POL-*-O3 (3 rows) | "Are policy mutations planned for v1?" |
| Policy audit capability | POL-PA-PC-* (5 rows) | "Should policy change audit be exposed in v1?" |
| Overview API | OVW-* (3 rows) | "Should Overview be Customer Console or Founder-only?" |

---

## V1 THIN UI IMPLEMENTATION GUIDANCE

### Priority 1: Implement First (35 rows)

All Activity and Logs rows plus READ-only Incidents and Policies:
- Full Activity domain (10 rows)
- Full Logs domain (13 rows)
- Incidents READ paths (7 rows)
- Policies READ paths (5 rows)

### Priority 2: Implement with Caveats (4 rows)

Incidents with mutations (ACK/RESOLVE):
- INC-AI-OI-O2 (bulk ACK)
- INC-AI-ID-O3 (ACK + RESOLVE)
- INC-HI-RI-O5 (export with latency warning)
- Plus 1 more incident timeline row

**Caveat:** Show confirmation with "This action cannot be undone" until reversibility is confirmed.

### Priority 3: Defer or Placeholder (11 rows)

- Overview domain: "Coming Soon" placeholder
- Policy O3 panels: Read-only with disabled mutations
- Policy Changes: "Coming Soon" placeholder

---

## Attestation

```
✔ 52 L2.1 rows evaluated
✔ 12 Phase 1 capabilities bound
✔ 39 rows marked SAFE for thin UI
✔ 11 rows marked NOT SAFE (with reasons)
✔ 5 blocking unknowns documented
✔ Implementation priorities defined
```
