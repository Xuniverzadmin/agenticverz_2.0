# PIN-334: CRM Unquarantine & Unified Founder Review Page

**Created:** 2026-01-06
**Status:** COMPLETE
**Category:** Founder Console / Feature Integration
**Related:** PIN-293 (CRM Contract Review), PIN-317 (Phase 1.1 Legacy Resolution), PIN-333 (AUTO_EXECUTE Review)

---

## Summary

Restored quarantined CRM contract review files (PIN-293) and merged with AUTO_EXECUTE review dashboard (PIN-333) into a unified tabbed Founder Review page at `/fops/review`.

---

## Background

During Phase 1.1 Legacy Resolution (PIN-317), founder review files were quarantined because:
- No frontend page was calling the API endpoints
- Files were moved to `app/quarantine/` to prevent accidental imports
- Documentation was preserved in `QUARANTINE.md`

The user requested these files be restored and merged with the PIN-333 AUTO_EXECUTE review to create a single unified review interface.

---

## What Was Quarantined

### Original Files (PIN-317 Quarantine)

| File | Original Location | Reason |
|------|-------------------|--------|
| `founder_review.py` | `app/api/founder_review.py` | No frontend caller |
| `founder_review_adapter.py` | `app/adapters/founder_review_adapter.py` | No frontend caller |

### Functionality

The quarantined CRM workflow provided:
- `GET /fdr/contracts/review-queue` - List contracts pending review
- `GET /fdr/contracts/{contract_id}` - Contract detail view
- `POST /fdr/contracts/{contract_id}/review` - Approve/reject contracts

---

## Restoration Actions

### 1. File Renames (Conflict Avoidance)

Original `founder_review.py` name was already used by PIN-333 for AUTO_EXECUTE review. Files were renamed:

| Quarantined | Restored As |
|-------------|-------------|
| `founder_review.py` | `app/api/founder_contract_review.py` |
| `founder_review_adapter.py` | `app/adapters/founder_contract_review_adapter.py` |

### 2. Backend Restoration

**`app/api/founder_contract_review.py`**
- Copied from quarantine with renamed imports
- Added FOPS token authentication (`verify_fops_token`)
- Router prefix: `/fdr/contracts`

**`app/adapters/founder_contract_review_adapter.py`**
- Copied from quarantine
- L3 adapter translating Contract domain → Founder views
- DTOs: `FounderContractSummaryView`, `FounderContractDetailView`, `FounderReviewResult`

**`app/adapters/__init__.py`**
- Restored import for `founder_contract_review_adapter`
- Added exports to `__all__`

**`app/main.py`**
- Registered `founder_contract_review_router`
- Routes active at `/fdr/contracts/*`

### 3. Frontend Creation

**`website/app-shell/src/api/contractReview.ts`**
- TypeScript API client for contract review
- Types: `ContractSummary`, `ContractDetail`, `ReviewQueueResponse`, `ReviewResult`
- Functions: `getReviewQueue()`, `getContractDetail()`, `submitReview()`

**`website/fops/src/pages/fdr/ContractReviewContent.tsx`**
- Contract review tab content
- Components: `QueueStats`, `ContractTable`, `ContractDrawer`
- Full approve/reject workflow with notes

**`website/fops/src/pages/fdr/AutoExecuteReviewContent.tsx`**
- Extracted from `AutoExecuteReviewPage.tsx`
- Evidence-only content for AUTO_EXECUTE tab (read-only)

**`website/fops/src/pages/fdr/FounderReviewPage.tsx`**
- Unified tabbed dashboard
- Tabs: "AUTO_EXECUTE Decisions" | "Contract Review"
- Lazy loads appropriate content component

### 4. Route Registration

**`website/app-shell/src/routes/index.tsx`**
```typescript
// Unified Founder Review Dashboard (AUTO_EXECUTE + Contract Review)
const FounderReviewPage = lazy(() => import('@fops/pages/fdr/FounderReviewPage'));

<Route path="fops/review" element={<FounderRoute><FounderReviewPage /></FounderRoute>} />
```

---

## Verification

All imports verified working:
```
✅ Contract model imports: OK
✅ Contract service imports: OK
✅ Contract review adapter imports: OK
✅ Adapter exports via __init__.py: OK
✅ API router imports: OK
✅ FOPS auth imports: OK
```

---

## Routes Summary

### Unified Review Page
- **URL:** `/fops/review`
- **Auth:** FOPS token (founder-only)
- **Tabs:** AUTO_EXECUTE | Contracts

### Contract Review API
- `GET /fdr/contracts/review-queue` - Queue of pending contracts
- `GET /fdr/contracts/{contract_id}` - Contract details
- `POST /fdr/contracts/{contract_id}/review` - Submit decision

### AUTO_EXECUTE Review API (PIN-333)
- `GET /fdr/review/auto-execute/queue` - Pending decisions
- `GET /fdr/review/auto-execute/{decision_id}` - Decision evidence

---

## Files Modified/Created

### Created
- `backend/app/api/founder_contract_review.py`
- `backend/app/adapters/founder_contract_review_adapter.py`
- `website/app-shell/src/api/contractReview.ts`
- `website/fops/src/pages/fdr/FounderReviewPage.tsx`
- `website/fops/src/pages/fdr/ContractReviewContent.tsx`
- `website/fops/src/pages/fdr/AutoExecuteReviewContent.tsx`

### Modified
- `backend/app/adapters/__init__.py` - Added adapter import
- `backend/app/main.py` - Registered router
- `website/app-shell/src/routes/index.tsx` - Added route
- `backend/app/quarantine/QUARANTINE.md` - Documented restoration

---

## Architecture Notes

### Layer Compliance
- L2 (API): `founder_contract_review.py` - Request handlers
- L3 (Adapter): `founder_contract_review_adapter.py` - Thin translation
- L4 (Service): Existing contract services (unchanged)

### Auth Pattern
- All endpoints require FOPS token
- Uses `verify_fops_token` from `app.auth.console_auth`
- Founder-only access enforced

### Separation of Concerns
- AUTO_EXECUTE tab: **Read-only evidence** (no mutations)
- Contract Review tab: **Full workflow** (approve/reject with mutations)
- Clear visual distinction in UI

---

## Quarantine Update

`QUARANTINE.md` updated to show:
- All items restored
- None currently quarantined
- Full restoration history documented
