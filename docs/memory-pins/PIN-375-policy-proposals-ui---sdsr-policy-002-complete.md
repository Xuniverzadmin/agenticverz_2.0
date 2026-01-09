# PIN-375: Policy Proposals UI - SDSR-POLICY-002 Complete

**Status:** ✅ COMPLETE
**Created:** 2026-01-09
**Category:** SDSR / Policy Domain

---

## Summary

Policy Proposals subdomain implemented via proper L2.1 pipeline. Proposals visible in UI with approve/reject controls. Backend creates proposals from incidents.

---

## Details

## Problem

Need to display policy proposals in the Customer Console with human approve/reject controls. Previous attempt violated UI pipeline architecture.

## Solution

### Proper Implementation Flow

1. **Added intent rows to CSV** (source of truth):
   ```csv
   Policies,PROPOSALS,PENDING_PROPOSALS,...,POL-PR-PP-O1,Pending Proposals Summary,...
   Policies,PROPOSALS,PENDING_PROPOSALS,...,POL-PR-PP-O2,Pending Proposals List,...
   ```

2. **Ran L2.1 pipeline**:
   - l2_pipeline.py generate v4
   - l2_raw_intent_parser.py
   - intent_normalizer.py
   - surface_to_slot_resolver.py
   - intent_compiler.py
   - ui_projection_builder.py

3. **Copied projection to frontend**:
   ```bash
   cp design/l2_1/ui_contract/ui_projection_lock.json website/app-shell/public/projection/
   ```

4. **Added renderers to PanelContentRegistry** (LAST step):
   - POL-PR-PP-O1: PendingProposalsSummary
   - POL-PR-PP-O2: ProposalsList with approve/reject mutations

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/policy-proposals | GET | List proposals |
| /api/v1/policy-proposals/{id} | GET | Proposal detail |
| /api/v1/policy-proposals/{id}/approve | POST | Approve (human action) |
| /api/v1/policy-proposals/{id}/reject | POST | Reject (human action) |

### Data Flow (SDSR)

```
Failed Run → Incident Engine → Incident Created
                    ↓
           Policy Engine → Proposal Created (status: draft)
                    ↓
           Console UI → Human sees proposal
                    ↓
           Human Action → Approve/Reject
                    ↓
           Policy Rule Created (if approved)
```

### Database State (Verified)

- policy_proposals table has draft/approved/rejected entries
- Proposals linked to triggering incidents via triggering_feedback_ids
- PB-S4 contract: human approval mandatory, no auto-enforce

## Key Files

| File | Role |
|------|------|
| backend/app/api/policy_proposals.py | API endpoints |
| backend/app/services/policy_proposal.py | Business logic |
| website/app-shell/src/api/proposals.ts | Frontend API client |
| website/app-shell/src/components/panels/PanelContentRegistry.tsx | UI renderers |

## Reference

- PIN-373 (Policy Lifecycle Completion)
- PIN-374 (UI Pipeline Mastery)
- SDSR-POLICY-002 scenario

---

## Related PINs

- [PIN-373](PIN-373-.md)
- [PIN-374](PIN-374-.md)
