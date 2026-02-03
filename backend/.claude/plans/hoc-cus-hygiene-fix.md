# HOC/CUS Hygiene Fix Plan

**Status:** PENDING APPROVAL
**Date:** 2026-02-03
**Reference:** Two-pass analysis with Python validation

---

## Problem Statement

Two-pass analysis of `hoc/cus/` identified:
- 1 broken import (critical)
- 4 missing `__init__.py` files
- 37 files missing `# AUDIENCE:` header
- 12 NotImplementedError locations (deferred)
- 18 TODOs (deferred)

---

## Scope

**In Scope:**
- Fix broken import (critical path)
- Add missing `__init__.py` files
- Add `# AUDIENCE:` headers to 37 files

**Out of Scope (Deferred):**
- NotImplementedError stubs (require design decisions)
- TODOs (require feature implementation)
- Zero-caller analysis (requires broader audit)

---

## Fix Plan

### Phase 1: Critical — Fix Broken Import

**File:** `app/hoc/cus/incidents/L5_engines/prevention_engine.py`

**Lines 819 and 848:**
```python
# BEFORE (broken):
from app.hoc.cus.incidents.L5_engines.policy_violation_service import (
    PolicyViolationService,
    ViolationFact,
)

# AFTER (fixed):
from app.hoc.cus.incidents.L5_engines.policy_violation_engine import (
    PolicyViolationEngine,
    ViolationFact,
)
```

**Also update any usage of `PolicyViolationService` → `PolicyViolationEngine`**

---

### Phase 2: Add Missing `__init__.py` Files

| Directory | Content |
|-----------|---------|
| `hoc_spine/tests/__init__.py` | Empty (test package) |
| `apis/L6_drivers/__init__.py` | Empty (driver package) |
| `logs/L5_support/CRM/engines/__init__.py` | Empty (engine package) |
| `integrations/L5_notifications/engines/__init__.py` | Empty (engine package) |

**Template:**
```python
# Layer: L{X} — {Type}
# AUDIENCE: INTERNAL
# Role: Package marker for {description}
```

---

### Phase 3: Add Missing `# AUDIENCE:` Headers

**37 files require `# AUDIENCE:` header addition.**

**Files by domain:**

| Domain | Files | Default AUDIENCE |
|--------|-------|------------------|
| hoc_spine/schemas | 1 | INTERNAL |
| hoc_spine/authority | 2 | INTERNAL |
| hoc_spine/orchestrator | 1 | INTERNAL |
| policies/adapters | 3 | CUSTOMER |
| policies/L5_schemas | 1 | INTERNAL |
| policies/L5_engines | 2 | CUSTOMER |
| activity/adapters | 2 | CUSTOMER |
| api_keys/adapters | 1 | CUSTOMER |
| logs/adapters | 1 | CUSTOMER |
| integrations/adapters | 12 | CUSTOMER |
| Other | 11 | INTERNAL |

**Header format to add (after `# Layer:` line):**
```python
# AUDIENCE: {CUSTOMER|INTERNAL}
```

---

## File List

### Phase 1: Broken Import (1 file)

```
app/hoc/cus/incidents/L5_engines/prevention_engine.py
```

### Phase 2: Missing `__init__.py` (4 files to create)

```
app/hoc/cus/hoc_spine/tests/__init__.py
app/hoc/cus/apis/L6_drivers/__init__.py
app/hoc/cus/logs/L5_support/CRM/engines/__init__.py
app/hoc/cus/integrations/L5_notifications/engines/__init__.py
```

### Phase 3: Header Fixes (37 files)

```
hoc_spine/schemas/retry.py
hoc_spine/authority/degraded_mode_checker.py
hoc_spine/authority/runtime_adapter.py
hoc_spine/orchestrator/execution/job_executor.py
policies/adapters/policy_adapter.py
policies/adapters/customer_policies_adapter.py
policies/adapters/founder_contract_review_adapter.py
policies/L5_schemas/policy_rules.py
policies/L5_engines/policy_command.py
policies/L5_engines/worker_execution_command.py
policies/L5_engines/plan_generation_engine.py
activity/adapters/workers_adapter.py
activity/adapters/customer_activity_adapter.py
api_keys/adapters/customer_keys_adapter.py
logs/adapters/customer_logs_adapter.py
integrations/adapters/vector_stores_base.py
integrations/adapters/founder_ops_adapter.py
integrations/adapters/smtp_adapter.py
integrations/adapters/slack_adapter.py
integrations/adapters/pgvector_adapter.py
integrations/adapters/serverless_base.py
integrations/adapters/workers_adapter.py
integrations/adapters/gcs_adapter.py
integrations/adapters/webhook_adapter.py
integrations/adapters/file_storage_base.py
integrations/adapters/weaviate_adapter.py
integrations/adapters/customer_activity_adapter.py
integrations/adapters/customer_keys_adapter.py
integrations/adapters/cloud_functions_adapter.py
integrations/adapters/runtime_adapter.py
integrations/L5_schemas/datasource_model.py
controls/adapters/customer_controls_adapter.py
controls/adapters/controls_adapter.py
overview/adapters/customer_overview_adapter.py
incidents/adapters/customer_incidents_adapter.py
incidents/adapters/incidents_adapter.py
account/adapters/account_adapter.py
```

---

## Verification

```bash
# 1. Verify broken import fixed
PYTHONPATH=. python3 -c "
from app.hoc.cus.incidents.L5_engines.prevention_engine import *
print('OK: prevention_engine imports cleanly')
"

# 2. Verify __init__.py files created
ls -la app/hoc/cus/hoc_spine/tests/__init__.py
ls -la app/hoc/cus/apis/L6_drivers/__init__.py
ls -la app/hoc/cus/logs/L5_support/CRM/engines/__init__.py
ls -la app/hoc/cus/integrations/L5_notifications/engines/__init__.py

# 3. Verify AUDIENCE headers (sample)
head -5 app/hoc/cus/hoc_spine/schemas/retry.py | grep AUDIENCE

# 4. Run CI hygiene check
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
```

---

## Execution Order

1. **Phase 1** — Fix broken import (prevents runtime errors)
2. **Phase 2** — Add `__init__.py` files (enables proper imports)
3. **Phase 3** — Add AUDIENCE headers (compliance)
4. **Verify** — Run verification commands
5. **Commit** — Single commit with all fixes

---

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|------------|
| 1 | Class rename may break callers | Grep for all usages before/after |
| 2 | None | Empty files, no behavior change |
| 3 | None | Comment-only changes |

---

## Commit Message (Draft)

```
fix(hoc): hygiene fixes — broken import, missing __init__, AUDIENCE headers

Phase 1: Fix broken import in prevention_engine.py
- Change policy_violation_service → policy_violation_engine
- Update class reference PolicyViolationService → PolicyViolationEngine

Phase 2: Add missing __init__.py (4 files)
- hoc_spine/tests/, apis/L6_drivers/
- logs/L5_support/CRM/engines/, integrations/L5_notifications/engines/

Phase 3: Add # AUDIENCE: headers (37 files)
- All adapters: CUSTOMER
- All schemas/authority/orchestrator: INTERNAL

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## Approval Required

- [ ] Phase 1: Fix broken import
- [ ] Phase 2: Add missing `__init__.py`
- [ ] Phase 3: Add AUDIENCE headers

**Approve all phases?**
