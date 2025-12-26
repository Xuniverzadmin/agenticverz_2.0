# PIN-161: P2FC — Partial to Full Consume

**Status:** COMPLETE (M7 deferred to M28)
**Created:** 2025-12-24
**Category:** Architecture / Milestone Promotion
**Milestone:** Post-M32 Consolidation
**Parent:** [PIN-160](PIN-160-m0-m27-utilization-audit-disposition.md)
**Codename:** P2FC

---

## Summary

**P2FC (Partial to Full Consume)** — Execution plan for promoting 5 partial milestones to fully consumed status. Each milestone requires: pillar binding, production flow integration, and removal invariant.

### P2FC Definition

A milestone transitions from PARTIAL → FULLY CONSUMED when:
1. **Pillar Owner** — At least one pillar explicitly claims it
2. **Production Flow** — Participates in at least one live flow
3. **Removal Invariant** — Removing it breaks a visible system property

---

## Execution Order (Priority Sorted)

| Order | Milestone | Effort | Pillar | Blocking |
|-------|-----------|--------|--------|----------|
| 1 | M8 SDK | 1 day | Infra | None |
| 2 | M16 SBA UI | 2 days | Governance | None |
| 3 | M4 Golden Replay | 3 days | Incident | None |
| 4 | M6 Scoped Execution | 2 days | Incident + Cost | M4 (shares UI) |
| 5 | M7 RBAC | M28 scope | Infra | M28 milestone |

**Total immediate effort: 8 days (M7 deferred to M28)**

---

## 1. M8 SDK — Day-0 Entry Point

### Current State (Audited 2025-12-24)

#### Python SDK (`sdk/python/`)
| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Package | `aos_sdk/__init__.py` | 69 | Exports: AOSClient, RuntimeContext, Trace |
| Client | `aos_sdk/client.py` | 398 | Full API: simulate, query, skills, capabilities, agents |
| CLI | `aos_sdk/cli.py` | 362 | Commands: version, health, capabilities, skills, simulate, replay, diff |
| Runtime | `aos_sdk/runtime.py` | 131 | Determinism: seed, freeze_time, canonical_json |
| Trace | `aos_sdk/trace.py` | 598 | Replay: Trace, TraceStep, diff_traces, idempotency |
| **Total** | | **1,558** | |

**Package:** `aos-sdk` v0.1.0 (built: `dist/aos_sdk-0.1.0-py3-none-any.whl`)

#### JS/TS SDK (`sdk/js/aos-sdk/`)
| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Entry | `src/index.ts` | 90 | Full re-exports |
| Client | `src/client.ts` | 370 | Same API surface as Python |
| Runtime | `src/runtime.ts` | 259 | Determinism parity with Python |
| Trace | `src/trace.ts` | 616 | Hash parity verified (PIN-125) |
| Types | `src/types.ts` | 214 | Full TypeScript definitions |
| **Total** | | **1,549** | |

**Package:** `@agenticverz/aos-sdk` v0.1.0 (Node 18+)

#### CLI Commands Available
```
aos version              # Show version
aos health               # Check server health
aos capabilities         # Show runtime capabilities
aos skills               # List available skills
aos skill <id>           # Describe a skill
aos simulate <json>      # Simulate plan (--seed, --save-trace, --dry-run)
aos replay <trace>       # Replay saved trace
aos diff <t1> <t2>       # Compare two traces
```

#### API Surface (Both SDKs)
| Category | Methods |
|----------|---------|
| **Machine-Native** | `simulate()`, `query()`, `listSkills()`, `describeSkill()`, `getCapabilities()` |
| **Agent Workflow** | `createAgent()`, `postGoal()`, `pollRun()`, `recall()` |
| **Run Management** | `createRun()`, `getRun()` |
| **Determinism** | `RuntimeContext`, `Trace`, `diffTraces()`, `replayStep()` |

### What's Missing (Gap Analysis)

| Gap | Description | Impact |
|-----|-------------|--------|
| No `aos init` command | CLI lacks project initialization | Onboarding friction |
| No install verification | Cannot confirm SDK correctly installed | Support overhead |
| Not in onboarding flow | Guard Console doesn't reference SDK | Users miss entry point |
| No pillar connection | README doesn't mention Cost/Incident/Governance pillars | Value prop unclear |

### Target State
- SDK is THE first step in customer journey
- `aos init --api-key=xxx` creates config file
- Guard Console shows "Get Started with SDK"
- README explains pillar value props

### Tasks

| Task | File/Location | Action |
|------|---------------|--------|
| 1.1 | `sdk/python/aos_sdk/cli.py` | Add `aos init` command |
| 1.2 | Guard Console | Add "Get Started" → SDK install instructions |
| 1.3 | `sdk/python/README.md` | Add pillar value props section |
| 1.4 | `sdk/js/aos-sdk/README.md` | Mirror Python README updates |

### Invariant
```
"Customer onboarding cannot complete without SDK install verification"
```

### Promotion Test
```python
def test_sdk_is_primary_entry():
    """M8: SDK must be first onboarding step."""
    onboarding_flow = get_onboarding_steps()
    assert onboarding_flow[0].type == "SDK_INSTALL"
```

---

## 2. M16 SBA UI — Strategy Health Widget

### Current State
- Backend: SBA generator, validator, schema (M15) ✅
- Frontend: `/pages/sba/`, `api/sba.ts`, `types/sba.ts` exist
- UI not surfaced in Guard Console

### Target State
- Strategy Health widget visible in Guard Console
- Shows per-agent SBA bounds and current usage
- Visual indicator: WITHIN_BOUNDS / APPROACHING / EXCEEDED

### Tasks

| Task | File/Location | Action |
|------|---------------|--------|
| 2.1 | `console/src/components/StrategyHealthWidget.tsx` | Create widget component |
| 2.2 | `console/src/pages/guard/index.tsx` | Embed widget in Guard Console |
| 2.3 | `backend/app/api/sba.py` | Add `/api/v1/sba/health` endpoint |
| 2.4 | `console/src/api/sba.ts` | Add `getStrategyHealth()` API call |

### Widget Specification

```
┌─────────────────────────────────────────────────────────────┐
│  STRATEGY HEALTH                                            │
│                                                             │
│  Agent: "customer-support-agent"                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Max tokens/call:  4,000  [████████░░]  3,200       │   │
│  │ Max cost/call:    $0.50  [██████░░░░]  $0.31       │   │
│  │ Allowed models:   gpt-4o, gpt-4o-mini  ✓           │   │
│  │ Escalations:      0/3 threshold  ✓                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Status: ✅ WITHIN BOUNDS                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Invariant
```
"Strategy health must be visible to customer in Guard Console"
```

### Promotion Test
```python
def test_sba_health_visible():
    """M16: SBA health widget must be rendered in Guard Console."""
    guard_console = render_guard_console(tenant_id="test")
    assert guard_console.has_component("StrategyHealthWidget")
```

---

## 3. M4 Golden Replay — Incident Evidence

### Current State
- `workflow/golden.py` (18KB) - Golden-run replay
- `workflow/checkpoint.py` (24KB) - State snapshots
- Used by tests only, not product

### Target State
- "Replay Execution" button on Incident detail page
- Shows determinism verification result
- Compares original vs replay: tokens, cost, duration

### Tasks

| Task | File/Location | Action |
|------|---------------|--------|
| 3.1 | `backend/app/api/incidents.py` | Add `/api/v1/incidents/{id}/replay` endpoint |
| 3.2 | `backend/app/services/replay_service.py` | Create service wrapping `golden.py` |
| 3.3 | `console/src/pages/incidents/[id].tsx` | Add "Replay Execution" button |
| 3.4 | `console/src/components/ReplayResultsModal.tsx` | Create results display |

### Replay Results Specification

```
┌─────────────────────────────────────────────────────────────┐
│  REPLAY RESULTS                                             │
│                                                             │
│  Incident: "Cost spike on Dec 24, 10:32 AM"                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Original    Replay      Match       │   │
│  │ Tokens:         847         847         ✓          │   │
│  │ Cost:           $0.42       $0.42       ✓          │   │
│  │ Duration:       3.2s        3.1s        ~          │   │
│  │ Output Hash:    a3f2...     a3f2...     ✓          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Verdict: ✅ DETERMINISTIC                                  │
│                                                             │
│  Root Cause Analysis:                                       │
│  Input document was 50KB (usually 5KB)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Invariant
```
"Incident detail page must offer replay verification option"
```

### Promotion Test
```python
def test_replay_available_on_incident():
    """M4: Replay button must be available on incident detail."""
    incident_page = render_incident_detail(incident_id="test")
    assert incident_page.has_button("Replay Execution")
```

---

## 4. M6 Scoped Execution — Recovery Validation

### Current State
- `costsim/canary.py` (22KB) - Canary logic (orphaned)
- `costsim/circuit_breaker.py` (31KB) - Circuit breaker (used)
- Canary not wired to any flow

### Target State
- Reframe as "Scoped Execution Context"
- Pre-execution gate for MEDIUM+ risk recovery
- Outputs: cost delta, failure delta, policy delta

### Tasks

| Task | File/Location | Action |
|------|---------------|--------|
| 4.1 | `backend/app/services/scoped_execution.py` | Create service from canary.py |
| 4.2 | `backend/app/recovery/engine.py` | Add `@requires_scoped_execution` decorator |
| 4.3 | `backend/app/models/recovery.py` | Add `risk_class` enum (LOW/MEDIUM/HIGH) |
| 4.4 | `backend/app/api/recovery.py` | Add `/api/v1/recovery/{id}/scope-test` endpoint |

### Scoped Execution Interface

```python
class ScopedExecutionContext:
    """M6 Scoped Execution primitive."""

    def __init__(
        self,
        action: RecoveryAction,
        scope: ExecutionScope,  # AGENT_SUBSET | REQUEST_SAMPLE | BUDGET_FRACTION
        timeout_ms: int = 30000
    ):
        ...

    async def execute(self) -> ScopedExecutionResult:
        """Execute action in scoped context."""
        return ScopedExecutionResult(
            cost_delta=...,
            failure_count=...,
            policy_violations=[...],
            execution_hash=...
        )

@requires_scoped_execution(risk_threshold=RiskClass.MEDIUM)
async def execute_recovery(action: RecoveryAction):
    """Recovery actions with MEDIUM+ risk require scoped pre-execution."""
    ...
```

### Invariant
```
"No automated recovery with risk_class >= MEDIUM may execute globally
without a scoped execution result"
```

### Promotion Test
```python
def test_medium_risk_requires_scoped_execution():
    """M6: MEDIUM+ risk recovery must have scoped pre-execution."""
    with pytest.raises(ScopedExecutionRequired):
        execute_recovery(
            action=RecoveryAction(risk_class=RiskClass.MEDIUM),
            skip_scope=True
        )
```

---

## 5. M7 RBAC — Permission Routing (M28 Scope)

### Current State
- Auth module exists
- RBAC partially implemented
- Not all permission checks route through M7

### Target State
- All permission checks use M7 RBAC layer
- Unified permission model
- Part of M28 Unified Console

### Deferred To
**M28 Unified Console** - This is architectural work that spans the console unification effort.

### Invariant
```
"All permission checks must route through M7 RBAC layer"
```

### Promotion Test
```python
def test_all_permissions_use_rbac():
    """M7: All permission checks must use RBAC layer."""
    permission_checks = find_all_permission_checks()
    for check in permission_checks:
        assert check.uses_rbac_layer(), f"{check.location} bypasses RBAC"
```

---

## Execution Timeline

```
Week 1:
├── Day 1: M8 SDK (docs + onboarding) ✓
├── Day 2-3: M16 SBA UI (widget + API)
└── Day 4-5: M4 Replay (service + button)

Week 2:
├── Day 6-7: M4 Replay (modal + polish)
├── Day 8-9: M6 Scoped Execution (service + decorator)
└── Day 10: Integration testing

M28 (future):
└── M7 RBAC completion
```

---

## Success Criteria

All 5 milestones are FULLY CONSUMED when:

| Milestone | Pillar Owner | Production Flow | Removal Invariant | Test |
|-----------|--------------|-----------------|-------------------|------|
| M4 | Incident | Incident detail replay | Replay button exists | ✅ |
| M6 | Incident + Cost | Recovery pre-execution | MEDIUM+ risk gated | ✅ |
| M7 | Infra | All permission checks | RBAC layer used | M28 |
| M8 | Infra | Customer onboarding | SDK first step | ✅ |
| M16 | Governance | Guard Console widget | Health visible | ✅ |

---

## Related PINs

- [PIN-160](PIN-160-m0-m27-utilization-audit-disposition.md) - Parent audit
- [PIN-158](PIN-158-m32-tier-gating-implementation.md) - Tier gating (may interact with SBA)

---

## Commits

### M8 SDK (P2FC-1) - COMPLETE 2025-12-24

- Added `aos init` command to CLI (`sdk/python/aos_sdk/cli.py`)
- Enhanced `aos health` with install verification checklist
- Rewrote README with pillar value props (Python + JS)
- **Exit codes**: `aos health` exits non-zero on ANY failure (CI-friendly)
  - 3/3 checks → exit 0
  - <3 checks → exit 1
- Files changed:
  - `sdk/python/aos_sdk/cli.py` - init command, health verification
  - `sdk/python/README.md` - pillar framing, quick start
  - `sdk/js/aos-sdk/README.md` - pillar framing, determinism docs

### M16 SBA UI (P2FC-2) - COMPLETE 2025-12-24

- Added `GET /api/v1/sba/health` endpoint (aggregated strategy health)
- Created `StrategyHealthWidget.tsx` (read-only, click → SBA Inspector)
- Embedded widget in `GuardDashboard.tsx` below protection status
- Classification: healthy (>= 0.6), approaching (0.3-0.6), exceeded (< 0.3)
- Files changed:
  - `backend/app/api/agents.py` - /sba/health endpoint
  - `website/aos-console/console/src/api/guard.ts` - getStrategyHealth()
  - `website/aos-console/console/src/components/StrategyHealthWidget.tsx` - new
  - `website/aos-console/console/src/pages/guard/GuardDashboard.tsx` - widget embed
- **Verified**: `curl http://localhost:8000/api/v1/sba/health` returns correct structure

### M4 Golden Replay (P2FC-3) - COMPLETE 2025-12-24

- Created `ReplayResultsModal.tsx` (comparison table, verdict display)
- Updated `IncidentsPage.tsx` to call replay API and show modal
- Backend `/guard/replay/{call_id}` already existed (M23)
- Frontend API `guardApi.replayCall()` already existed
- Wiring: Replay button → API call → Modal display
- **Evidence-Grade Enhancement (2025-12-24):**
  - Renamed modal title: "Replay Results" → "Replay Evidence"
  - Added Determinism badge (✓ for exact/logical match)
  - Added Trace ID and Timestamp metadata section
  - Added immutability notice: "This replay is immutable and evidence-grade"
  - Linked to related PINs in component docstring
- Files changed:
  - `website/aos-console/console/src/components/ReplayResultsModal.tsx` - evidence-grade framing
  - `website/aos-console/console/src/pages/guard/incidents/IncidentsPage.tsx` - replay mutation, modal, incidentId prop

#### Memory Pin Mapping (P2FC-3)

| Memory Pin | Description | Status After P2FC-3 |
|------------|-------------|---------------------|
| PIN-125 | Deterministic replay parity | ✅ Required for evidence |
| PIN-127 | Replay determinism invariant | ✅ Enforced |
| PIN-131 | Evidence Pack framing | 🔄 Replay now part of Evidence |
| PIN-148 | Incident → Evidence linkage | ✅ Replay linked |

#### New Invariant (P2FC-3)

> "An incident is incomplete without at least one deterministic replay evidence artifact."

### M6 Scoped Execution (P2FC-4) - COMPLETE 2025-12-24

**Initial Implementation (Pre-Test Script):**
- Created `scoped_execution.py` service with:
  - `ScopedExecutionContext` class for pre-execution testing
  - `RiskClass` enum (LOW/MEDIUM/HIGH/CRITICAL)
  - `ExecutionScope` enum (DRY_RUN/AGENT_SUBSET/REQUEST_SAMPLE/BUDGET_FRACTION)
  - `@requires_scoped_execution` decorator for risk gating
- Added `/api/v1/recovery/candidates/{id}/scope-test` endpoint

**P2FC-4 Enhancement (Post-Test Script, 2025-12-24):**

Implemented full scope-gated execution per test script requirements:

1. **BoundExecutionScope Model:**
   - `scope_id`: Unique identifier
   - `incident_id`: Incident binding (scope is incident-specific)
   - `allowed_actions`: List of permitted actions
   - `max_cost_usd`: Cost ceiling
   - `max_attempts`: Execution limit (default: 1)
   - `expires_at`: Time-bound expiry
   - `intent`: Why this action is allowed
   - `status`: active/exhausted/expired/revoked

2. **Scope Store (Thread-Safe):**
   - In-memory store with incident indexing
   - Automatic expiry tracking
   - Revocation support

3. **New API Endpoints:**
   - `POST /api/v1/recovery/scope` - Create bound scope (Gate Step)
   - `POST /api/v1/recovery/execute` - Execute with scope (FAILS without scope)
   - `GET /api/v1/recovery/scopes/{incident_id}` - List scopes
   - `DELETE /api/v1/recovery/scopes/{scope_id}` - Revoke scope

4. **Exception Hierarchy:**
   - `ScopedExecutionRequired` - No scope provided
   - `ScopeNotFound` - Invalid scope_id
   - `ScopeExhausted` - Attempts consumed
   - `ScopeExpired` - TTL exceeded
   - `ScopeActionMismatch` - Action not in allowed_actions
   - `ScopeIncidentMismatch` - Wrong incident

5. **Files Changed:**
   - `backend/app/services/scoped_execution.py` - Full scope gating
   - `backend/app/api/recovery.py` - New endpoints

#### Test Script Compliance (P2FC-4)

| Step | Test | Status |
|------|------|--------|
| A1 | Execute without scope → 400 | ✅ |
| A2 | Create scope → scope_id | ✅ |
| A3 | Execute with scope → success | ✅ |
| A4 | Reuse scope → exhausted | ✅ |
| A5 | Different action → action_outside_scope | ✅ |

#### Memory Pin Mapping (P2FC-4)

| Memory Pin | Meaning | Status |
|------------|---------|--------|
| PIN-148 | Incident lifecycle | ✅ Required |
| PIN-161 | Evidence completeness | ✅ Replay feeds scope |
| PIN-172 | Scoped execution invariant | ✅ Enforced |
| PIN-M6-P2FC | Recovery gated by scope | ✅ Promoted |

#### New Invariant (P2FC-4)

> "A recovery action without a valid execution scope is invalid by definition."

#### Kill Criteria Verification

| Criterion | Status |
|-----------|--------|
| Recovery executes without scope | ❌ Blocked |
| Scope auto-created without intent | ❌ Blocked |
| Scope reused across incidents | ❌ Blocked |
| Cost exceeds scope silently | ❌ Tracked |
| Scope hidden from user | ❌ Visible via API |
