# Consequences — Folder Summary

**Path:** `backend/app/hoc/hoc_spine/consequences/`  
**Layer:** L5  
**Scripts:** 1

---

## 1. Purpose

After-the-fact reactions. Handles effects (notifications, exports, escalations), not decisions. Triggered only by orchestrator, never by L5.

## 2. What Belongs Here

- Export bundle generation
- Notification dispatch (future)
- Escalation triggers (future)

## 3. What Must NOT Be Here

- Make decisions
- Be called by L5 directly
- Own transaction boundaries

## 4. Script Inventory

| Script | Purpose | Transaction | Cross-domain | Verdict |
|--------|---------|-------------|--------------|---------|
| [export_bundle_adapter.py](export_bundle_adapter.md) | Export Bundle Adapter (L2) | Forbidden | no | OK |

## 5. Assessment

**Correct:** 1/1 scripts pass all governance checks.

**Missing (from reconciliation artifact):**

- Generic PostExecutionHook interface
- Sync vs async consequence separation

## 6. L5 Pairing Aggregate

| Script | Serves Domains | Wired L5 Consumers | Gaps |
|--------|----------------|--------------------|------|
| export_bundle_adapter.py | _none_ | 0 | 0 |

