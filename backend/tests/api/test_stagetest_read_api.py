# Layer: TEST
# AUDIENCE: INTERNAL
# Role: API tests for stagetest evidence console read endpoints
# artifact_class: TEST
"""
Tests for /hoc/api/stagetest/* read-only API.

Validates:
1. All canonical endpoints return expected shapes.
2. Router uses correct prefix (/hoc/api/stagetest, NOT /api/v1/stagetest).
3. All endpoints are GET-only.
4. Founder auth dependency is enforced.
5. No write endpoints exist.
"""

import ast
import json
import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestStagetestRouterStructure:
    """Structural tests for the stagetest router."""

    def _get_router_source(self) -> str:
        path = os.path.join(
            BACKEND_DIR, "app", "hoc", "api", "fdr", "ops", "stagetest.py"
        )
        with open(path) as f:
            return f.read()

    def test_router_prefix_is_canonical(self):
        """Router prefix must be /hoc/api/stagetest (never /api/v1/stagetest)."""
        source = self._get_router_source()
        assert '/hoc/api/stagetest' in source, "Router must use canonical /hoc/api/stagetest prefix"
        assert '/api/v1/stagetest' not in source, "FORBIDDEN: /api/v1/stagetest found in router"

    def test_router_has_auth_dependency(self):
        """Router must enforce founder auth (verify_fops_token)."""
        source = self._get_router_source()
        assert "verify_fops_token" in source, "Router must import and use verify_fops_token"

    def test_all_endpoints_are_get_only(self):
        """All stagetest endpoints must be GET (read-only). No POST/PUT/DELETE."""
        source = self._get_router_source()
        tree = ast.parse(source)

        decorators_found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr in ("post", "put", "delete", "patch"):
                    if isinstance(node.value, ast.Name) and node.value.id == "router":
                        decorators_found.append(node.attr)

        assert not decorators_found, (
            f"Write endpoints found on stagetest router: {decorators_found}. "
            "Stagetest API must be read-only (GET only)."
        )

    def test_canonical_endpoints_exist(self):
        """All canonical GET endpoints are defined."""
        source = self._get_router_source()

        expected_paths = [
            "/runs",
            "/runs/{run_id}",
            "/runs/{run_id}/cases",
            "/runs/{run_id}/cases/{case_id}",
            "/apis",
            "/apis/ledger",
        ]
        for path in expected_paths:
            assert path in source, f"Missing endpoint path: {path}"

    def test_facade_registration(self):
        """Stagetest router is registered in fdr.ops facade."""
        facade_path = os.path.join(
            BACKEND_DIR, "app", "hoc", "api", "facades", "fdr", "ops.py"
        )
        with open(facade_path) as f:
            source = f.read()

        assert "stagetest" in source.lower(), "Stagetest router not registered in fdr.ops facade"
        assert "stagetest_router" in source, "stagetest_router not imported in facade"


class TestStagetestEndpointImport:
    """Test that the stagetest module can be imported without errors."""

    def test_router_importable(self):
        """Stagetest router module is importable."""
        sys.path.insert(0, BACKEND_DIR)
        try:
            from app.hoc.api.fdr.ops.stagetest import router
            assert router is not None
            assert hasattr(router, "routes")
        finally:
            sys.path.pop(0)


class TestStagetestLedgerSnapshot:
    """Behavioral tests for merged HOC ledger snapshot selection."""

    def test_ledger_snapshot_prefers_merged_hoc_file(self, tmp_path, monkeypatch):
        sys.path.insert(0, BACKEND_DIR)
        try:
            from app.hoc.fdr.ops.engines import stagetest_read_engine as engine

            docs_api = tmp_path / "docs" / "api"
            docs_api.mkdir(parents=True, exist_ok=True)
            all_file = docs_api / "HOC_API_LEDGER_ALL.json"
            all_file.write_text(
                json.dumps(
                    {
                        "generated_at_utc": "2026-02-21T00:00:00Z",
                        "endpoints": [
                            {"method": "GET", "path": "/hoc/api/cus/a", "operation": "a"},
                        ],
                    }
                )
            )

            monkeypatch.setattr(
                engine,
                "LEDGER_FILES",
                {
                    "all": all_file,
                    "cus": docs_api / "HOC_CUS_API_LEDGER.json",
                    "fdr": docs_api / "HOC_FDR_API_LEDGER.json",
                },
            )
            snapshot = engine.get_apis_ledger_snapshot()
            assert snapshot["run_id"] == "ledger-hoc-all"
            assert len(snapshot["endpoints"]) == 1
            assert snapshot["endpoints"][0]["path"] == "/hoc/api/cus/a"
        finally:
            sys.path.pop(0)

    def test_ledger_snapshot_merges_cus_and_fdr_files(self, tmp_path, monkeypatch):
        sys.path.insert(0, BACKEND_DIR)
        try:
            from app.hoc.fdr.ops.engines import stagetest_read_engine as engine

            docs_api = tmp_path / "docs" / "api"
            docs_api.mkdir(parents=True, exist_ok=True)
            (docs_api / "HOC_CUS_API_LEDGER.json").write_text(
                json.dumps(
                    {
                        "generated_at_utc": "2026-02-21T00:00:00Z",
                        "endpoints": [
                            {"method": "GET", "path": "/hoc/api/cus/a", "operation": "cus_a"},
                        ],
                    }
                )
            )
            (docs_api / "HOC_FDR_API_LEDGER.json").write_text(
                json.dumps(
                    {
                        "generated_at_utc": "2026-02-21T00:00:01Z",
                        "endpoints": [
                            {"method": "GET", "path": "/hoc/api/fdr/b", "operation": "fdr_b"},
                        ],
                    }
                )
            )

            monkeypatch.setattr(
                engine,
                "LEDGER_FILES",
                {
                    "all": docs_api / "HOC_API_LEDGER_ALL.json",
                    "cus": docs_api / "HOC_CUS_API_LEDGER.json",
                    "fdr": docs_api / "HOC_FDR_API_LEDGER.json",
                },
            )
            snapshot = engine.get_apis_ledger_snapshot()
            assert snapshot["run_id"] == "ledger-hoc-cus-fdr"
            assert len(snapshot["endpoints"]) == 2
            assert {e["path"] for e in snapshot["endpoints"]} == {
                "/hoc/api/cus/a",
                "/hoc/api/fdr/b",
            }
        finally:
            sys.path.pop(0)

    def test_schemas_importable(self):
        """Stagetest schemas are importable."""
        sys.path.insert(0, BACKEND_DIR)
        try:
            from app.hoc.fdr.ops.schemas.stagetest import (
                RunSummary,
                RunListResponse,
                CaseDetail,
                CaseListResponse,
                ApisSnapshotResponse,
            )
            assert RunSummary is not None
            assert RunListResponse is not None
            assert CaseDetail is not None
            assert CaseListResponse is not None
            assert ApisSnapshotResponse is not None
        finally:
            sys.path.pop(0)

    def test_engine_importable(self):
        """Stagetest read engine is importable."""
        sys.path.insert(0, BACKEND_DIR)
        try:
            from app.hoc.fdr.ops.engines.stagetest_read_engine import (
                list_runs,
                get_run,
                list_cases,
                get_case,
                get_apis_snapshot,
                get_apis_ledger_snapshot,
            )
            assert callable(list_runs)
            assert callable(get_run)
            assert callable(list_cases)
            assert callable(get_case)
            assert callable(get_apis_snapshot)
            assert callable(get_apis_ledger_snapshot)
        finally:
            sys.path.pop(0)
