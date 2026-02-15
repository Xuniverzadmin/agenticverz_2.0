# Layer: L5 — Schemas
# AUDIENCE: FOUNDER
# Role: Response/request schemas for stagetest evidence API
# artifact_class: CODE
"""
Stagetest Evidence API Schemas

Pydantic response models for /hoc/api/stagetest/* endpoints.
Read-only — no write schemas needed.
"""

from __future__ import annotations

from pydantic import BaseModel


class AssertionItem(BaseModel):
    id: str
    status: str
    message: str


class CaseSummary(BaseModel):
    case_id: str
    uc_id: str
    stage: str
    operation_name: str
    status: str
    determinism_hash: str


class CaseDetail(BaseModel):
    run_id: str
    case_id: str
    uc_id: str
    stage: str
    operation_name: str
    route_path: str
    api_method: str
    request_fields: dict
    response_fields: dict
    synthetic_input: dict
    observed_output: dict
    assertions: list[AssertionItem]
    status: str
    determinism_hash: str
    signature: str
    evidence_files: list[str]


class RunSummary(BaseModel):
    run_id: str
    created_at: str
    stages_executed: list[str]
    total_cases: int
    pass_count: int
    fail_count: int
    determinism_digest: str
    artifact_version: str


class RunListResponse(BaseModel):
    runs: list[RunSummary]
    total: int


class CaseListResponse(BaseModel):
    run_id: str
    cases: list[CaseSummary]
    total: int


class ApiEndpoint(BaseModel):
    method: str
    path: str
    operation: str


class ApisSnapshotResponse(BaseModel):
    run_id: str
    generated_at: str
    endpoints: list[ApiEndpoint]
