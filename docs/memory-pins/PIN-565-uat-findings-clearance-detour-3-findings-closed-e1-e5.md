# PIN-565: UAT Findings Clearance Detour — 3 Findings Closed (E1-E5)

**Status:** ✅ COMPLETE
**Created:** 2026-02-15
**Category:** Architecture

---

## Summary

Executed UC_UAT_FINDINGS_CLEARANCE_DETOUR_PLAN E1-E5. E1: tsconfig.uat.json scoped to src/features/uat/ (0 TS errors); global typecheck retained as non-blocking debt (293 errors). E2: @playwright/test installed, ESM __dirname fix in uc-uat.spec.ts + bit.spec.ts, npm scripts test:bit/test:uat/test:uat:list added. E3: Gate script corrected — typecheck:uat blocking, typecheck global non-blocking (WARN), Playwright emits actionable errors not silent skip. E4: Signoff v2 supersedes v1, removes false global TS claim, adds exact command outputs. E5: TS debt inventory (293 errors: fops 232, src 42, onboarding 19, 3 remediation waves). All 3 reality-audit findings CLOSED. Commit 13a9c27a.

---

## Details

### Findings Cleared

| # | Finding | Resolution |
|---|---------|------------|
| 1 | Global typecheck fails (293 errors) but signoff claimed PASS | Scoped `tsconfig.uat.json` (0 errors), global retained as non-blocking debt |
| 2 | Playwright not deterministic — missing dep, ESM `__dirname` error | `@playwright/test` installed, `fileURLToPath` fix, npm scripts added |
| 3 | Gate script blocks on global typecheck, ambiguous paths | `typecheck:uat` blocking, `typecheck` non-blocking (WARN), paths documented |

### Artifacts Created

| File | Purpose |
|------|---------|
| `website/app-shell/tsconfig.uat.json` | UAT-scoped TS config |
| `UC_CODEBASE_ELICITATION_VALIDATION_UAT_SIGNOFF_2026-02-15_v2.md` | Corrected signoff |
| `UC_CODEBASE_ELICITATION_VALIDATION_UAT_REALITY_AUDIT_ADDENDUM_2026-02-15.md` | Findings closure |
| `APP_SHELL_TS_DEBT_INVENTORY_2026-02-15.md` | 293-error debt inventory |
| `UC_UAT_FINDINGS_CLEARANCE_DETOUR_IMPLEMENTED_2026-02-15.md` | Implementation evidence |

### Artifacts Modified

| File | Change |
|------|--------|
| `website/app-shell/package.json` | +`@playwright/test`, +`js-yaml`, +6 npm scripts |
| `tests/uat/uc-uat.spec.ts` | ESM `__dirname` fix |
| `tests/bit/bit.spec.ts` | ESM `__dirname` fix |
| `backend/scripts/ops/hoc_uc_validation_uat_gate.sh` | Scoped typecheck, non-blocking global, Playwright error messaging |

### Commit
`13a9c27a` — 16 files, +856/-28
