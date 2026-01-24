# Phase 2 Extraction Protocol

**Version:** 1.0
**Date:** 2026-01-23
**Status:** ACTIVE

---

## 1. Canonical Segregation Contract (NON-NEGOTIABLE)

### L4 — Engine (After Extraction)

Engine files **MUST satisfy ALL**:

| Constraint | Required |
|------------|----------|
| ❌ No `sqlalchemy` imports | MANDATORY |
| ❌ No `sqlmodel` imports | MANDATORY |
| ❌ No `Session`, `AsyncSession` | MANDATORY |
| ❌ No `select() / insert() / update() / delete()` | MANDATORY |
| ❌ No ORM model imports | MANDATORY |
| ✅ Only business rules | MANDATORY |
| ✅ Only decision logic | MANDATORY |
| ✅ Only calls to drivers | MANDATORY |
| ✅ Returns domain DTOs / primitives | MANDATORY |

### L6 — Driver

Driver files **MUST satisfy ALL**:

| Constraint | Required |
|------------|----------|
| ❌ No business branching (`if policy…`, `if budget…`) | MANDATORY |
| ❌ No cross-domain imports | MANDATORY |
| ❌ No retries / sleeps / orchestration | MANDATORY |
| ✅ Only DB reads/writes | MANDATORY |
| ✅ Only ORM ↔ DTO transformation | MANDATORY |
| ✅ Only query construction | MANDATORY |

**If a file violates both → SPLIT, not compromise.**

---

## 2. Driver Naming Convention

### Pattern Rules

| Source File Pattern | Driver Name Pattern | Example |
|--------------------|--------------------|---------|
| `{domain}_read_service.py` | `{domain}_read_driver.py` | `incident_read_driver.py` |
| `{domain}_write_service.py` | `{domain}_write_driver.py` | `incident_write_driver.py` |
| `{domain}_service.py` (mixed) | `{domain}_driver.py` | `incident_driver.py` |
| `{domain}_facade.py` | `{domain}_data_driver.py` | `policies_data_driver.py` |
| `{domain}_engine.py` | `{domain}_persistence_driver.py` | `prevention_persistence_driver.py` |

### Naming Principles

1. **Intent over origin** - Name reflects what the driver does, not where it came from
   - ❌ `incident_service_driver.py` (origin-based)
   - ✅ `incident_read_driver.py` (intent-based)

2. **Read/Write separation** - Prefer separate read and write drivers
   - ✅ `incident_read_driver.py` + `incident_write_driver.py`
   - ⚠️ `incident_driver.py` (only if operations are minimal)

3. **Domain prefix** - Always include domain in driver name
   - ❌ `read_driver.py`
   - ✅ `incident_read_driver.py`

### File Placement

```
houseofcards/{audience}/{domain}/
├── engines/
│   └── incident_engine.py        # Business logic (no DB)
├── drivers/
│   ├── incident_read_driver.py   # Read operations
│   └── incident_write_driver.py  # Write operations
└── schemas/
    └── incident_dto.py           # Data transfer objects
```

---

## 3. Batch Execution Order (MANDATORY)

| Batch | Pattern | Files | Rationale |
|-------|---------|-------|-----------|
| 1 | `*_read_service.py` | 3 | DB-heavy, lowest coupling, fastest wins |
| 2 | `*_write_service.py` | 5 | Side-effectful but mechanical |
| 3 | `*_service.py` (mixed) | 41 | Requires judgment, do after patterns learned |
| 4 | `*_facade.py` | 24 | L4/L3 confusion cases, only after DB gravity removed |
| 5 | Other patterns | 162 | Last, most varied |

**DO NOT MIX BATCHES.**

---

## 4. Per-File Extraction Procedure

### Step 1: FREEZE

- [ ] No refactors
- [ ] No renames
- [ ] No logic changes
- [ ] Mark file in backlog as `in_progress`

### Step 2: MARK DB BLOCKS

Add comments to identify DB operations:

```python
# --- DB_START: query_incidents_by_tenant ---
stmt = select(Incident).where(Incident.tenant_id == tenant_id)
result = session.execute(stmt).scalars().all()
# --- DB_END ---
```

### Step 3: CREATE DRIVER

Create new file in `drivers/`:

```python
# Layer: L6 — Driver
# AUDIENCE: {CUSTOMER|FOUNDER|INTERNAL}
# Role: Data access for {domain} {read|write} operations

from typing import List, Optional
from sqlalchemy import select, insert, update, delete
from sqlmodel import Session
from app.models.{domain} import {Model}

class {Domain}{Read|Write}Driver:
    """Pure data access - no business logic."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_tenant(self, tenant_id: str) -> List[{Model}]:
        stmt = select({Model}).where({Model}.tenant_id == tenant_id)
        return self.session.execute(stmt).scalars().all()
```

### Step 4: MOVE DB BLOCKS (AS-IS)

Move marked DB blocks to driver with ZERO edits except:
- Session passed as argument (not self.session from engine)
- Return values normalized to DTO/primitive

### Step 5: REPLACE IN ENGINE

Update engine to call driver:

```python
# BEFORE
class IncidentEngine:
    def __init__(self, session: Session):
        self.session = session

    def get_active_incidents(self, tenant_id: str):
        stmt = select(Incident).where(...)  # ❌ DB in engine
        result = self.session.execute(stmt)

# AFTER
class IncidentEngine:
    def __init__(self, incident_driver: IncidentReadDriver):
        self.driver = incident_driver

    def get_active_incidents(self, tenant_id: str):
        incidents = self.driver.get_by_tenant(tenant_id)  # ✅ Driver call
        return [self._classify(i) for i in incidents]  # Business logic
```

### Step 6: ENFORCE GATE

Run classifier on extracted file:

```bash
python3 scripts/migration/layer_analysis.py
python3 scripts/migration/layer_classifier.py
```

**Verify:**
- [ ] Engine has 0 L6_DRIVER signals
- [ ] Driver has 0 L4_ENGINE signals

If not → **ROLLBACK** and retry.

### Step 7: UPDATE BACKLOG

Mark file in `phase2_backlog.yaml`:
- `status: extracted`
- `driver_file: "path/to/driver.py"`
- `extracted_date: YYYY-MM-DD`

---

## 5. Per-Batch Checklist

### Batch 1: `*_read_service.py` (3 files)

| # | File | Status | Driver | Date |
|---|------|--------|--------|------|
| 1 | `customer/incidents/engines/incident_read_service.py` | ⬜ | - | - |
| 2 | `customer/policies/controls/engines/customer_killswitch_read_service.py` | ⬜ | - | - |
| 3 | `customer/policies/engines/customer_policy_read_service.py` | ⬜ | - | - |

**Batch 1 Target:** All 3 files extracted with 0 DB signals in engines.

### Batch 2: `*_write_service.py` (5 files)

| # | File | Status | Driver | Date |
|---|------|--------|--------|------|
| 1 | `customer/account/engines/user_write_service.py` | ⬜ | - | - |
| 2 | `customer/analytics/engines/cost_write_service.py` | ⬜ | - | - |
| 3 | `customer/general/controls/engines/guard_write_service.py` | ⬜ | - | - |
| 4 | `customer/incidents/engines/incident_write_service.py` | ⬜ | - | - |
| 5 | `founder/ops/engines/founder_action_write_service.py` | ⬜ | - | - |

**Batch 2 Target:** All 5 files extracted with 0 DB signals in engines.

---

## 6. Stop Condition

**Phase 2 is DONE when:**

```
Engines with DB signals ≤ 5%
```

**Current state:**
- After Phase 1: 55% (183 impure engines)
- Target: ≤5% (~9 allowed)

**Nothing else matters.**

Until this is met:
- ❌ Do NOT start EXTRACT_AUTHORITY
- ❌ Do NOT SPLIT_FILE
- ❌ Do NOT redesign runtime
- ❌ Do NOT touch governance logic

---

## 7. CI Rules (Phase 2 Mode)

### Blocking Rules

| Rule | Trigger | Action |
|------|---------|--------|
| NEW_DB_IN_ENGINE | New L6 signal in engine file | ❌ FAIL |
| EXISTING_DB_ALLOWED | L6 signal in backlog file | ⚠️ WARN |
| DRIVER_PURITY | L4 signal in driver file | ❌ FAIL |
| BACKLOG_SYNC | File not in backlog with DB signals | ❌ FAIL |

### Enforcement

```yaml
# .github/workflows/layer-compliance.yml (Phase 2 mode)
phase2_rules:
  - name: no_new_db_in_engines
    condition: "L6_DRIVER signal in engine file NOT in backlog"
    action: FAIL

  - name: driver_purity
    condition: "L4_ENGINE signal in driver file"
    action: FAIL

  - name: backlog_sync
    condition: "File has DB signals AND not in phase2_backlog.yaml"
    action: FAIL
```

---

## 8. Verification Commands

```bash
# Run analysis after each extraction
python3 scripts/migration/layer_analysis.py
python3 scripts/migration/layer_classifier.py

# Check compliance
python3 scripts/migration/layer_compliance_check.py

# Check stop condition
python3 scripts/migration/check_stop_condition.py
```

---

## References

- `phase2_backlog.yaml` - File tracking
- `PHASE2_EXTRACTION_PLAYBOOK.md` - Overall strategy
- `PHASE1_COMPLETION_REPORT.md` - Phase 1 results
- `layer_fit_report.json` - Current state

---

**Document Status:** ACTIVE
**Next Action:** Execute Batch 1 (`*_read_service.py`)
