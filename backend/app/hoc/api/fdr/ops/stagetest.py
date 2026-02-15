# Layer: L2 — Product APIs
# AUDIENCE: FOUNDER
# Product: ops-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Stagetest evidence console — read-only endpoints for test artifacts
# Callers: Stagetest Evidence Console UI (founder)
# Allowed Imports: L5 (engines), L5 (schemas)
# Forbidden Imports: L1, L6, sqlalchemy
# artifact_class: CODE
"""
Stagetest Evidence Console API — Read-Only Founder Endpoints

Canonical prefix: /hoc/api/stagetest/*
Legacy v1 prefix is FORBIDDEN — see stagetest_route_prefix_guard.py.

Endpoints:
- GET /hoc/api/stagetest/runs            — List all test runs
- GET /hoc/api/stagetest/runs/{run_id}   — Get run summary
- GET /hoc/api/stagetest/runs/{run_id}/cases         — List cases for run
- GET /hoc/api/stagetest/runs/{run_id}/cases/{case_id} — Get case detail
- GET /hoc/api/stagetest/apis            — Get API endpoint snapshot

Architecture:
- L2 is thin HTTP boundary — no filesystem I/O here
- All reads delegate to L5 stagetest_read_engine
- Founder auth enforced via verify_fops_token
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.console_auth import verify_fops_token
from app.hoc.fdr.ops.engines.stagetest_read_engine import (
    get_apis_snapshot,
    get_case,
    get_run,
    list_cases,
    list_runs,
)
from app.hoc.fdr.ops.schemas.stagetest import (
    ApisSnapshotResponse,
    CaseDetail,
    CaseListResponse,
    CaseSummary,
    RunListResponse,
    RunSummary,
)

logger = logging.getLogger("nova.api.stagetest")

router = APIRouter(
    prefix="/hoc/api/stagetest",
    tags=["Stagetest Evidence Console"],
    dependencies=[Depends(verify_fops_token)],
)


@router.get("/runs", response_model=RunListResponse)
async def stagetest_list_runs():
    """GET /hoc/api/stagetest/runs — List all test runs."""
    runs = list_runs()
    return RunListResponse(
        runs=[RunSummary(**r) for r in runs],
        total=len(runs),
    )


@router.get("/runs/{run_id}", response_model=RunSummary)
async def stagetest_get_run(run_id: str):
    """GET /hoc/api/stagetest/runs/{run_id} — Get run summary."""
    data = get_run(run_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return RunSummary(**data)


@router.get("/runs/{run_id}/cases", response_model=CaseListResponse)
async def stagetest_list_cases(run_id: str):
    """GET /hoc/api/stagetest/runs/{run_id}/cases — List cases for run."""
    run_data = get_run(run_id)
    if run_data is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    cases = list_cases(run_id)
    return CaseListResponse(
        run_id=run_id,
        cases=[CaseSummary(**c) for c in cases],
        total=len(cases),
    )


@router.get("/runs/{run_id}/cases/{case_id}", response_model=CaseDetail)
async def stagetest_get_case(run_id: str, case_id: str):
    """GET /hoc/api/stagetest/runs/{run_id}/cases/{case_id} — Get case detail."""
    data = get_case(run_id, case_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {run_id}/{case_id}")
    return CaseDetail(**data)


@router.get("/apis", response_model=ApisSnapshotResponse)
async def stagetest_list_apis():
    """GET /hoc/api/stagetest/apis — Get API endpoint snapshot."""
    data = get_apis_snapshot()
    if data is None:
        # Return default snapshot if no artifacts exist yet
        return ApisSnapshotResponse(
            run_id="none",
            generated_at="",
            endpoints=[],
        )
    return ApisSnapshotResponse(**data)
