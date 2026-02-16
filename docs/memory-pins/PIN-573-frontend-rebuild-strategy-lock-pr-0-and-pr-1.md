# PIN-573: Frontend Rebuild Strategy Lock: PR-0 and PR-1

**Status:** 📋 LOCKED
**Created:** 2026-02-16
**Category:** Architecture Strategy
**Milestone:** PR-0/PR-1

---

## Summary

Decision locked to build a new parallel frontend package, harden backend L2.1 facade exposure by CUS domain, and execute PR-0/PR-1 before UI implementation.

---

## Details

Loop `L001` initialized via `strategic-thinker-northstar`.

Plan artifact updated at:
- `artifacts/strategic_thinker_loops/L001/L001_micro_execution_plan.md`

Key decisions:
- No app-shell feature extension.
- No mock adapter track.
- Use `stagetest` and `preflight` environments for testing.
- Enforce canonical HOC paths over `/api/v1` legacy prefix.

---

## Related PINs

- [PIN-451](PIN-451-sidebar-domain-expansion---analytics-account-connectivity.md)
- [PIN-490](PIN-490-hoc-spine-constitution-document-authoritative-audit-guide.md)
- [PIN-565](PIN-565-uat-findings-clearance-detour-3-findings-closed-e1-e5.md)
