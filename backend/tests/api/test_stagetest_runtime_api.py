# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Runtime API tests for stagetest endpoints using FastAPI TestClient + seeded fixtures
# artifact_class: TEST
"""
Stagetest Runtime API Tests

Validates all 5 stagetest endpoints against a seeded fixture directory:
- GET /hoc/api/stagetest/runs            → 200 with run list
- GET /hoc/api/stagetest/runs/{run_id}   → 200 with run summary
- GET /hoc/api/stagetest/runs/{run_id}/cases → 200 with case list
- GET /hoc/api/stagetest/runs/{run_id}/cases/{case_id} → 200 with case detail
- GET /hoc/api/stagetest/apis            → 200 with API snapshot
- 404 cases for missing runs/cases
"""

import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# -------------------------------------------------------------------------
# Seed fixture data
# -------------------------------------------------------------------------
RUN_ID = "20260215T999999Z"
CASE_ID = "TC-RUNTIME-001"
UC_ID = "UC-002"
STAGE = "1.2"
OP_NAME = "account.onboarding.advance"


def _make_determinism_hash(case_id, uc_id, stage, op, syn_in, obs_out, assertions):
    payload = {
        "case_id": case_id,
        "uc_id": uc_id,
        "stage": stage,
        "operation_name": op,
        "synthetic_input": syn_in,
        "observed_output": obs_out,
        "assertions": assertions,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


SYNTHETIC_INPUT = {"tenant_id": "test-001", "step": "api-key"}
OBSERVED_OUTPUT = {"status": "PASS", "progress": 100}
ASSERTIONS = [{"id": "A-1", "status": "PASS", "message": "OK"}]
DET_HASH = _make_determinism_hash(CASE_ID, UC_ID, STAGE, OP_NAME, SYNTHETIC_INPUT, OBSERVED_OUTPUT, ASSERTIONS)

API_CALLS_USED = [
    {"method": "POST", "path": "/hoc/api/cus/onboarding/advance", "operation": "account.onboarding.advance", "status_code": 200, "duration_ms": 45},
]

CASE_DATA = {
    "run_id": RUN_ID,
    "case_id": CASE_ID,
    "uc_id": UC_ID,
    "stage": STAGE,
    "operation_name": OP_NAME,
    "route_path": "/hoc/api/cus/onboarding/advance",
    "api_method": "POST",
    "request_fields": {"tenant_id": "string", "step": "string"},
    "response_fields": {"status": "string", "progress": "number"},
    "synthetic_input": SYNTHETIC_INPUT,
    "observed_output": OBSERVED_OUTPUT,
    "assertions": ASSERTIONS,
    "status": "PASS",
    "determinism_hash": DET_HASH,
    "signature": "UNSIGNED_LOCAL",
    "evidence_files": [],
    "api_calls_used": API_CALLS_USED,
}

ALL_HASHES = sorted([DET_HASH])
DET_DIGEST = hashlib.sha256("|".join(ALL_HASHES).encode()).hexdigest()

RUN_SUMMARY = {
    "run_id": RUN_ID,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "stages_executed": [STAGE],
    "total_cases": 1,
    "pass_count": 1,
    "fail_count": 0,
    "determinism_digest": DET_DIGEST,
    "artifact_version": "1.0.0",
}

APIS_SNAPSHOT = {
    "run_id": RUN_ID,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "endpoints": [
        {"method": "GET", "path": "/hoc/api/stagetest/runs", "operation": "stagetest.list_runs"},
    ],
}


@pytest.fixture(scope="module")
def seeded_dir():
    """Create a temp directory with seeded stagetest artifacts."""
    tmp = tempfile.mkdtemp(prefix="stagetest_runtime_")
    run_dir = Path(tmp) / RUN_ID
    cases_dir = run_dir / "cases"
    cases_dir.mkdir(parents=True)

    (run_dir / "run_summary.json").write_text(json.dumps(RUN_SUMMARY, indent=2))
    (run_dir / "apis_snapshot.json").write_text(json.dumps(APIS_SNAPSHOT, indent=2))
    (cases_dir / f"{CASE_ID}.json").write_text(json.dumps(CASE_DATA, indent=2))

    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="module")
def client(seeded_dir):
    """Create a TestClient with auth override and patched ARTIFACTS_ROOT."""
    # Patch ARTIFACTS_ROOT in the read engine to point to our seeded dir
    with patch("app.hoc.fdr.ops.engines.stagetest_read_engine.ARTIFACTS_ROOT", seeded_dir):
        from app.hoc.api.fdr.ops.stagetest import router

        app = FastAPI()
        # Override auth dependency
        app.dependency_overrides = {}
        app.include_router(router)

        # Override the auth dependency globally on the app
        from app.auth.console_auth import verify_fops_token
        app.dependency_overrides[verify_fops_token] = lambda: {"role": "founder"}

        yield TestClient(app)


class TestStagetestRuntimeAPI:
    """Runtime tests against seeded fixture data."""

    def test_list_runs_returns_200(self, client):
        """GET /runs returns 200 with at least one run."""
        resp = client.get("/hoc/api/stagetest/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any(r["run_id"] == RUN_ID for r in data["runs"])

    def test_get_run_returns_200(self, client):
        """GET /runs/{run_id} returns 200 with correct summary."""
        resp = client.get(f"/hoc/api/stagetest/runs/{RUN_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == RUN_ID
        assert data["total_cases"] == 1

    def test_get_run_404_for_missing(self, client):
        """GET /runs/{run_id} returns 404 for non-existent run."""
        resp = client.get("/hoc/api/stagetest/runs/NONEXISTENT")
        assert resp.status_code == 404

    def test_list_cases_returns_200(self, client):
        """GET /runs/{run_id}/cases returns 200 with cases."""
        resp = client.get(f"/hoc/api/stagetest/runs/{RUN_ID}/cases")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == RUN_ID
        assert data["total"] == 1
        assert data["cases"][0]["case_id"] == CASE_ID

    def test_list_cases_404_for_missing_run(self, client):
        """GET /runs/{run_id}/cases returns 404 for non-existent run."""
        resp = client.get("/hoc/api/stagetest/runs/NONEXISTENT/cases")
        assert resp.status_code == 404

    def test_get_case_returns_200(self, client):
        """GET /runs/{run_id}/cases/{case_id} returns 200 with full detail."""
        resp = client.get(f"/hoc/api/stagetest/runs/{RUN_ID}/cases/{CASE_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_id"] == CASE_ID
        assert data["route_path"] == "/hoc/api/cus/onboarding/advance"
        assert data["api_method"] == "POST"
        assert data["request_fields"] == {"tenant_id": "string", "step": "string"}
        assert data["response_fields"] == {"status": "string", "progress": "number"}
        assert data["determinism_hash"] == DET_HASH

    def test_get_case_404_for_missing(self, client):
        """GET /runs/{run_id}/cases/{case_id} returns 404 for non-existent case."""
        resp = client.get(f"/hoc/api/stagetest/runs/{RUN_ID}/cases/NONEXISTENT")
        assert resp.status_code == 404

    def test_apis_snapshot_returns_200(self, client):
        """GET /apis returns 200 with endpoint snapshot."""
        resp = client.get("/hoc/api/stagetest/apis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == RUN_ID
        assert len(data["endpoints"]) >= 1

    def test_case_detail_has_stage_12_fields(self, client):
        """Stage 1.2 case has non-empty request/response fields, valid route."""
        resp = client.get(f"/hoc/api/stagetest/runs/{RUN_ID}/cases/{CASE_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage"] == "1.2"
        assert data["request_fields"], "request_fields must be non-empty for stage 1.2"
        assert data["response_fields"], "response_fields must be non-empty for stage 1.2"
        assert data["route_path"] not in ("N/A", "", None)
        assert data["api_method"] not in ("N/A", "", None)

    def test_case_detail_has_api_calls_used(self, client):
        """Stage 1.2 case has non-empty api_calls_used with required fields."""
        resp = client.get(f"/hoc/api/stagetest/runs/{RUN_ID}/cases/{CASE_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert "api_calls_used" in data, "api_calls_used field must be present"
        calls = data["api_calls_used"]
        assert len(calls) >= 1, "api_calls_used must have at least one entry"
        for call in calls:
            assert "method" in call, "api_calls_used entry must have method"
            assert "path" in call, "api_calls_used entry must have path"
            assert "operation" in call, "api_calls_used entry must have operation"
            assert "status_code" in call, "api_calls_used entry must have status_code"
            assert "duration_ms" in call, "api_calls_used entry must have duration_ms"
        # Verify first call matches seeded data
        assert calls[0]["method"] == "POST"
        assert calls[0]["path"] == "/hoc/api/cus/onboarding/advance"
        assert calls[0]["status_code"] == 200
