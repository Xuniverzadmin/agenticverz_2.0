# HOC Migration Phase 2 - Extraction Playbook

**Version:** 1.0
**Date:** 2026-01-23
**Status:** ACTIVE
**Purpose:** Operational playbook for layer migration execution

---

## 1. Core Diagnosis (Non-Negotiable)

> **82% of L4 "engines" are actually L6 DB code.**

This is THE problem. Everything else (headers, folders, naming) is secondary.

**Implication:** The system does not currently have an L4 layer in practice. You must *create* L4 by **removing DB gravity**, not by adding rules.

**Key Numbers:**
- 348 files declare L4
- Only 13 behave like L4
- 285 (82%) behave like L6 (DB operations)
- 480 files total behave like L6
- Only 21 files are true L4 engines

---

## 2. Phase Ordering (Strict - No Skipping)

### ❌ What NOT to Start With

- Do NOT touch HIGH effort files first
- Do NOT try to "fix" engines conceptually
- Do NOT redesign runtime now

You will amplify chaos.

---

### Phase 0 — Stabilize the Measurement (2-3 days)

**Goal:** Ensure the report is trustworthy and repeatable.

**Actions:**
1. ✅ Freeze `layer_classifier.py` rules (DONE)
2. ✅ Commit reports (DONE):
   - `layer_fit_detailed_report.md`
   - `layer_fit_report.json`
   - `layer_fit_customer_domains.md`
3. ⏳ Add CI rule:
   - ❌ Fail if total MISFIT count increases

**No code refactors yet.**

---

### Phase 1 — Low Effort Mass Cleanup (Week 1)

**276 files (HEADER_FIX + RECLASSIFY)**

**Why first:** These reduce noise so MEDIUM work is accurate.

**Rules:**
- **HEADER_FIX_ONLY** → Change header, nothing else
- **RECLASSIFY_ONLY** → Move file, no edits

**Outcome required before proceeding:**
- [ ] Folder-based stats stabilize
- [ ] False positives drop
- [ ] EXTRACT_DRIVER list becomes "pure"

---

### Phase 2 — Driver Extraction (Week 2-3)

**234 files (EXTRACT_DRIVER)**

This is the main event. See Section 3 for extraction rules.

**Stop Condition (Critical):**
> Stop MEDIUM work when: **Engines with DB signals ≤ 5%**

Until then:
- Do NOT touch HIGH effort files
- Do NOT redesign runtime
- Do NOT add new engines

---

### Phase 3 — Complex Work (Week 4)

**32 files (EXTRACT_AUTHORITY + SPLIT_FILE)**

Only after Phase 2 stop condition is met.

---

## 3. Driver Extraction Rules (Canonical)

### 3.1 Extraction Criteria

For every EXTRACT_DRIVER file:

| If the line contains... | Action |
|-------------------------|--------|
| `select(`, `insert(`, `update(`, `delete(` | Move to `drivers/` |
| `Session`, `AsyncSession` | Move to `drivers/` |
| `from sqlalchemy import` | Move to `drivers/` |
| `from sqlmodel import` | Move to `drivers/` |
| `session.execute()`, `session.add()` | Move to `drivers/` |
| `.scalars()`, `.one()`, `.all()`, `.first()` | Move to `drivers/` |
| `.commit()`, `.flush()`, `.refresh()` | Move to `drivers/` |
| ORM model import (`from app.models.*`) | Move to `drivers/` |
| if/else business rules | Stay in engine |
| Aggregation / mapping logic | Stay in engine |
| Domain object returns (Verdict, Decision) | Stay in engine |

**No exceptions.**

---

### 3.2 Target Shape (Validation Criteria)

After extraction:

**Engine file MUST:**
- ❌ No SQLAlchemy imports
- ❌ No session usage
- ❌ No direct DB calls
- ✅ Calls driver methods only
- ✅ Contains business logic only
- ✅ Returns domain objects

**Driver file MUST:**
- ❌ No business branching
- ❌ No cross-domain imports
- ❌ No authority decisions
- ✅ DB in → rows out
- ✅ Single responsibility
- ✅ In `drivers/` folder

**If either condition fails → rollback.**

---

### 3.3 Extraction Template

**Before (engine with DB gravity):**
```python
# Layer: L4 — Engine
# AUDIENCE: CUSTOMER
# Role: Incident management business logic

from sqlalchemy import select
from sqlmodel import Session
from app.models.incidents import Incident

class IncidentEngine:
    def __init__(self, session: Session):
        self.session = session

    def get_active_incidents(self, tenant_id: str) -> List[IncidentDTO]:
        # DB operation mixed with business logic
        stmt = select(Incident).where(
            Incident.tenant_id == tenant_id,
            Incident.status == "active"
        )
        rows = self.session.execute(stmt).scalars().all()

        # Business logic
        return [
            IncidentDTO(
                id=r.id,
                severity=self._classify_severity(r),
                priority=self._calculate_priority(r)
            )
            for r in rows
        ]

    def _classify_severity(self, incident: Incident) -> str:
        # Business rule
        if incident.impact_score > 80:
            return "critical"
        elif incident.impact_score > 50:
            return "high"
        return "medium"
```

**After (engine + driver separated):**

**Driver (NEW - `drivers/incident_read_service.py`):**
```python
# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Incident data access (read operations)

from sqlalchemy import select
from sqlmodel import Session
from app.models.incidents import Incident
from typing import List

class IncidentReadService:
    """Pure data access - no business logic."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_tenant_and_status(
        self, tenant_id: str, status: str
    ) -> List[Incident]:
        stmt = select(Incident).where(
            Incident.tenant_id == tenant_id,
            Incident.status == status
        )
        return self.session.execute(stmt).scalars().all()
```

**Engine (CLEANED - `engines/incident_engine.py`):**
```python
# Layer: L4 — Engine
# AUDIENCE: CUSTOMER
# Role: Incident management business logic

from typing import List
from ..drivers.incident_read_service import IncidentReadService
from ..schemas.incident_dto import IncidentDTO

class IncidentEngine:
    """Business logic only - no DB imports."""

    def __init__(self, incident_driver: IncidentReadService):
        self.driver = incident_driver

    def get_active_incidents(self, tenant_id: str) -> List[IncidentDTO]:
        # Get raw data from driver
        rows = self.driver.get_by_tenant_and_status(tenant_id, "active")

        # Apply business logic
        return [
            IncidentDTO(
                id=r.id,
                severity=self._classify_severity(r),
                priority=self._calculate_priority(r)
            )
            for r in rows
        ]

    def _classify_severity(self, incident) -> str:
        """Business rule - stays in engine."""
        if incident.impact_score > 80:
            return "critical"
        elif incident.impact_score > 50:
            return "high"
        return "medium"
```

---

### 3.4 Batch by Pattern (Not by Domain)

Do NOT process: activity → incidents → policies

Instead batch by **file behavior pattern**:

| Batch | Pattern | Count | Template |
|-------|---------|-------|----------|
| 1 | `*_read_service.py` | ~80 | Read-only driver |
| 2 | `*_write_service.py` | ~60 | Write-only driver |
| 3 | `*_facade.py` with DB | ~50 | Facade + driver split |
| 4 | Mixed read/write | ~44 | Dual driver extraction |

This allows copy-paste extraction with minimal thinking.

---

## 4. HIGH Effort Work (32 files)

Only after Phase 2 stop condition is met.

### 4.1 EXTRACT_AUTHORITY (12 files)

**Smells to look for:**
- Retries (`@retry`, `tenacity`)
- Incident creation
- Policy enforcement
- HTTP awareness (`HTTPException`, `JSONResponse`)

**Action:**
- Pull *decisions* upward into L4 runtime
- Leave execution in engines

**Rule:**
> Engines decide *how*
> Runtime decides *whether*

Never invert this.

### 4.2 SPLIT_FILE (20 files)

These are **historical blobs** with multiple responsibilities.

**Procedure (mandatory):**
1. Freeze file (no other changes)
2. Extract outward (drivers / schemas / engines)
3. Shrink original
4. Delete or reclassify last

**Never rewrite in place.**

---

## 5. CI Enforcement (Drift Prevention)

### 5.1 CI Rules (Immediate)

Add these CI rules:

```yaml
# .github/workflows/layer-compliance.yml
layer_compliance:
  rules:
    - name: no_regression
      fail_if: FIT_file_becomes_MISFIT
      severity: BLOCKING

    - name: new_file_layer
      fail_if: new_file_has_no_declared_layer
      severity: BLOCKING

    - name: engine_purity
      fail_if: engine_imports_sqlalchemy
      severity: BLOCKING

    - name: misfit_increase
      fail_if: total_MISFIT_count_increases
      severity: BLOCKING
```

**No warnings. Only failures.**

### 5.2 Allowed Violations Registry

Create `docs/architecture/migration/ALLOWED_VIOLATIONS.yaml`:

```yaml
# Temporary escape hatch for known violations
# CI fails if:
#   - expiry passes without resolution
#   - new violation added without entry

allowed_violations:
  - file: hoc/cus/incidents/L5_engines/legacy_service.py
    action: EXTRACT_DRIVER
    expires: 2026-03-15
    reason: Pending Phase 2 extraction
    owner: team-incidents

  - file: hoc/cus/integrations/facades/webhook_adapter.py
    action: EXTRACT_AUTHORITY
    expires: 2026-04-01
    reason: Pending Phase 3 - requires architect review
    owner: team-integrations
```

---

## 6. Progress Tracking

### 6.1 Key Metrics

| Metric | Start | Target | Current |
|--------|-------|--------|---------|
| Total MISFIT | 560 | <100 | 560 |
| Engines with DB signals | 82% | <5% | 82% |
| FIT files | 155 | >600 | 155 |
| Work items remaining | 542 | 0 | 542 |

### 6.2 Phase Gate Criteria

| Phase | Entry Criteria | Exit Criteria |
|-------|----------------|---------------|
| Phase 0 | - | CI rules active, reports committed |
| Phase 1 | Phase 0 complete | 276 LOW files processed |
| Phase 2 | Phase 1 complete | DB signals in engines ≤ 5% |
| Phase 3 | Phase 2 complete | All 32 HIGH files processed |

---

## 7. Domain Execution Order (Based on Priority Matrix)

### Phase 1 Order (LOW effort)

| Order | Domain | HEADER_FIX | RECLASSIFY | Total LOW |
|-------|--------|------------|------------|-----------|
| 1 | policies | 3 | 42 | 45 |
| 2 | integrations | 4 | 16 | 20 |
| 3 | general | 4 | 14 | 18 |
| 4 | logs | 3 | 12 | 15 |
| 5 | incidents | 2 | 10 | 12 |
| 6 | agent | 1 | 10 | 11 |
| 7 | analytics | 1 | 7 | 8 |
| 8 | account | 0 | 3 | 3 |
| 9-13 | (remaining) | 2 | 5 | 7 |

### Phase 2 Order (MEDIUM effort)

| Order | Domain | EXTRACT_DRIVER | Pattern Focus |
|-------|--------|----------------|---------------|
| 1 | policies | 34 | `*_service.py`, `*_facade.py` |
| 2 | logs | 23 | `*_facade.py`, `*_detector.py` |
| 3 | integrations | 20 | `*_adapter.py`, `*_base.py` |
| 4 | general | 19 | `*_service.py`, `*_manager.py` |
| 5 | incidents | 13 | `*_service.py`, `*_engine.py` |
| 6 | analytics | 9 | `*_worker.py`, `*_service.py` |
| 7-13 | (remaining) | 16 | Mixed patterns |

---

## 8. Success Criteria

**Migration is COMPLETE when:**
1. ✅ Engines with DB signals ≤ 5%
2. ✅ All 542 work items resolved
3. ✅ CI rules prevent regression
4. ✅ MISFIT count < 100
5. ✅ FIT count > 600

**The real outcome:**
- L4 runtime becomes obvious
- Governance becomes enforceable
- Panel engine becomes trivial
- Drift becomes mechanically impossible

---

## References

- `PHASE2_STEP3_LAYER_CRITERIA.md` - Layer signal detection rules
- `layer_fit_detailed_report.md` - Full analysis report
- `layer_fit_customer_domains.md` - Domain-wise breakdown
- `layer_fit_report.json` - Machine-readable data

---

**Document Status:** ACTIVE
**Next Action:** Implement Phase 0 CI rules
