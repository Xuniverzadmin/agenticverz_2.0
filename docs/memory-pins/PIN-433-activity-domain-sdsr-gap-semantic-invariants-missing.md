## Problem Discovered

SDSR scenarios for ACTIVITY domain panels were auto-generated with **generic invariants** that only verify:
1. Response is dict and not empty
2. Status code == 200
3. Auth works (not 401/403)

They do NOT verify that the endpoint **answers the panel's question**.

## Evidence

All 10 ACTIVITY scenarios have this pattern:

```yaml
invariants:
- id: INV-001
  name: response_shape
  assertion: response is dict and response is not empty  # GENERIC
- id: INV-002
  name: status_code
  assertion: status_code == 200                          # GENERIC
- id: INV-003
  name: auth_works
  assertion: status_code != 401 and status_code != 403   # GENERIC

# HUMAN MAY OPTIONALLY:
#   - Add domain-specific invariants
#   - Tighten response expectations
#   - Add custom checks
```

## Affected Panels

| Panel | Purpose | Endpoint | Missing Invariant |
|-------|---------|----------|-------------------|
| ACT-LLM-LIVE-O3 | Near-threshold runs | /api/v1/activity/runs | `has near_threshold_count` |
| ACT-LLM-LIVE-O4 | Telemetry status | /api/v1/workers/.../runs | `has telemetry_status` |
| ACT-LLM-LIVE-O5 | Run distribution | /health | `has distribution_by_provider` |
| ACT-LLM-COMP-O2 | Success count | /api/v1/activity/summary | `has successful_count` |
| ACT-LLM-COMP-O4 | Near-limit completed | /api/v1/cus/activity | `has near_limit_count` |
| ACT-LLM-COMP-O5 | Aborted runs | /api/v1/runtime/traces | `has aborted_count` |
| ACT-LLM-SIG-O2 | Threshold proximity | /api/v1/predictions | `has threshold_proximity` |
| ACT-LLM-SIG-O3 | Temporal patterns | /api/v1/predictions/.../summary | `has temporal_patterns` |
| ACT-LLM-SIG-O4 | Cost deviations | /api/v1/discovery | `has cost_deviations` |
| ACT-LLM-SIG-O5 | Attention priority | /api/v1/discovery/stats | `has attention_priority` |

## Root Cause

`aurora_sdsr_synth.py` generates scenarios from capability registry with generic invariants. It cannot infer semantic requirements from panel purpose in Intent Ledger.

## Resolution Required

1. **Add semantic invariants** to each SDSR scenario that check response contains fields needed by panel
2. **Re-run SDSR** — scenarios will FAIL correctly revealing backend gaps
3. **Fix backend** — add missing fields/endpoints to answer panel questions
4. **Re-run SDSR** — scenarios pass with semantic verification

## Key Insight

> SDSR passing with generic invariants means "endpoint exists"
> SDSR passing with semantic invariants means "endpoint answers the question"

The pipeline currently proves existence, not correctness.

## Files Affected

- `backend/scripts/sdsr/scenarios/SDSR-ACT-LLM-*.yaml` — need semantic invariants
- `design/l2_1/INTENT_LEDGER.md` — panels updated to DRAFT (done)
- `backend/AURORA_L2_CAPABILITY_REGISTRY/` — capabilities mapped (done)

## Next Steps

1. Human decision: Define what fields each panel needs in response
2. Add invariants to scenarios checking those fields
3. Run SDSR — expect failures
4. Backend work to surface correct data
5. Re-run SDSR — expect passes
