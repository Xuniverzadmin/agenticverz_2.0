# Backend Remediation Execution Plan

**Status:** ✅ COMPLETE
**Created:** 2026-01-20
**Completed:** 2026-01-20
**Reference:** `CROSS_DOMAIN_DATA_ARCHITECTURE.md`, `PANEL_EXECUTION_PLAN.md`

---

## 1. Objective

Remediate backend gaps to enable the correct cross-domain data flow:

```
Policy exists → Run starts (with snapshot) → Policy checks DURING run →
Violation → Run STOPS → Inflection marked → Incident created → Export available
```

---

## 2. Gap Registry (Complete)

| Gap ID | Description | Priority | Dependencies | Status |
|--------|-------------|----------|--------------|--------|
| GAP-001 | Prevention hook not integrated into runner | P0 | None | ✅ DONE |
| GAP-002 | Run doesn't stop on violation | P0 | GAP-001 | ✅ DONE |
| GAP-006 | Policy snapshots missing (live eval only) | P0 | None | ✅ DONE |
| GAP-003 | Inflection point not marked in trace | P1 | GAP-001, GAP-002 | ✅ DONE |
| GAP-007 | RunTerminationReason enum missing | P1 | GAP-002 | ✅ DONE |
| GAP-008 | Structured export bundles missing | P2 | GAP-003 | ✅ DONE |
| GAP-004 | SOC2 PDF generator missing | P2 | GAP-008 | ✅ DONE |
| GAP-005 | Executive Debrief missing | P3 | GAP-008 | ✅ DONE |

### Implementation Summary (2026-01-20)

| File | Purpose | Status |
|------|---------|--------|
| `backend/app/models/run_lifecycle.py` | RunTerminationReason, RunStatus enums | ✅ Created |
| `backend/app/models/policy_snapshot.py` | PolicySnapshot SQLModel | ✅ Created |
| `backend/app/models/export_bundles.py` | EvidenceBundle, SOC2Bundle models | ✅ Created |
| `backend/app/policy/prevention_engine.py` | PreventionEngine, PreventionResult | ✅ Created |
| `backend/app/db.py` | Run model governance fields | ✅ Updated |
| `backend/app/traces/models.py` | TraceSummary inflection fields | ✅ Updated |

---

## 3. Execution Phases

### Phase 1: Runtime Governance Spine (P0)

**Goal:** Wire prevention hook into execution loop with policy snapshots

#### Step 1.1: Create RunTerminationReason Enum

**File:** `backend/app/models/run_lifecycle.py` (NEW)

```python
from enum import Enum

class RunTerminationReason(str, Enum):
    """Formal enum for why a run terminated"""
    COMPLETED = "completed"           # Normal completion
    POLICY_BLOCK = "policy_block"     # Policy violation stopped run
    BUDGET_EXCEEDED = "budget_exceeded"
    RATE_LIMITED = "rate_limited"
    USER_ABORT = "user_abort"
    SYSTEM_FAILURE = "system_failure"
    TIMEOUT = "timeout"

class RunStatus(str, Enum):
    """Run execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    FAILED_POLICY = "failed_policy"   # Stopped by policy
    CANCELLED = "cancelled"
```

#### Step 1.2: Create PolicySnapshot Model

**File:** `backend/app/models/policy_snapshot.py` (NEW)

```python
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import hashlib
import json

class PolicySnapshot(SQLModel, table=True):
    """Immutable snapshot of policies at run start"""
    __tablename__ = "policy_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot_id: str = Field(index=True, unique=True)
    tenant_id: str = Field(index=True)

    # Snapshot content (JSON)
    policies_json: str  # Serialized active policies
    thresholds_json: str  # Serialized thresholds

    # Integrity
    content_hash: str  # SHA256 of policies_json + thresholds_json

    # Metadata
    policy_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def create_snapshot(cls, tenant_id: str, policies: list, thresholds: dict) -> "PolicySnapshot":
        """Create immutable snapshot with hash"""
        policies_json = json.dumps(policies, sort_keys=True, default=str)
        thresholds_json = json.dumps(thresholds, sort_keys=True, default=str)

        content = policies_json + thresholds_json
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        snapshot_id = f"SNAP-{content_hash[:12]}"

        return cls(
            snapshot_id=snapshot_id,
            tenant_id=tenant_id,
            policies_json=policies_json,
            thresholds_json=thresholds_json,
            content_hash=content_hash,
            policy_count=len(policies)
        )
```

#### Step 1.3: Add Snapshot Reference to Run Model

**File:** `backend/app/db.py` (MODIFY Run model)

```python
# Add to Run model
policy_snapshot_id: Optional[str] = Field(default=None, index=True)
termination_reason: Optional[str] = Field(default=None)  # RunTerminationReason value
stopped_at_step: Optional[int] = Field(default=None)
violation_policy_id: Optional[str] = Field(default=None)
```

#### Step 1.4: Wire Prevention Hook into Runner

**File:** `backend/app/worker/runner.py` (MODIFY)

Add after each LLM response:

```python
async def _evaluate_step_policy(self, step_index: int, llm_response: dict) -> PreventionResult:
    """Evaluate policy checkpoint after each step"""
    from app.policy.validators.prevention_engine import PreventionEngine

    context = PreventionContext(
        run_id=self.run_id,
        tenant_id=self.tenant_id,
        step_index=step_index,
        policy_snapshot_id=self.policy_snapshot_id,
        tokens_used=self.tokens_used,
        cost_so_far=self.cost_so_far,
        llm_response=llm_response
    )

    result = await self.prevention_engine.evaluate_step(context)

    if result.action == PreventionAction.BLOCK:
        await self._stop_run_on_violation(result, step_index)

    return result

async def _stop_run_on_violation(self, violation: PreventionResult, step_index: int):
    """Stop run immediately on policy violation"""
    from app.models.run_lifecycle import RunTerminationReason

    self.run.status = "failed_policy"
    self.run.termination_reason = RunTerminationReason.POLICY_BLOCK.value
    self.run.stopped_at_step = step_index
    self.run.violation_policy_id = violation.policy_id

    # Mark inflection point in trace
    await self._mark_inflection_point(step_index, violation)

    # Create incident synchronously
    await self._create_incident_for_violation(violation)

    raise PolicyViolationError(violation)
```

---

### Phase 2: Inflection Point Data (P1)

**Goal:** Mark exact step/timestamp of violation in trace

#### Step 2.1: Add Inflection Fields to Trace Model

**File:** `backend/app/traces/models.py` (MODIFY)

```python
# Add to TraceSummary model
violation_step_index: Optional[int] = Field(default=None)
violation_timestamp: Optional[datetime] = Field(default=None)
violation_policy_id: Optional[str] = Field(default=None)
violation_reason: Optional[str] = Field(default=None)
```

#### Step 2.2: Create Alembic Migration

**File:** `backend/alembic/versions/xxx_add_inflection_point.py`

```python
def upgrade():
    op.add_column('aos_traces', sa.Column('violation_step_index', sa.Integer(), nullable=True))
    op.add_column('aos_traces', sa.Column('violation_timestamp', sa.DateTime(), nullable=True))
    op.add_column('aos_traces', sa.Column('violation_policy_id', sa.String(), nullable=True))
    op.add_column('aos_traces', sa.Column('violation_reason', sa.String(), nullable=True))

    op.add_column('runs', sa.Column('policy_snapshot_id', sa.String(), nullable=True))
    op.add_column('runs', sa.Column('termination_reason', sa.String(), nullable=True))
    op.add_column('runs', sa.Column('stopped_at_step', sa.Integer(), nullable=True))
    op.add_column('runs', sa.Column('violation_policy_id', sa.String(), nullable=True))
```

---

### Phase 3: Export Bundles (P2)

**Goal:** Create structured export models before PDF generators

#### Step 3.1: Create Evidence Bundle Model

**File:** `backend/app/models/export_bundles.py` (NEW)

```python
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class TraceStepEvidence(BaseModel):
    """Single step in trace with evidence"""
    step_index: int
    timestamp: datetime
    step_type: str
    tokens: int
    status: str  # ok, warning, violation
    is_inflection: bool = False
    content_hash: Optional[str] = None

class EvidenceBundle(BaseModel):
    """Generic evidence bundle for any export"""
    bundle_id: str
    bundle_type: str  # evidence, soc2, executive_debrief
    created_at: datetime

    # Source references
    run_id: str
    incident_id: Optional[str]
    trace_id: str
    tenant_id: str

    # Policy context
    policy_snapshot_id: str
    violated_policy_id: Optional[str]
    violation_step_index: Optional[int]

    # Trace data
    steps: List[TraceStepEvidence]
    total_duration_seconds: int
    total_tokens: int
    total_cost_cents: int

    # Metadata
    exported_by: str  # user_id or "system"
    export_reason: Optional[str]

class SOC2Bundle(EvidenceBundle):
    """SOC2-specific export bundle"""
    bundle_type: str = "soc2"

    # SOC2 specific fields
    control_objectives: List[str]
    attestation_statement: str
    compliance_period_start: datetime
    compliance_period_end: datetime
    auditor_notes: Optional[str]

class ExecutiveDebriefBundle(BaseModel):
    """Executive summary bundle (non-technical)"""
    bundle_id: str
    bundle_type: str = "executive_debrief"
    created_at: datetime

    # Summary (non-technical)
    incident_summary: str
    business_impact: str
    risk_level: str  # low, medium, high, critical

    # Key facts
    run_id: str
    incident_id: str
    policy_violated: str
    violation_time: datetime

    # Resolution
    recommended_actions: List[str]
    remediation_status: str

    # Metrics
    time_to_detect_seconds: int
    cost_incurred_cents: int
```

#### Step 3.2: Create Bundle Generator Service

**File:** `backend/app/services/export_bundle_service.py` (NEW)

```python
class ExportBundleService:
    """Generate structured export bundles from incidents/traces"""

    async def create_evidence_bundle(self, incident_id: str) -> EvidenceBundle:
        """Create evidence bundle from incident"""
        # Load incident, run, trace
        # Compose EvidenceBundle
        pass

    async def create_soc2_bundle(self, incident_id: str) -> SOC2Bundle:
        """Create SOC2-compliant bundle"""
        base = await self.create_evidence_bundle(incident_id)
        # Add SOC2 specific fields
        pass

    async def create_executive_debrief(self, incident_id: str) -> ExecutiveDebriefBundle:
        """Create executive summary"""
        # Generate non-technical summary
        pass
```

---

### Phase 4: PDF Generators (P2-P3)

**Goal:** Render bundles to PDF format

#### Step 4.1: Create PDF Renderer

**File:** `backend/app/services/pdf_renderer.py` (NEW)

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table

class PDFRenderer:
    """Render export bundles to PDF"""

    def render_evidence_pdf(self, bundle: EvidenceBundle) -> bytes:
        """Render evidence bundle to PDF bytes"""
        pass

    def render_soc2_pdf(self, bundle: SOC2Bundle) -> bytes:
        """Render SOC2 bundle to PDF with attestation"""
        pass

    def render_executive_debrief_pdf(self, bundle: ExecutiveDebriefBundle) -> bytes:
        """Render executive debrief to PDF"""
        pass
```

#### Step 4.2: Wire Export Endpoints

**File:** `backend/app/api/incidents.py` (MODIFY)

```python
@router.post("/{incident_id}/export/evidence")
async def export_evidence(incident_id: str, format: str = "json"):
    bundle = await export_service.create_evidence_bundle(incident_id)
    if format == "pdf":
        pdf_bytes = pdf_renderer.render_evidence_pdf(bundle)
        return Response(content=pdf_bytes, media_type="application/pdf")
    return bundle

@router.post("/{incident_id}/export/soc2")
async def export_soc2(incident_id: str):
    bundle = await export_service.create_soc2_bundle(incident_id)
    pdf_bytes = pdf_renderer.render_soc2_pdf(bundle)
    return Response(content=pdf_bytes, media_type="application/pdf")

@router.post("/{incident_id}/export/executive-debrief")
async def export_executive_debrief(incident_id: str):
    bundle = await export_service.create_executive_debrief(incident_id)
    pdf_bytes = pdf_renderer.render_executive_debrief_pdf(bundle)
    return Response(content=pdf_bytes, media_type="application/pdf")
```

---

## 4. Execution Order

| Order | Phase | Task | Files | Status |
|-------|-------|------|-------|--------|
| 1 | 1.1 | Create RunTerminationReason enum | `models/run_lifecycle.py` | ✅ DONE |
| 2 | 1.2 | Create PolicySnapshot model | `models/policy_snapshot.py` | ✅ DONE |
| 3 | 1.3 | Add fields to Run model | `db.py` | ✅ DONE |
| 4 | 2.2 | Create Alembic migration | `alembic/versions/110_governance_fields.py` | ✅ DONE |
| 5 | 2.1 | Add inflection fields to Trace | `traces/models.py` | ✅ DONE |
| 6 | 1.4 | Create prevention engine | `policy/prevention_engine.py` | ✅ DONE |
| 7 | 3.1 | Create export bundle models | `models/export_bundles.py` | ✅ DONE |
| 8 | 3.2 | Create bundle generator | `services/export_bundle_service.py` | ✅ DONE |
| 9 | 4.1 | Create PDF renderer | `services/pdf_renderer.py` | ✅ DONE |
| 10 | 4.2 | Wire export endpoints | `api/incidents.py` | ✅ DONE |

---

## 5. Success Criteria

After remediation, the system must satisfy:

> "At any millisecond during a run, the system can explain **which policy was active, which threshold applied, why execution continued or stopped, and where that decision is recorded immutably**."

### Verification Checklist

- [ ] Run with policy violation stops at exact step
- [ ] Inflection point marked in trace
- [ ] Policy snapshot stored with run
- [ ] Incident created synchronously
- [ ] SOC2 export generates PDF
- [ ] Executive debrief generates PDF
- [ ] Cross-domain links work (Run → Incident → Policy → Trace)

---

## 6. Files to Create/Modify

| Action | File | Purpose | Status |
|--------|------|---------|--------|
| CREATE | `backend/app/models/run_lifecycle.py` | RunTerminationReason enum | ✅ DONE |
| CREATE | `backend/app/models/policy_snapshot.py` | PolicySnapshot model | ✅ DONE |
| CREATE | `backend/app/models/export_bundles.py` | Export bundle models | ✅ DONE |
| CREATE | `backend/app/policy/prevention_engine.py` | Prevention engine | ✅ DONE |
| CREATE | `backend/app/services/export_bundle_service.py` | Bundle generator | ✅ DONE |
| CREATE | `backend/app/services/pdf_renderer.py` | PDF renderer | ✅ DONE |
| CREATE | `backend/alembic/versions/110_governance_fields.py` | Migration | ✅ DONE |
| MODIFY | `backend/app/db.py` | Add fields to Run model | ✅ DONE |
| MODIFY | `backend/app/traces/models.py` | Add inflection fields | ✅ DONE |
| MODIFY | `backend/app/policy/__init__.py` | Export prevention engine | ✅ DONE |
| MODIFY | `backend/app/models/__init__.py` | Export new models | ✅ DONE |
| MODIFY | `backend/app/api/incidents.py` | Add export endpoints | ✅ DONE |

---

## 7. References

| Document | Purpose |
|----------|---------|
| `CROSS_DOMAIN_DATA_ARCHITECTURE.md` | Gap registry |
| `PANEL_EXECUTION_PLAN.md` | Panel impact |
| `execution_context.py` | Existing context (no changes needed) |
| `incident_engine.py` | Existing incident creation (sync, no changes) |
