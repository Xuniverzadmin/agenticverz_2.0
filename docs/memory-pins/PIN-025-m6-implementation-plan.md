# PIN-025: M6 Implementation Plan (Authoritative)

**Serial:** PIN-025
**Title:** M6 Full Implementation Plan
**Category:** Milestone / Implementation
**Status:** COMPLETE (Implementation done - see PIN-026)
**Created:** 2025-12-04
**Completed:** 2025-12-04
**Authority:** This supersedes all previous M6 interpretations

---

## Preconditions (M5 Lock Verified)

| Component | Status | Action |
|-----------|--------|--------|
| SDK v1 | ✅ FROZEN | No changes |
| CostSimulator V1 | ✅ FROZEN | `backend/app/worker/simulate.py` unchanged |
| Soft capability enforcement | ✅ FROZEN | No changes |
| RBAC stub | ✅ FROZEN | No changes |
| File-based webhook keys | ✅ FROZEN | No changes |
| PgBouncer simple auth | ✅ FROZEN | No changes |

---

## M6 Component Implementation Plan

### 1. CostSim V2 Sandbox Path

#### 1.1 New Files to Create

```
backend/app/costsim/
├── __init__.py
├── v2_adapter.py          # CostSimV2Adapter class
├── provenance.py          # Provenance logging
├── canary.py              # Canary runner
├── sandbox.py             # Sandbox routing
├── models.py              # V2-specific models
└── config.py              # Feature flags & config
```

#### 1.2 API Design

**Feature Flag:** `COSTSIM_V2_SANDBOX=true|false` (default: false)

**CostSimV2Adapter Interface:**
```python
class CostSimV2Adapter:
    async def simulate(self, plan: List[Dict]) -> V2SimulationResult
    async def compare_with_v1(self, plan: List[Dict]) -> ComparisonResult
```

**Provenance Log Schema:**
```python
@dataclass
class ProvenanceLog:
    id: str                    # UUID
    timestamp: datetime
    input_hash: str            # SHA256 of input
    output_hash: str           # SHA256 of output
    input_json: str            # Full input (compressed)
    output_json: str           # Full output (compressed)
    model_version: str         # V2 model version
    adapter_version: str       # Adapter version
    commit_sha: str            # Git commit
    runtime_ms: int            # Execution time
    status: str                # success/error
    tenant_id: Optional[str]   # Tenant if present
```

#### 1.3 Canary Runner Design

```python
class CanaryRunner:
    """Daily canary comparing V2 vs V1 vs Golden."""

    async def run_daily_canary(self) -> CanaryReport:
        # 1. Load reference datasets
        # 2. Run V1 simulation
        # 3. Run V2 simulation
        # 4. Compare results
        # 5. Generate diff artifacts
        # 6. Store report

    async def compare_v2_vs_v1(self, plan: List[Dict]) -> DiffResult
    async def compare_v2_vs_golden(self, dataset_id: str) -> DiffResult
```

#### 1.4 Isolation Guarantee

- V2 sandbox writes to separate tables: `costsim_v2_runs`, `costsim_v2_provenance`
- No writes to production `simulation_runs` table
- Feature flag controls routing completely
- Production path unchanged when `COSTSIM_V2_SANDBOX=false`

---

### 2. Drift Detection & Alerts

#### 2.1 New Metrics

```python
# backend/app/costsim/metrics.py

from prometheus_client import Counter, Histogram, Gauge

costsim_runs_total = Counter(
    "costsim_runs_total",
    "Total CostSim runs",
    ["version", "status"]  # version: v1/v2, status: success/error
)

costsim_drift_score = Histogram(
    "costsim_drift_score",
    "Drift score between V1 and V2",
    ["dataset"],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
)

costsim_output_p50 = Gauge(
    "costsim_output_p50",
    "P50 of cost estimates",
    ["version"]
)

costsim_output_p90 = Gauge(
    "costsim_output_p90",
    "P90 of cost estimates",
    ["version"]
)

costsim_runtime_ms = Histogram(
    "costsim_runtime_ms",
    "Simulation runtime in milliseconds",
    ["version"],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000]
)

costsim_schema_errors_total = Counter(
    "costsim_schema_errors_total",
    "Schema validation errors",
    ["version", "error_type"]
)
```

#### 2.2 Alert Rules

```yaml
# monitoring/alerts/costsim-alerts.yml

groups:
  - name: costsim_alerts
    rules:
      # P1: Auto-disable V2 on high drift
      - alert: CostSimV2DriftCritical
        expr: avg(costsim_drift_score{version="v2"}) > 0.2
        for: 5m
        labels:
          severity: critical
          action: auto_disable
        annotations:
          summary: "CostSim V2 drift exceeds threshold"

      # P2: Median shift warning
      - alert: CostSimMedianShift
        expr: |
          abs(costsim_output_p50{version="v2"} - costsim_output_p50{version="v1"})
          / costsim_output_p50{version="v1"} > 0.15
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CostSim median shifted >15%"

      # P3: Schema mismatch
      - alert: CostSimSchemaError
        expr: increase(costsim_schema_errors_total[5m]) > 0
        labels:
          severity: warning
        annotations:
          summary: "CostSim schema validation errors"
```

#### 2.3 Auto-Disable Logic

```python
# backend/app/costsim/circuit_breaker.py

class CostSimCircuitBreaker:
    """Auto-disable V2 on drift detection."""

    DRIFT_THRESHOLD = 0.2
    DISABLE_FILE = "/var/lib/aos/costsim_v2_disabled"

    async def check_and_disable(self, drift_score: float) -> bool:
        if drift_score > self.DRIFT_THRESHOLD:
            await self._disable_v2()
            await self._store_incident()
            return True
        return False

    async def _disable_v2(self):
        # Write disable file
        # Update feature flag
        # Log incident

    async def _store_incident(self):
        # Create incident file with timestamp
        # Store diff artifacts
        # Send alert
```

---

### 3. status_history API

#### 3.1 Database Migration

```sql
-- migrations/versions/m6_001_status_history.py

CREATE TABLE status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_type VARCHAR(64) NOT NULL,      -- 'workflow', 'agent', 'run', etc.
    object_id VARCHAR(255) NOT NULL,
    status_from VARCHAR(64),               -- Previous status (NULL for creation)
    status_to VARCHAR(64) NOT NULL,        -- New status
    metadata JSONB DEFAULT '{}',           -- Additional context
    reason TEXT,                           -- Human-readable reason
    tenant_id VARCHAR(255),                -- Tenant identifier
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by VARCHAR(255),               -- User/system that made change

    -- Indexes for efficient querying
    INDEX idx_status_history_object (object_type, object_id),
    INDEX idx_status_history_tenant (tenant_id, created_at),
    INDEX idx_status_history_created (created_at)
);

-- Immutability: No UPDATE or DELETE allowed
-- Enforced via TRIGGER or RLS
CREATE OR REPLACE FUNCTION prevent_status_history_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'status_history table is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER status_history_immutable
BEFORE UPDATE OR DELETE ON status_history
FOR EACH ROW EXECUTE FUNCTION prevent_status_history_modification();
```

#### 3.2 API Endpoints

```python
# backend/app/api/status_history.py

@router.get("/status-history")
async def get_status_history(
    object_type: Optional[str] = None,
    object_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tenant_id: Optional[str] = None,
    limit: int = Query(100, le=10000),
    offset: int = 0,
    format: str = Query("json", regex="^(json|csv|jsonl)$"),
) -> Response:
    """
    Query status history with filters.

    - Tenant-scoped if tenant_id provided
    - Supports CSV, JSON, JSONL export
    - Paginated for large results
    """

@router.get("/status-history/export")
async def export_status_history(
    object_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tenant_id: Optional[str] = None,
    format: str = Query("csv", regex="^(csv|jsonl)$"),
) -> Response:
    """
    Large export with signed URL.

    - For exports >10k rows
    - Returns signed URL to download
    - Audit logged
    """
```

#### 3.3 Audit Logging

```python
async def log_export_access(
    user_id: str,
    tenant_id: Optional[str],
    filters: Dict[str, Any],
    row_count: int,
    export_format: str,
):
    """Log every status_history export for audit."""
    await status_history_store.append(
        object_type="status_history_export",
        object_id=str(uuid4()),
        status_from=None,
        status_to="exported",
        metadata={
            "filters": filters,
            "row_count": row_count,
            "format": export_format,
            "user_id": user_id,
        },
        tenant_id=tenant_id,
    )
```

---

### 4. Cost Divergence Report

#### 4.1 Endpoint Design

```python
# backend/app/api/costsim.py

@router.get("/costsim/divergence-report")
async def get_divergence_report(
    start_date: datetime,
    end_date: datetime,
    version: str = "v2",
    format: str = Query("json", regex="^(csv|json|jsonl)$"),
    dataset_id: Optional[str] = None,
) -> Response:
    """
    Generate cost divergence report.

    Computes:
    - delta_p50: Difference in median estimates
    - delta_p90: Difference in P90 estimates
    - kl_divergence: KL divergence between distributions
    - outlier_count: Number of outliers (>2 std dev)
    - fail_ratio: Ratio of failed simulations
    - matching_rate: % of results within tolerance
    """
```

#### 4.2 Computation Logic

```python
# backend/app/costsim/divergence.py

@dataclass
class DivergenceReport:
    start_date: datetime
    end_date: datetime
    sample_count: int
    delta_p50: float
    delta_p90: float
    kl_divergence: float
    outlier_count: int
    fail_ratio: float
    matching_rate: float
    detailed_samples: List[Dict]

async def compute_divergence(
    start_date: datetime,
    end_date: datetime,
    version: str = "v2",
) -> DivergenceReport:
    """Compute divergence metrics between V1 and V2."""

    # 1. Fetch paired results from DB
    v1_results = await fetch_v1_results(start_date, end_date)
    v2_results = await fetch_v2_results(start_date, end_date)

    # 2. Align by input hash
    pairs = align_by_input_hash(v1_results, v2_results)

    # 3. Compute statistics
    v1_costs = [p.v1_cost for p in pairs]
    v2_costs = [p.v2_cost for p in pairs]

    delta_p50 = np.percentile(v2_costs, 50) - np.percentile(v1_costs, 50)
    delta_p90 = np.percentile(v2_costs, 90) - np.percentile(v1_costs, 90)

    # KL divergence
    kl_div = compute_kl_divergence(v1_costs, v2_costs)

    # Outliers (beyond 2 std dev)
    diffs = [v2 - v1 for v1, v2 in zip(v1_costs, v2_costs)]
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs)
    outliers = sum(1 for d in diffs if abs(d - mean_diff) > 2 * std_diff)

    # Matching rate (within 10% tolerance)
    matching = sum(1 for v1, v2 in zip(v1_costs, v2_costs)
                   if abs(v2 - v1) / max(v1, 1) < 0.1)

    return DivergenceReport(
        start_date=start_date,
        end_date=end_date,
        sample_count=len(pairs),
        delta_p50=delta_p50,
        delta_p90=delta_p90,
        kl_divergence=kl_div,
        outlier_count=outliers,
        fail_ratio=compute_fail_ratio(pairs),
        matching_rate=matching / len(pairs) if pairs else 0,
        detailed_samples=pairs[:100],
    )
```

---

### 5. Reference Dataset Validation

#### 5.1 Dataset Structure

```
backend/data/reference_datasets/
├── low_variance.json           # Predictable, stable plans
├── high_variance.json          # Plans with high cost variance
├── mixed_city.json             # Geographic diversity
├── noise_injected.json         # Plans with random noise
└── historical_anonymized.json  # Real historical data (anonymized)
```

#### 5.2 Dataset Schema

```python
# backend/app/costsim/datasets.py

@dataclass
class ReferenceDataset:
    id: str
    name: str
    description: str
    plans: List[Dict[str, Any]]
    expected_costs: List[int]          # Ground truth costs
    expected_durations: List[int]      # Ground truth durations
    tolerance_pct: float = 0.1         # Acceptable deviation

@dataclass
class ValidationResult:
    dataset_id: str
    mean_error: float
    median_error: float
    std_deviation: float
    outlier_pct: float
    drift_score: float
    verdict: str  # "acceptable" or "not_acceptable"
    details: Dict[str, Any]
```

#### 5.3 Validation Logic

```python
async def validate_v2_against_dataset(
    dataset: ReferenceDataset,
) -> ValidationResult:
    """Validate V2 against a reference dataset."""

    errors = []
    for plan, expected_cost in zip(dataset.plans, dataset.expected_costs):
        result = await costsim_v2.simulate(plan)
        error = abs(result.estimated_cost_cents - expected_cost)
        errors.append(error)

    mean_error = np.mean(errors)
    median_error = np.median(errors)
    std_dev = np.std(errors)

    # Outliers: errors > mean + 2*std
    outlier_threshold = mean_error + 2 * std_dev
    outliers = sum(1 for e in errors if e > outlier_threshold)
    outlier_pct = outliers / len(errors)

    # Drift score: normalized deviation from expected
    drift_scores = [e / max(exp, 1) for e, exp in zip(errors, dataset.expected_costs)]
    drift_score = np.mean(drift_scores)

    # Verdict
    verdict = "acceptable" if (
        drift_score < 0.15 and
        outlier_pct < 0.05 and
        median_error < dataset.tolerance_pct * np.mean(dataset.expected_costs)
    ) else "not_acceptable"

    return ValidationResult(
        dataset_id=dataset.id,
        mean_error=mean_error,
        median_error=median_error,
        std_deviation=std_dev,
        outlier_pct=outlier_pct,
        drift_score=drift_score,
        verdict=verdict,
        details={"sample_count": len(errors)},
    )
```

---

### 6. M6a Packaging Foundation

#### 6.1 Helm Chart Structure

```
helm/aos/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   └── costsim-sandbox/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
└── charts/
```

#### 6.2 K8s Manifests Updates

```yaml
# k8s/backend-deployment.yaml - Add probes
spec:
  template:
    spec:
      containers:
        - name: backend
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
```

#### 6.3 Sandbox Namespace

```yaml
# k8s/costsim-sandbox-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aos-costsim-sandbox
  labels:
    environment: sandbox
    component: costsim-v2
```

---

### 7. M6b Isolation Preparation

#### 7.1 Tenant Context Propagation

```python
# backend/app/middleware/tenant.py

class TenantContext:
    """Thread-local tenant context."""

    _context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "tenant_id", default=None
    )

    @classmethod
    def get(cls) -> Optional[str]:
        return cls._context.get()

    @classmethod
    def set(cls, tenant_id: str):
        cls._context.set(tenant_id)

async def tenant_middleware(request: Request, call_next):
    """Extract tenant from header and set context."""
    tenant_id = request.headers.get("X-Tenant-ID")
    TenantContext.set(tenant_id)
    response = await call_next(request)
    return response
```

#### 7.2 Tenant-Aware Queries

```python
# All status_history queries MUST filter by tenant

async def query_status_history(
    filters: Dict[str, Any],
    tenant_id: Optional[str] = None,
) -> List[StatusHistoryRecord]:
    """Query with mandatory tenant scoping."""

    query = select(StatusHistory)

    # ALWAYS apply tenant filter if present
    if tenant_id:
        query = query.where(StatusHistory.tenant_id == tenant_id)

    # Apply other filters...
    return await session.execute(query)
```

#### 7.3 Cross-Tenant Leak Prevention

```python
# backend/app/costsim/isolation.py

class TenantIsolationChecker:
    """Verify no cross-tenant data leakage."""

    async def verify_query_isolation(
        self,
        query_result: List[Any],
        expected_tenant: str,
    ) -> bool:
        """Verify all results belong to expected tenant."""
        for record in query_result:
            if hasattr(record, 'tenant_id'):
                if record.tenant_id != expected_tenant:
                    logger.error(
                        f"Cross-tenant leak detected: "
                        f"expected {expected_tenant}, got {record.tenant_id}"
                    )
                    return False
        return True
```

---

## Implementation Order

| Phase | Component | Duration | Dependencies |
|-------|-----------|----------|--------------|
| 1 | Database migrations | Day 1 | None |
| 2 | CostSim V2 core + provenance | Days 2-4 | Migrations |
| 3 | Drift metrics & alerts | Days 5-6 | V2 core |
| 4 | status_history API | Days 7-9 | Migrations |
| 5 | Divergence reporting | Days 10-11 | V2 + metrics |
| 6 | Reference datasets | Days 12-14 | V2 core |
| 7 | Canary runner | Days 15-17 | All above |
| 8 | Packaging (Helm/K8s) | Days 18-19 | All above |
| 9 | Tenant isolation | Days 20-21 | status_history |
| 10 | Exit tests & validation | Days 22-25 | All above |

---

## Exit Criteria Checklist

- [x] CostSim V2 adapter implemented and sandboxed
- [x] Provenance logging complete
- [x] Canary runner operational
- [x] All 6 drift metrics exposed
- [x] P1/P2/P3 alerts configured
- [x] Auto-disable on drift working
- [x] status_history table created (immutable)
- [x] GET /status-history endpoint working
- [x] CSV/JSONL export working
- [x] Signed URL export working
- [x] Export audit logging working
- [x] GET /costsim/divergence-report working
- [x] All 5 reference datasets created
- [x] Dataset validation passing
- [x] Helm chart skeleton created
- [x] K8s manifests with probes
- [x] Sandbox namespace configured
- [x] Tenant context propagation working
- [x] Tenant-scoped queries implemented
- [x] Cross-tenant leak tests passing
- [x] Zero regressions vs M5
- [x] All M6 tests passing

**All exit criteria verified - see PIN-026 for implementation details.**

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-04 | **IMPLEMENTATION COMPLETE** - All exit criteria verified |
| 2025-12-04 | Created M6 implementation plan per authoritative specification |
