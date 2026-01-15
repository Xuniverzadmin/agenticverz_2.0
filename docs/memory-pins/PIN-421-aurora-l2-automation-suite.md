# PIN-421: AURORA L2 Automation Suite

**Status:** COMPLETE
**Created:** 2026-01-15
**Category:** UI Pipeline / Automation
**Milestone:** AURORA L2
**Related PINs:** PIN-370, PIN-379, PIN-417, PIN-420

---

## Summary

Complete automation suite for the AURORA L2 pipeline, implementing machine-owned
state transitions while preserving human authority over intent and approval.

**Core Principle:**
> "Humans declare intent and approve gates. Machines generate, discover, verify, apply, and block."

---

## Problem Statement

The AURORA L2 pipeline required manual steps at each phase, creating opportunities for:
- Human error in capability status transitions
- Inconsistency between UI plan, intent, capability, and backend
- Silent drift that breaks compilation or runtime
- No enforcement of ownership boundaries

---

## Solution: Automation Suite

### Scripts Implemented (8 total)

| Script | Phase | Purpose |
|--------|-------|---------|
| `aurora_coherency_check.py` | 3.5 | **Coherency Gate** - validates consistency chain |
| `aurora_intent_scaffold.py` | 2 | Scaffolds intent YAML from ui_plan |
| `aurora_intent_registry_sync.py` | 2 | Syncs intents to registry, handles approvals |
| `aurora_capability_scaffold.py` | 3 | Scaffolds capability YAML (DECLARED status) |
| `aurora_sdsr_synth.py` | 4 | Generates SDSR scenario from intent |
| `aurora_sdsr_runner.py` | 4 | Executes SDSR with coherency pre-check |
| `aurora_apply_observation.py` | 5 | Applies observation (DECLARED→OBSERVED) |
| `aurora_bind.py` | All | **Orchestrator** - single command for full pipeline |

### CI Workflow

| File | Purpose |
|------|---------|
| `aurora-ownership-guard.yml` | Blocks manual edits to machine-owned artifacts |

---

## Phase 3.5: Coherency Gate (Critical Addition)

The coherency gate validates **wiring truth** before SDSR validates **behavior truth**.

### Coherency Invariants

| ID | Invariant | Category |
|----|-----------|----------|
| COH-001 | ui_plan.panel_id == intent.panel_id | Identity |
| COH-002 | intent_spec path exists | Identity |
| COH-003 | intent.capability.id == capability.capability_id | Wiring |
| COH-004 | intent.endpoint == capability.endpoint | Wiring |
| COH-005 | intent.method == capability.method | Wiring |
| COH-006 | intent.domain == capability.domain | Wiring |
| COH-007 | capability.status in valid FSM | State |
| COH-008 | sdsr.verified → status >= OBSERVED | State |
| COH-009 | capability.endpoint exists in backend | Reality |
| COH-010 | capability.method matches route | Reality |

### Why Coherency Gate is Mandatory

Without it:
- SDSR could "pass" against wrong endpoint
- Intent could reference non-existent capability
- Status could be inconsistent with verification state
- System breaks at compilation or runtime

With it:
- Wiring validated before behavior
- SDSR only runs against verified wiring
- State transitions are provably correct

---

## Ownership Matrix

| Artifact | Owner | Enforcement |
|----------|-------|-------------|
| `ui_plan.yaml` | **Human** | Product authority |
| Intent display/notes | **Human** | Semantic content |
| Intent registry `APPROVED` | **Human** | Explicit approval |
| Capability `status` | **Machine** | CI blocks manual edits |
| SDSR observations | **Machine** | Runner output only |
| Projection lock | **Machine** | Compiler output only |
| Intent `sdsr.verified` | **Machine** | Observation applier only |

---

## Usage

### Single Command Bind

```bash
# Start binding a new panel
python aurora_bind.py OVR-SUM-HL-O2

# After human approval, continue
python aurora_bind.py OVR-SUM-HL-O2 --continue

# Check status anytime
python aurora_bind.py OVR-SUM-HL-O1 --status
```

### Individual Tools

```bash
# Scaffold intent
python aurora_intent_scaffold.py --panel OVR-SUM-HL-O2

# Approve intent
python aurora_intent_registry_sync.py --approve OVR-SUM-HL-O2

# Run coherency check
python aurora_coherency_check.py --panel OVR-SUM-HL-O1

# Generate SDSR scenario
python aurora_sdsr_synth.py --panel OVR-SUM-HL-O2

# Execute SDSR
python aurora_sdsr_runner.py --panel OVR-SUM-HL-O2

# Apply observation
python aurora_apply_observation.py --capability overview.activity_snapshot
```

---

## Pipeline Flow with Automation

```
PHASE 1: Human Intent Declaration
    └─ ui_plan.yaml (HUMAN AUTHORITY - no automation)

PHASE 2: Intent Specification
    ├─ aurora_intent_scaffold.py     → Creates intent YAML
    ├─ aurora_intent_registry_sync.py → Registers as DRAFT
    └─ [HUMAN] Reviews and approves   → DRAFT → APPROVED

PHASE 3: Capability Declaration
    └─ aurora_capability_scaffold.py  → Creates capability (DECLARED)

PHASE 3.5: Coherency Gate ◄─── NEW
    └─ aurora_coherency_check.py      → Validates COH-001 to COH-010
                                      → BLOCKS if any fail

PHASE 4: SDSR Verification
    ├─ aurora_sdsr_synth.py          → Generates scenario
    └─ aurora_sdsr_runner.py         → Executes, emits observation

PHASE 5: Observation Application
    └─ aurora_apply_observation.py   → DECLARED → OBSERVED

PHASE 6: Compilation
    └─ SDSR_UI_AURORA_compiler.py    → Generates projection

PHASE 7: PDG
    └─ projection_diff_guard.py      → Auto-allowlist safe transitions

PHASE 8: Frontend
    └─ Reads projection verbatim
```

---

## Key Decisions

### 1. DECLARED Status is Useful

Capability can exist in DECLARED status as a "work in progress" signal.
The transition DECLARED → OBSERVED is machine-only via SDSR.

### 2. Coherency Gate Before SDSR

Wiring must be validated before behavior.
SDSR should not "discover" endpoints - it should verify them.

### 3. Backend Route Introspection

COH-009/010 introspect FastAPI routes to verify endpoint existence.
Routes are cached in `.routes_cache.json` for performance.

### 4. Human Approval is Explicit

DRAFT → APPROVED requires explicit `--approve` command.
Automation cannot auto-approve intents.

---

## Files Created

```
backend/aurora_l2/tools/
├── aurora_coherency_check.py      # Phase 3.5 gate
├── aurora_intent_scaffold.py      # Phase 2 automation
├── aurora_intent_registry_sync.py # Phase 2 automation
├── aurora_capability_scaffold.py  # Phase 3 automation
├── aurora_sdsr_synth.py           # Phase 4 scenario generation
├── aurora_sdsr_runner.py          # Phase 4 execution
├── aurora_apply_observation.py    # Phase 5 automation
├── aurora_bind.py                 # Orchestrator
└── .routes_cache.json             # Backend routes cache

.github/workflows/
└── aurora-ownership-guard.yml     # CI ownership enforcement
```

---

## Validation

```bash
# Test coherency on existing panel
$ python aurora_coherency_check.py --panel OVR-SUM-HL-O1

COHERENCY CHECK: OVR-SUM-HL-O1
======================================================================
  COH-001  ✅ PASS  Panel exists in ui_plan.yaml
  COH-002  ✅ PASS  Intent YAML exists
  COH-003  ✅ PASS  Capability ID matches
  COH-004  ⚠️ WARN  Intent declares endpoint but capability does not
  COH-005  ⏭️ SKIP  Method not declared in both
  COH-006  ⏭️ SKIP  Domain not declared in capability
  COH-007  ✅ PASS  Capability status valid: OBSERVED
  COH-008  ✅ PASS  SDSR verification status consistent
  COH-009  ✅ PASS  Backend route exists
  COH-010  ✅ PASS  Route method matches

✅ COHERENCY GATE PASSED
```

---

## Lessons Locked

1. **Coherency gate is structurally mandatory** - not a nice-to-have
2. **Wiring truth precedes behavior truth** - validate before verify
3. **DECLARED is a valid tracking state** - not just a temporary placeholder
4. **Machine ownership must be enforced by CI** - not just by convention
5. **Single orchestrator command** - aurora_bind.py reduces error surface

---

## Phase 5.5: Hardening (IMPLEMENTED)

### Trust Evaluator (OBSERVED → TRUSTED)

Implemented in `aurora_trust_evaluator.py`:

```bash
# Evaluate eligibility
python aurora_trust_evaluator.py --capability overview.activity_snapshot

# Promote if eligible
python aurora_trust_evaluator.py --capability overview.activity_snapshot --promote
```

**Trust Policy:**
| Parameter | Default | Purpose |
|-----------|---------|---------|
| min_runs | 10 | Minimum SDSR runs required |
| min_pass_rate | 0.98 | 98% pass rate over window |
| max_consecutive_failures | 1 | Max failures in a row |
| time_window_days | 7 | Observation window |
| invariant_stability_required | true | Same invariants passing |

### SDSR Failure Taxonomy

Formal failure classification in observations:

| Class | Meaning | Trust Impact |
|-------|---------|--------------|
| COHERENCY_VIOLATION | COH-001 to COH-008 failed | Blocks SDSR |
| REALITY_MISMATCH | COH-009/010 failed (endpoint missing) | Hard failure |
| INVARIANT_VIOLATED | SDSR invariants failed | Counts against trust |
| SEMANTIC_REGRESSION | Previously passing now fails | High severity |
| TRANSIENT_FAILURE | Network/service issues | May retry |
| AUTH_FAILURE | 401/403 errors | Credential issue |

### Intent Hash Freezing

Hash is frozen at APPROVED time to detect post-approval modifications:

```bash
# Verify all intent hashes (staleness check)
python aurora_intent_registry_sync.py --verify

# List shows frozen hash status
python aurora_intent_registry_sync.py --list
```

**Output:**
```
AURORA L2 Intent Staleness Check
======================================================================
  ✅ OK: OVR-SUM-HL-O1
  ⚠️  STALE: OVR-SUM-HL-O2
       Frozen:  abc123...
       Current: def456...
```

### PDG Audit Logging

Provenance logging for every PDG run:

```bash
# Run with audit logging
python projection_diff_guard.py --old old.json --new new.json --audit
```

Logs stored in `backend/scripts/sdsr/pdg_audit/PDG_AUDIT_*.json`

---

## Future Enhancements

1. **Capability YAML endpoint/method sync** - Auto-fill from intent when scaffolding
2. **Batch binding** - `aurora_bind.py --all` for multiple panels
3. **TRUSTED demotion** - Auto-demote on regression
4. **Cross-intent coherency** - Detect conflicting intents

---

## References

- `backend/aurora_l2/tools/` - All automation scripts
- `docs/governance/SDSR_SYSTEM_CONTRACT.md` - SDSR contract
- `docs/contracts/UI_AS_CONSTRAINT_V1.md` - UI authority model
- PIN-370 - SDSR System Contract
- PIN-379 - E2E Pipeline
- PIN-417 - HIL v1 Implementation
- PIN-420 - Intent Ledger Pipeline
