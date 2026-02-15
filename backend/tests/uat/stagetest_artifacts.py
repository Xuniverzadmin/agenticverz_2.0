# Layer: L4 — Test Utility
# AUDIENCE: INTERNAL
# Role: Stagetest artifact emitter — produces evidence JSON files during test runs
# artifact_class: CODE
"""
Stagetest Artifact Emitter

Provides helpers for Stage 1.1/1.2 tests to emit structured case artifacts
with determinism hashes, enabling the evidence console to display machine-backed
test claims.

Usage:
    from stagetest_artifacts import StagetestEmitter

    emitter = StagetestEmitter()
    emitter.emit_case(
        case_id="TC-S12-001-scenario-1",
        uc_id="UC-002",
        stage="1.2",
        operation_name="account.onboarding.advance",
        route_path="/onboarding/advance/api-key",
        api_method="POST",
        request_fields={"tenant_id": "string", "step": "string"},
        response_fields={"status": "string", "progress": "number"},
        synthetic_input={"tenant_id": "test-001", "step": "api-key"},
        observed_output={"status": "PASS"},
        assertions=[{"id": "A1", "status": "PASS", "message": "Step advanced"}],
    )
    emitter.finalize()  # writes run_summary.json + apis_snapshot.json
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path


ARTIFACTS_ROOT = Path(__file__).resolve().parent.parent.parent / "artifacts" / "stagetest"


def _compute_determinism_hash(payload: dict) -> str:
    """SHA-256 of canonical JSON representation."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class StagetestEmitter:
    """Emits stagetest artifact files for a single test run."""

    def __init__(self, run_id: str | None = None):
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_dir = ARTIFACTS_ROOT / self.run_id
        self.cases_dir = self.run_dir / "cases"
        self.cases_dir.mkdir(parents=True, exist_ok=True)
        self.cases: list[dict] = []
        self.stages_executed: set[str] = set()
        self._start_time = time.monotonic()

    def emit_case(
        self,
        case_id: str,
        uc_id: str,
        stage: str,
        operation_name: str,
        route_path: str = "N/A",
        api_method: str = "N/A",
        request_fields: dict | None = None,
        response_fields: dict | None = None,
        synthetic_input: dict | None = None,
        observed_output: dict | None = None,
        assertions: list[dict] | None = None,
        status: str = "PASS",
        evidence_files: list[str] | None = None,
        api_calls_used: list[dict] | None = None,
    ) -> dict:
        """Emit a single case artifact file and return the case data."""
        request_fields = request_fields or {}
        response_fields = response_fields or {}
        synthetic_input = synthetic_input or {}
        observed_output = observed_output or {}
        assertions = assertions or []
        evidence_files = evidence_files or []
        api_calls_used = api_calls_used or []

        # Compute determinism hash over the canonical payload
        hash_payload = {
            "case_id": case_id,
            "uc_id": uc_id,
            "stage": stage,
            "operation_name": operation_name,
            "synthetic_input": synthetic_input,
            "observed_output": observed_output,
            "assertions": assertions,
        }
        determinism_hash = _compute_determinism_hash(hash_payload)

        case_data = {
            "run_id": self.run_id,
            "case_id": case_id,
            "uc_id": uc_id,
            "stage": stage,
            "operation_name": operation_name,
            "route_path": route_path,
            "api_method": api_method,
            "request_fields": request_fields,
            "response_fields": response_fields,
            "synthetic_input": synthetic_input,
            "observed_output": observed_output,
            "assertions": assertions,
            "status": status,
            "determinism_hash": determinism_hash,
            "signature": "UNSIGNED_LOCAL",
            "evidence_files": evidence_files,
            "api_calls_used": api_calls_used,
        }

        # Write case file
        case_file = self.cases_dir / f"{case_id}.json"
        case_file.write_text(json.dumps(case_data, indent=2) + "\n")

        self.cases.append(case_data)
        self.stages_executed.add(stage)
        return case_data

    def emit_apis_snapshot(self, apis: list[dict] | None = None) -> dict:
        """Emit apis_snapshot.json from route-operation manifest."""
        if apis is None:
            # Generate from the stagetest endpoints
            apis = [
                {"method": "GET", "path": "/hoc/api/stagetest/runs", "operation": "stagetest.list_runs"},
                {"method": "GET", "path": "/hoc/api/stagetest/runs/{run_id}", "operation": "stagetest.get_run"},
                {"method": "GET", "path": "/hoc/api/stagetest/runs/{run_id}/cases", "operation": "stagetest.list_cases"},
                {"method": "GET", "path": "/hoc/api/stagetest/runs/{run_id}/cases/{case_id}", "operation": "stagetest.get_case"},
                {"method": "GET", "path": "/hoc/api/stagetest/apis", "operation": "stagetest.list_apis"},
            ]

        snapshot = {
            "run_id": self.run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "endpoints": apis,
        }

        snapshot_file = self.run_dir / "apis_snapshot.json"
        snapshot_file.write_text(json.dumps(snapshot, indent=2) + "\n")
        return snapshot

    def finalize(self) -> dict:
        """Write run_summary.json and apis_snapshot.json, return summary."""
        pass_count = sum(1 for c in self.cases if c["status"] == "PASS")
        fail_count = sum(1 for c in self.cases if c["status"] == "FAIL")

        # Compute aggregate determinism digest
        all_hashes = sorted(c["determinism_hash"] for c in self.cases)
        digest_input = "|".join(all_hashes)
        determinism_digest = hashlib.sha256(digest_input.encode()).hexdigest()

        summary = {
            "run_id": self.run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "stages_executed": sorted(self.stages_executed),
            "total_cases": len(self.cases),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "determinism_digest": determinism_digest,
            "artifact_version": "1.0.0",
        }

        summary_file = self.run_dir / "run_summary.json"
        summary_file.write_text(json.dumps(summary, indent=2) + "\n")

        # Also emit apis snapshot
        self.emit_apis_snapshot()

        return summary


def get_latest_run_dir() -> Path | None:
    """Return the most recently created run directory, or None."""
    if not ARTIFACTS_ROOT.exists():
        return None
    runs = sorted(
        [d for d in ARTIFACTS_ROOT.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )
    return runs[0] if runs else None
