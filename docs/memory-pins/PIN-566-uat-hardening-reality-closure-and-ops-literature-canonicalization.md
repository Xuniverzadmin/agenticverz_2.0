# PIN-566: UAT Hardening Reality Closure + Ops Literature Canonicalization

**Status:** ✅ COMPLETE
**Created:** 2026-02-15
**Category:** Architecture / Validation / Documentation

---

## Summary

Closed the remaining broken/error-prone parts from the UC/UAT stream and synchronized ops-domain literature to repo reality.

Hardening outcomes:
- UI hygiene orphan-page detection now recognizes dynamic imports (`import(...)`) and no longer reports false positives for lazily loaded pages.
- Playwright BIT/UAT configs now use deterministic local host+port (`127.0.0.1:5173`) with explicit app-shell `cwd`.
- Unified gate now fails with an actionable preflight error when Playwright Chromium binary is missing, instead of failing later with ambiguous traces.

Documentation outcomes:
- Updated ops software bible and canonical literature to actual filenames and routes.
- Created missing ops docs (`DOMAIN_CAPABILITY.md`, `_summary.md`).
- Updated HOC domain index links for ops documentation.

---

## Design and Fixes

### 1. UI Hygiene False Positives Removed

**File:** `website/app-shell/scripts/ui-hygiene-check.cjs`

- Root cause: orphan-page check considered static imports only.
- Fix: include dynamic import patterns in page reference discovery.
- Result: lazy-loaded route pages are correctly treated as referenced.

### 2. Playwright Determinism Tightened

**Files:**
- `website/app-shell/tests/bit/playwright.config.ts`
- `website/app-shell/tests/uat/playwright.config.ts`

- Standardized base URL to `http://127.0.0.1:5173`.
- Standardized webServer command to `npm run dev -- --host 127.0.0.1 --port 5173`.
- Added explicit `cwd` to app-shell root to remove path ambiguity.

### 3. Gate Preflight for Browser Binary

**File:** `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`

- Added preflight verification of Playwright Chromium headless shell binary path using:
  - `npx playwright install --dry-run chromium`
- Gate now prints a deterministic remediation message:
  - `cd website/app-shell && npx playwright install chromium`
- Limitation captured: install requires outbound DNS/network access.

---

## Reality Notes

- In this sandbox, browser install can fail with network/DNS restrictions; this is environmental and not a code regression.
- UAT-specific typecheck remains the blocking contract; global TypeScript debt remains tracked separately.

---

## Files Updated in This Closure

- `website/app-shell/scripts/ui-hygiene-check.cjs`
- `website/app-shell/tests/bit/playwright.config.ts`
- `website/app-shell/tests/uat/playwright.config.ts`
- `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`
- `literature/hoc_domain/ops/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/ops/OPS_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/ops/DOMAIN_CAPABILITY.md` (new)
- `literature/hoc_domain/ops/_summary.md` (new)
- `literature/hoc_domain/INDEX.md`

---

## Related Artifacts

- `docs/memory-pins/PIN-564-uc-codebase-elicitation-validation-uat-taskpack-full-execution.md`
- `docs/memory-pins/PIN-565-uat-findings-clearance-detour-3-findings-closed-e1-e5.md`
- `backend/app/hoc/docs/architecture/usecases/UC_CODEBASE_ELICITATION_VALIDATION_UAT_SIGNOFF_2026-02-15_v2.md`
- `backend/app/hoc/docs/architecture/usecases/UC_UAT_FINDINGS_CLEARANCE_DETOUR_IMPLEMENTED_2026-02-15.md`
