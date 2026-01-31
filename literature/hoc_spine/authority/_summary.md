# Authority — Folder Summary

**Path:** `backend/app/hoc/hoc_spine/authority/`  
**Layer:** L4  
**Scripts:** 8

---

## 1. Purpose

Decides WHAT is allowed, not HOW. Determines eligibility, runtime mode, policy posture, and permission boundaries.

## 2. What Belongs Here

- Eligibility decisions
- Runtime mode switching
- Policy posture configuration
- Concurrent run limits
- Contract state machine

## 3. What Must NOT Be Here

- Call L5 engines
- Touch DB drivers directly
- Orchestrate execution

## 4. Script Inventory

| Script | Purpose | Transaction | Cross-domain | Verdict |
|--------|---------|-------------|--------------|---------|
| [concurrent_runs.py](concurrent_runs.md) | Concurrent run limit enforcement (Redis-backed) | Forbidden | no | OK |
| [contract_engine.py](contract_engine.md) | Part-2 Contract Service (L4) | Forbidden | no | OK |
| [degraded_mode_checker.py](degraded_mode_checker.md) | Module: degraded_mode_checker | Forbidden | no | OK |
| [guard_write_engine.py](guard_write_engine.md) | Guard Write Engine (L5) | Forbidden | no | OK |
| [profile_policy_mode.py](profile_policy_mode.md) | Governance Profile Configuration | Forbidden | no | OK |
| [runtime.py](runtime.md) | Runtime Utilities - Centralized Shared Helpers | Forbidden | no | OK |
| [runtime_adapter.py](runtime_adapter.md) | Runtime Adapter (L2) | Forbidden | no | OK |
| [runtime_switch.py](runtime_switch.md) | Module: runtime_switch | Forbidden | no | OK |

## 5. Assessment

**Correct:** 8/8 scripts pass all governance checks.

**Missing (from reconciliation artifact):**

- Unified AuthorityDecision object returned to orchestrator
- Explicit deny / degraded / conditional execution states

## 6. L5 Pairing Aggregate

| Script | Serves Domains | Wired L5 Consumers | Gaps |
|--------|----------------|--------------------|------|
| concurrent_runs.py | _none_ | 0 | 0 |
| contract_engine.py | _none_ | 0 | 0 |
| degraded_mode_checker.py | _none_ | 0 | 0 |
| guard_write_engine.py | _none_ | 0 | 0 |
| profile_policy_mode.py | _none_ | 0 | 0 |
| runtime.py | _none_ | 0 | 0 |
| runtime_adapter.py | _none_ | 0 | 0 |
| runtime_switch.py | _none_ | 0 | 0 |

