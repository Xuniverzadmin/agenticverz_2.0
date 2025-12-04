# CostSim V2 API (M6)
"""
API endpoints for CostSim V2 sandbox.

Endpoints:
- POST /costsim/v2/simulate - Run V2 simulation (sandbox mode)
- GET /costsim/v2/status - Get V2 sandbox status
- POST /costsim/v2/reset - Reset circuit breaker
- GET /costsim/divergence - Get divergence report
- POST /costsim/canary/run - Trigger canary run
- GET /costsim/canary/reports - Get canary reports
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.db import get_session
from app.costsim import (
    is_v2_sandbox_enabled,
    is_v2_disabled_by_drift,
    simulate_with_sandbox,
    simulate_v2_with_comparison,
    get_circuit_breaker,
    run_canary,
    CanaryRunConfig,
)
from app.costsim.config import get_config
from app.costsim.divergence import generate_divergence_report
from app.costsim.models import V2SimulationStatus, ComparisonVerdict

logger = logging.getLogger("nova.api.costsim")

router = APIRouter(prefix="/costsim", tags=["costsim"])


# Request/Response Models
class SimulationStep(BaseModel):
    """A single step in a simulation plan."""

    skill: str = Field(..., description="Skill ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="Skill parameters")


class SimulateRequest(BaseModel):
    """Request for V2 simulation."""

    plan: List[SimulationStep] = Field(..., description="Plan steps to simulate")
    budget_cents: int = Field(1000, ge=0, description="Available budget in cents")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    run_id: Optional[str] = Field(None, description="Run identifier")


class SimulationStepResult(BaseModel):
    """Result for a single step."""

    step_index: int
    skill_id: str
    cost_cents: float
    latency_ms: float
    confidence: float


class V2SimulationResponse(BaseModel):
    """Response from V2 simulation."""

    feasible: bool
    status: str
    estimated_cost_cents: int
    estimated_duration_ms: int
    budget_remaining_cents: int
    confidence_score: float
    model_version: str
    step_estimates: List[SimulationStepResult]
    risks: List[Dict[str, Any]]
    warnings: List[str]
    runtime_ms: int


class ComparisonResponse(BaseModel):
    """Comparison between V1 and V2."""

    verdict: str
    v1_cost_cents: int
    v2_cost_cents: int
    cost_delta_cents: int
    cost_delta_pct: float
    drift_score: float
    feasibility_match: bool


class SandboxSimulateResponse(BaseModel):
    """Response from sandbox simulation."""

    # V1 result (production)
    v1_feasible: bool
    v1_cost_cents: int
    v1_duration_ms: int

    # V2 result (if sandbox enabled)
    v2_result: Optional[V2SimulationResponse] = None
    comparison: Optional[ComparisonResponse] = None

    # Sandbox status
    sandbox_enabled: bool
    v2_error: Optional[str] = None


class SandboxStatusResponse(BaseModel):
    """Status of V2 sandbox."""

    sandbox_enabled: bool
    circuit_breaker_open: bool
    disabled_by_drift: bool
    model_version: str
    adapter_version: str
    drift_threshold: float


class DivergenceReportResponse(BaseModel):
    """Divergence report response."""

    start_date: datetime
    end_date: datetime
    version: str
    sample_count: int
    delta_p50: float
    delta_p90: float
    kl_divergence: float
    outlier_count: int
    fail_ratio: float
    matching_rate: float
    detailed_samples: List[Dict[str, Any]]


class CanaryRunResponse(BaseModel):
    """Canary run response."""

    run_id: str
    status: str
    passed: bool
    total_samples: int
    matching_samples: int
    kl_divergence: float
    failure_reasons: List[str]
    artifact_paths: List[str]


# API Endpoints
@router.get("/v2/status", response_model=SandboxStatusResponse)
async def get_sandbox_status():
    """
    Get current V2 sandbox status.

    Returns information about:
    - Whether sandbox is enabled (feature flag)
    - Whether circuit breaker is open (auto-disabled due to drift)
    - Current model version
    - Drift thresholds
    """
    config = get_config()
    circuit_breaker = get_circuit_breaker()

    # Use async method since we're in an async endpoint
    circuit_breaker_open = await circuit_breaker.is_disabled()

    return SandboxStatusResponse(
        sandbox_enabled=is_v2_sandbox_enabled(),
        circuit_breaker_open=circuit_breaker_open,
        disabled_by_drift=is_v2_disabled_by_drift(),
        model_version=config.model_version,
        adapter_version=config.adapter_version,
        drift_threshold=config.drift_threshold,
    )


@router.post("/v2/simulate", response_model=SandboxSimulateResponse)
async def simulate_v2(request: SimulateRequest):
    """
    Run simulation through V2 sandbox.

    This endpoint always runs V1 for production results.
    If sandbox is enabled, also runs V2 in shadow mode
    and returns comparison metrics.

    The V1 result is always the authoritative result.
    V2 is for validation only.
    """
    # Convert request to plan format
    plan = [
        {"skill": step.skill, "params": step.params}
        for step in request.plan
    ]

    # Run through sandbox
    result = await simulate_with_sandbox(
        plan=plan,
        budget_cents=request.budget_cents,
        tenant_id=request.tenant_id,
        run_id=request.run_id,
    )

    # Build response
    response = SandboxSimulateResponse(
        v1_feasible=result.v1_result.feasible,
        v1_cost_cents=result.v1_result.estimated_cost_cents,
        v1_duration_ms=result.v1_result.estimated_duration_ms,
        sandbox_enabled=result.sandbox_enabled,
        v2_error=result.v2_error,
    )

    # Add V2 result if available
    if result.v2_result:
        response.v2_result = V2SimulationResponse(
            feasible=result.v2_result.feasible,
            status=result.v2_result.status.value,
            estimated_cost_cents=result.v2_result.estimated_cost_cents,
            estimated_duration_ms=result.v2_result.estimated_duration_ms,
            budget_remaining_cents=result.v2_result.budget_remaining_cents,
            confidence_score=result.v2_result.confidence_score,
            model_version=result.v2_result.model_version,
            step_estimates=[
                SimulationStepResult(
                    step_index=e["step_index"],
                    skill_id=e["skill_id"],
                    cost_cents=e["cost_cents"],
                    latency_ms=e["latency_ms"],
                    confidence=e["confidence"],
                )
                for e in result.v2_result.step_estimates
            ],
            risks=result.v2_result.risks,
            warnings=result.v2_result.warnings,
            runtime_ms=result.v2_result.runtime_ms,
        )

    # Add comparison if available
    if result.comparison:
        response.comparison = ComparisonResponse(
            verdict=result.comparison.verdict.value,
            v1_cost_cents=result.comparison.v1_cost_cents,
            v2_cost_cents=result.comparison.v2_cost_cents,
            cost_delta_cents=result.comparison.cost_delta_cents,
            cost_delta_pct=result.comparison.cost_delta_pct,
            drift_score=result.comparison.drift_score,
            feasibility_match=result.comparison.feasibility_match,
        )

    return response


@router.post("/v2/reset")
async def reset_circuit_breaker(
    reason: Optional[str] = Query(None, description="Reason for reset"),
):
    """
    Reset the V2 circuit breaker.

    This re-enables V2 sandbox after it was auto-disabled due to drift.
    Should only be called after investigating and fixing the drift cause.

    Returns success status and updated circuit breaker state.
    """
    circuit_breaker = get_circuit_breaker()

    # Use async methods in async endpoint
    is_disabled = await circuit_breaker.is_disabled()
    if not is_disabled:
        state = await circuit_breaker.get_state()
        return {
            "success": True,
            "message": "Circuit breaker was already closed",
            "state": state.to_dict(),
        }

    success = await circuit_breaker.reset_v2(reason=reason or "Manual reset via API")

    state = await circuit_breaker.get_state()
    return {
        "success": success,
        "message": "Circuit breaker reset" if success else "Failed to reset",
        "state": state.to_dict(),
    }


@router.get("/v2/incidents")
async def get_incidents(
    include_resolved: bool = Query(False, description="Include resolved incidents"),
    limit: int = Query(10, ge=1, le=100, description="Max incidents to return"),
):
    """
    Get circuit breaker incidents.

    Returns recent incidents that caused circuit breaker trips.
    Useful for investigating drift causes.
    """
    circuit_breaker = get_circuit_breaker()
    incidents = circuit_breaker.get_incidents(
        include_resolved=include_resolved,
        limit=limit,
    )

    return {
        "incidents": [i.to_dict() for i in incidents],
        "total": len(incidents),
    }


@router.get("/divergence", response_model=DivergenceReportResponse)
async def get_divergence_report(
    start_date: Optional[datetime] = Query(None, description="Start of analysis period"),
    end_date: Optional[datetime] = Query(None, description="End of analysis period"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    days: int = Query(7, ge=1, le=90, description="Days to analyze (if start_date not provided)"),
):
    """
    Get cost divergence report between V1 and V2.

    Returns metrics:
    - delta_p50: Median cost delta
    - delta_p90: 90th percentile cost delta
    - kl_divergence: KL divergence between distributions
    - outlier_count: Number of outlier samples
    - fail_ratio: Ratio of major drift samples
    - matching_rate: Ratio of matching samples
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(days=days)

    report = await generate_divergence_report(
        start_date=start_date,
        end_date=end_date,
        tenant_id=tenant_id,
    )

    return DivergenceReportResponse(
        start_date=report.start_date,
        end_date=report.end_date,
        version=report.version,
        sample_count=report.sample_count,
        delta_p50=report.delta_p50,
        delta_p90=report.delta_p90,
        kl_divergence=report.kl_divergence,
        outlier_count=report.outlier_count,
        fail_ratio=report.fail_ratio,
        matching_rate=report.matching_rate,
        detailed_samples=report.detailed_samples,
    )


@router.post("/canary/run", response_model=CanaryRunResponse)
async def trigger_canary_run(
    sample_count: int = Query(100, ge=10, le=1000, description="Number of samples"),
    drift_threshold: float = Query(0.2, ge=0.0, le=1.0, description="Drift threshold"),
):
    """
    Trigger a canary run on-demand.

    The canary run:
    1. Loads samples from recent provenance logs
    2. Runs both V1 and V2 on each sample
    3. Computes drift metrics
    4. Returns pass/fail verdict

    Note: Daily canary runs are automatic via systemd timer.
    This endpoint is for manual testing.
    """
    report = await run_canary(
        sample_count=sample_count,
        drift_threshold=drift_threshold,
    )

    return CanaryRunResponse(
        run_id=report.run_id,
        status=report.status,
        passed=report.passed,
        total_samples=report.total_samples,
        matching_samples=report.matching_samples,
        kl_divergence=report.kl_divergence,
        failure_reasons=report.failure_reasons,
        artifact_paths=report.artifact_paths,
    )


@router.get("/canary/reports")
async def get_canary_reports(
    limit: int = Query(10, ge=1, le=100, description="Max reports to return"),
):
    """
    Get recent canary run reports.

    Returns summaries of recent canary runs.
    Full artifacts are available at the artifact_paths.
    """
    # TODO: Implement canary report storage and retrieval
    return {
        "reports": [],
        "message": "Canary report retrieval not yet implemented",
    }


# ============== Dataset Validation Endpoints ==============

from app.costsim.datasets import get_dataset_validator, validate_dataset as validate_ds, validate_all_datasets


class DatasetInfo(BaseModel):
    """Dataset information."""

    id: str
    name: str
    description: str
    sample_count: int
    thresholds: Dict[str, float]


class ValidationResultResponse(BaseModel):
    """Validation result response."""

    dataset_id: str
    dataset_name: str
    sample_count: int
    mean_error: float
    median_error: float
    std_deviation: float
    outlier_pct: float
    drift_score: float
    verdict: str
    details: Dict[str, Any]
    timestamp: datetime


@router.get("/datasets", response_model=List[DatasetInfo])
async def list_datasets():
    """
    List all available reference datasets.

    Reference datasets are used to validate V2 accuracy:
    - low_variance: Simple, predictable plans
    - high_variance: Complex, variable plans
    - mixed_city: Real-world mixed workloads
    - noise_injected: Edge cases and invalid inputs
    - historical: Real production patterns
    """
    validator = get_dataset_validator()
    datasets = validator.list_datasets()
    return [
        DatasetInfo(
            id=ds["id"],
            name=ds["name"],
            description=ds["description"],
            sample_count=ds["sample_count"],
            thresholds=ds["thresholds"],
        )
        for ds in datasets
    ]


@router.get("/datasets/{dataset_id}")
async def get_dataset_info(dataset_id: str):
    """Get information about a specific dataset."""
    validator = get_dataset_validator()
    dataset = validator.get_dataset(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")

    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "sample_count": len(dataset.samples),
        "thresholds": dataset.validation_thresholds,
        "sample_tags": list(set(tag for sample in dataset.samples for tag in sample.tags)),
    }


@router.post("/datasets/{dataset_id}/validate", response_model=ValidationResultResponse)
async def validate_against_dataset(dataset_id: str):
    """
    Validate V2 against a specific reference dataset.

    Runs V2 on all samples in the dataset and compares
    against expected values. Returns metrics and verdict.

    Verdict is "acceptable" if all metrics are within thresholds.
    """
    try:
        result = await validate_ds(dataset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ValidationResultResponse(
        dataset_id=result.dataset_id,
        dataset_name=result.dataset_name,
        sample_count=result.sample_count,
        mean_error=result.mean_error,
        median_error=result.median_error,
        std_deviation=result.std_deviation,
        outlier_pct=result.outlier_pct,
        drift_score=result.drift_score,
        verdict=result.verdict,
        details=result.details,
        timestamp=result.timestamp,
    )


@router.post("/datasets/validate-all")
async def validate_all():
    """
    Validate V2 against ALL reference datasets.

    This is a comprehensive validation that runs all 5 datasets.
    Use for pre-release validation or debugging.
    """
    results = await validate_all_datasets()

    all_passed = all(r.verdict == "acceptable" for r in results.values())

    return {
        "all_passed": all_passed,
        "results": {
            dataset_id: {
                "dataset_name": result.dataset_name,
                "sample_count": result.sample_count,
                "mean_error": result.mean_error,
                "drift_score": result.drift_score,
                "verdict": result.verdict,
            }
            for dataset_id, result in results.items()
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
