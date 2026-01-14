# PIN-420: Intent Ledger Pipeline and First SDSR Binding

**Status:** 📋 ACTIVE
**Created:** 2026-01-14
**Category:** Architecture / UI Pipeline
**Milestone:** PIN-419

---

## Summary

Documents the updated UI pipeline with separate UI intent ledger and capability intent, and records the first successful SDSR verification binding for OVR-SUM-HL-O1.

---

## Details

## Context

PIN-419 established the Intent Ledger architecture. This PIN documents the operational pipeline that emerged from first binding execution.

## Pipeline Architecture (Updated)

```
┌─────────────────────────────────────────────────────────────┐
│  UI_TOPOLOGY_TEMPLATE.yaml (FROZEN)                         │
│  - Structural law                                           │
│  - Domains → Subdomains → Topics → Slots                    │
│  - 107 total panel slots                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓ constrains
┌─────────────────────────────────────────────────────────────┐
│  INTENT_LEDGER.md (Human Authority)                         │
│  - ## Panels: What UI needs (107 panels)                    │
│  - ## Capabilities: Verified bindings (populated by SDSR)   │
│  - Panel state: EMPTY → DRAFT → BOUND                       │
└─────────────────────────────────────────────────────────────┘
                            ↓ derives
┌─────────────────────────────────────────────────────────────┐
│  CAPABILITY INTENT (ASSUMED)                                │
│  backend/AURORA_L2_CAPABILITY_REGISTRY/*.yaml               │
│  - Retrofitted from panel intent                            │
│  - Status: ASSUMED (not DECLARED)                           │
│  - "We assume backend exhibits this behavior"               │
└─────────────────────────────────────────────────────────────┘
                            ↓ verifies
┌─────────────────────────────────────────────────────────────┐
│  SDSR VERIFICATION                                          │
│  backend/scripts/sdsr/scenarios/*.yaml                      │
│  - Tests if assumption is true                              │
│  - Checks: endpoint exists, schema matches, data real       │
└─────────────────────────────────────────────────────────────┘
                            ↓ on_pass
┌─────────────────────────────────────────────────────────────┐
│  BINDING                                                    │
│  - Capability: ASSUMED → OBSERVED                           │
│  - Panel: EMPTY → BOUND                                     │
│  - Capability ledger updated                                │
└─────────────────────────────────────────────────────────────┘
```

## Key Principle

**UI intent is truth. Capability is derived. SDSR verifies.**

- Panel ledger defines WHAT is needed (human authority)
- Capability is retrofitted to fit (assumption)
- SDSR verifies backend exhibits assumed behavior
- Only after SDSR pass does capability become OBSERVED

## Ledger Structure

### Panel Entry (UI Intent)
```markdown
### Panel: OVR-SUM-HL-O1

Location:
- Domain: OVERVIEW
- Subdomain: SUMMARY
- Topic: HIGHLIGHTS
- Slot: 1

Class: interpretation
State: BOUND

Purpose:
Provide a single, glanceable snapshot of current system activity...

What it shows:
- Count of currently running LLM executions
- Count of executions completed in the last window
- Count of executions in near-threshold or risk state
- Timestamp of last successful observation update

Capability: overview.activity_snapshot
```

### Capability Entry (After SDSR)
```markdown
### Capability: overview.activity_snapshot

Panel: OVR-SUM-HL-O1
Status: OBSERVED
Verified: 2026-01-14

Implementation:
- Endpoint: /api/v1/activity/summary
- Method: GET

Data Mapping:
- count_running → runs.by_status.running
- count_completed_window → runs.by_status.completed
- count_near_threshold → attention.at_risk_count
- last_observed_at → provenance.generated_at

Scenario: observe_overview_activity_snapshot
```

## First SDSR Binding: OVR-SUM-HL-O1

### Summary
| Attribute | Value |
|-----------|-------|
| Panel | OVR-SUM-HL-O1 |
| Domain | OVERVIEW → SUMMARY → HIGHLIGHTS |
| Capability | overview.activity_snapshot |
| Endpoint | /api/v1/activity/summary |
| Status | OBSERVED |

### SDSR Verification Results
| Check | Result |
|-------|--------|
| Endpoint exists | PASS |
| Schema matches | PASS |
| Auth works | PASS |
| Data is real | PASS |
| Coherency Gate | PASS |

### Issues Encountered
1. **Semantic drift** - Initial capability name didn't match intent
2. **Ledger structure** - Capability section vs panel field confusion
3. **State mismatch** - DECLARED requires DRAFT, not UNBOUND
4. **Authority inversion** - Was declaring before deriving
5. **Endpoint path wrong** - Assumed path didn't exist
6. **Scenario name mismatch** - Reference didn't match filename
7. **Onboarding gate** - 403 on first auth attempt

### Resolution
- Capability derived FROM panel intent (not invented)
- SDSR discovered actual endpoint path
- All coherency checks pass

## Artifacts

| Artifact | Path |
|----------|------|
| UI Topology | design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml |
| Intent Ledger | design/l2_1/INTENT_LEDGER.md |
| Generated Plan | design/l2_1/ui_plan.yaml |
| Capability Registry | backend/AURORA_L2_CAPABILITY_REGISTRY/ |
| SDSR Scenarios | backend/scripts/sdsr/scenarios/ |
| Sync Script | scripts/tools/sync_from_intent_ledger.py |
| Coherency Gate | scripts/tools/coherency_gate.py |

## Current State

- Panels: 107 total (1 BOUND, 106 EMPTY)
- Capabilities: 1 OBSERVED
- Coherency: PASS (strict)

## Next Steps

1. Continue Phase A bindings (interpretation-only panels)
2. Each binding follows: UI Intent → Capability Assumption → SDSR Verify → Bind
3. Do not skip SDSR verification

---

## Related PINs

- [PIN-419](PIN-419-.md)
