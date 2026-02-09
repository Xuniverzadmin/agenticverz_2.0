# Domain Linkage Plan v3 (HOC)

**Date:** 2026-02-09  
**Scope:** LLM run monitoring linkages across Activity, Incidents, Policies, Controls, Logs  
**Audience:** Claude execution plan  
**Goal:** Complete run-scoped linkage validation and fix the remaining production blocker.

---

## 0. Current State (v2 Execution Summary)

**Phase A — Schema Verification:** PASS 4/4  
- 7 missing tables auto-created for stamped DB

**Phase B — Data Linkage:** PASS 4/4  
- All run_id paths resolve

**Phase C — L4 Coordinators:**  
- RunEvidence: FULL PASS (2 incidents + 3 policies + 1 limit + 3 decisions)  
- RunProof: **GAP** (broken import in `pg_store.py`)

**Phase D — Governance Logs:** PASS  
- LogsFacade returns 3 run‑scoped events

**Blocking Gap:**  
