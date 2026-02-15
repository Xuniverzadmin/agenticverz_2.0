# PIN-556: Cross-Domain E2 Fix — sdk_attestation_driver.py (PIN-520)

**Status:** ✅ COMPLETE
**Created:** 2026-02-12
**Category:** Architecture

---

## Summary

Fixed E2 HIGH cross-domain violation in account/L6_drivers/sdk_attestation_driver.py:32. Replaced forbidden L4 import (from hoc_spine.orchestrator.operation_registry import sql_text) with L6-safe import (from sqlalchemy import text as sql_text). Cross-domain validator now CLEAN: status=CLEAN, count=0, exit 0. Corrected inaccurate advisory claim in UC_EXPANSION_UC018_UC032_implemented.md Gate 3 section. All 8 retest gates pass. Plan doc: UC_EXPANSION_VALIDATOR_AUDIT_AND_FIX_PLAN.md

---

## Details

[Add details here]
