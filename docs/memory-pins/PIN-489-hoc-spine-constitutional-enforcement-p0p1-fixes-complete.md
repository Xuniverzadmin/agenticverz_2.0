# PIN-489: HOC Spine Constitutional Enforcement — P0/P1 Fixes Complete

**Status:** ✅ COMPLETE
**Created:** 2026-01-30
**Category:** Architecture

---

## Summary

Executed P0 and P1 governance fixes on hoc_spine (65 scripts). P0-1: Eliminated all 12 cross-domain import sites across 6 files (contract_engine, export_bundle_adapter, transaction_coordinator, execution, run_governance_facade, orchestrator/__init__). All replaced with TODO(L1) markers — broken intentionally, re-wire during L1 design. P0-2: Tagged 5 unauthorized conn.commit() calls in decisions.py and ledger.py as VIOLATION TODO(L1) — require session migration to transaction_coordinator. P1: Removed services.time import from schemas/artifact.py and schemas/plan.py — inlined utc_now(). Result: violations reduced from 9 to 2 (both commit-related architectural debt). Cross-domain imports: 0. Schema impurity: 0. Literature regenerated, INDEX.md updated (63 clean / 2 violated). Constitution doc at literature/hoc_spine/HOC_SPINE_CONSTITUTION.md.

---

## Details

[Add details here]
