# Quarantine Directory

**Created:** 2026-01-06
**Phase:** Phase 1.1 - Legacy Resolution & Structural Hardening
**Reference:** PIN-317

---

## Purpose

This directory contains frontend artifacts that have been quarantined during Phase 1.1.

Quarantined items are NOT deleted because they may have:
- Historical significance
- Future intent
- Architectural value that hasn't been connected yet

---

## Quarantined Items

### SupportPage.tsx

**Original Location:** `products/ai-console/account/SupportPage.tsx`
**Quarantine Date:** 2026-01-06
**Reason:** Imported in AIConsoleApp but no route defined for `/support`

**Evidence:**
- Component is complete and functional
- Import exists in AIConsoleApp.tsx (removed during quarantine)
- No route in `routes/index.tsx`
- DOMAIN_MAPPING_ANALYSIS.md mentions it but route was never added

**Recovery Path:**
1. Add route in `routes/index.tsx`: `<Route path="guard/support" element={<SupportPage />} />`
2. Move file back to `products/ai-console/account/`
3. Restore import in AIConsoleApp.tsx

---

## Rules

- Files here must NOT be imported anywhere
- Files here must NOT be deleted without explicit approval
- Each file must have documentation in this file
- Recovery requires explicit human approval
