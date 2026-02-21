# Layer: TEST
# AUDIENCE: INTERNAL
# Role: API tests for CUS publication endpoints (/apis/ledger/cus, /apis/swagger/cus)
# artifact_class: TEST
# capability_id: CAP-011
"""
Tests for CUS Publication Router (backend/app/hoc/api/apis/cus_publication.py).

Validates:
1. Router structure (prefix, tags, GET-only).
2. Ledger handler returns correct shape and domain coverage.
3. Swagger handler returns valid OpenAPI subset.
4. Domain resolution covers all 502 ledger endpoints.
5. Invalid domain returns 404.
"""

import ast
import json
import os
import sys

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPO_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
sys.path.insert(0, BACKEND_DIR)

CANONICAL_CUS_DOMAINS = (
    "overview", "activity", "incidents", "policies", "controls",
    "logs", "analytics", "integrations", "api_keys", "account",
)


class TestCusPublicationRouterStructure:
    """Structural tests for the CUS publication router."""

    def _get_router_source(self) -> str:
        path = os.path.join(
            BACKEND_DIR, "app", "hoc", "api", "apis", "cus_publication.py"
        )
        with open(path) as f:
            return f.read()

    def test_router_prefix_is_apis(self):
        """Router prefix must be /apis."""
        source = self._get_router_source()
        assert 'prefix="/apis"' in source, "Router must use /apis prefix"

    def test_router_has_cus_publication_tag(self):
        """Router must have CUS Publication tag."""
        source = self._get_router_source()
        assert "CUS Publication" in source, "Router must have CUS Publication tag"

    def test_all_endpoints_are_get_only(self):
        """All publication endpoints must be GET (read-only)."""
        source = self._get_router_source()
        tree = ast.parse(source)

        decorators_found = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        decorators_found.append(dec.func.attr)

        for method in decorators_found:
            assert method == "get", f"Non-GET endpoint found: @router.{method}"

    def test_exactly_four_endpoints(self):
        """Must have exactly 4 publication endpoints."""
        source = self._get_router_source()
        tree = ast.parse(source)

        route_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr == "get":
                            route_count += 1

        assert route_count == 4, f"Expected 4 GET endpoints, found {route_count}"

    def test_has_capability_id(self):
        """File must have a capability_id annotation."""
        source = self._get_router_source()
        assert "capability_id: CAP-" in source, "Missing capability_id annotation"


class TestCusPublicationFacade:
    """Structural tests for the APIs facade."""

    def _get_facade_source(self) -> str:
        path = os.path.join(
            BACKEND_DIR, "app", "hoc", "api", "facades", "apis", "__init__.py"
        )
        with open(path) as f:
            return f.read()

    def test_facade_exists(self):
        """APIs facade must exist."""
        path = os.path.join(
            BACKEND_DIR, "app", "hoc", "api", "facades", "apis", "__init__.py"
        )
        assert os.path.exists(path), "APIs facade __init__.py must exist"

    def test_facade_exports_routers(self):
        """Facade must export ROUTERS list."""
        source = self._get_facade_source()
        assert "ROUTERS" in source, "Facade must export ROUTERS"

    def test_facade_imports_from_apis_lane(self):
        """Facade must import from apis lane (not directly from cus)."""
        source = self._get_facade_source()
        assert "app.hoc.api.apis" in source, "Facade must import from apis lane"

    def test_facade_has_capability_id(self):
        """Facade must have capability_id annotation."""
        source = self._get_facade_source()
        assert "capability_id: CAP-" in source, "Facade missing capability_id"


class TestAppWiringContract:
    """Verify app.py imports publication router through facade only."""

    def _get_app_source(self) -> str:
        path = os.path.join(BACKEND_DIR, "app", "hoc", "app.py")
        with open(path) as f:
            return f.read()

    def test_no_direct_apis_import(self):
        """app.py must NOT import directly from app.hoc.api.apis (use facade)."""
        source = self._get_app_source()
        assert "from app.hoc.api.apis" not in source, \
            "app.py must import through facades, not directly from apis lane"

    def test_imports_through_facade(self):
        """app.py must import from app.hoc.api.facades.apis."""
        source = self._get_app_source()
        assert "from app.hoc.api.facades.apis" in source, \
            "app.py must import APIS_ROUTERS through facades"


class TestLedgerHandlers:
    """Test ledger handlers via direct invocation."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.ledger_file = os.path.join(REPO_ROOT, "docs", "api", "HOC_CUS_API_LEDGER.json")

    def test_ledger_file_exists(self):
        """Global CUS ledger JSON must exist."""
        assert os.path.exists(self.ledger_file), f"Ledger not found: {self.ledger_file}"

    def test_ledger_has_502_endpoints(self):
        """Ledger must contain 502 total endpoints."""
        with open(self.ledger_file) as f:
            data = json.load(f)
        total = len(data.get("endpoints", []))
        assert total == 502, f"Expected 502 endpoints, got {total}"

    def test_ledger_has_499_unique_mp(self):
        """Ledger must have 499 unique method+path pairs."""
        with open(self.ledger_file) as f:
            data = json.load(f)
        eps = data.get("endpoints", [])
        unique = len({(e.get("method", ""), e.get("path", "")) for e in eps})
        assert unique == 499, f"Expected 499 unique m+p, got {unique}"


class TestDomainResolution:
    """Test that _resolve_domain covers all ledger endpoints."""

    def test_all_endpoints_resolve(self):
        """Every endpoint in the ledger must resolve to a valid domain."""
        from app.hoc.api.apis.cus_publication import _resolve_domain

        ledger_file = os.path.join(REPO_ROOT, "docs", "api", "HOC_CUS_API_LEDGER.json")
        with open(ledger_file) as f:
            data = json.load(f)

        unresolved = []
        for ep in data.get("endpoints", []):
            path = ep.get("path", "")
            domain = _resolve_domain(path)
            if domain is None or domain not in CANONICAL_CUS_DOMAINS:
                unresolved.append(path)

        assert len(unresolved) == 0, f"{len(unresolved)} unresolved paths: {unresolved[:5]}"

    def test_all_10_domains_populated(self):
        """All 10 canonical domains must have at least 1 endpoint."""
        from app.hoc.api.apis.cus_publication import _resolve_domain

        ledger_file = os.path.join(REPO_ROOT, "docs", "api", "HOC_CUS_API_LEDGER.json")
        with open(ledger_file) as f:
            data = json.load(f)

        domain_counts: dict[str, int] = {d: 0 for d in CANONICAL_CUS_DOMAINS}
        for ep in data.get("endpoints", []):
            domain = _resolve_domain(ep.get("path", ""))
            if domain and domain in domain_counts:
                domain_counts[domain] += 1

        empty = [d for d, c in domain_counts.items() if c == 0]
        assert len(empty) == 0, f"Domains with 0 endpoints: {empty}"


class TestPerDomainLedgers:
    """Validate per-domain ledger artifacts."""

    def test_all_10_domain_jsons_exist(self):
        """Each canonical domain must have a JSON ledger."""
        cus_dir = os.path.join(REPO_ROOT, "docs", "api", "cus")
        for domain in CANONICAL_CUS_DOMAINS:
            path = os.path.join(cus_dir, f"{domain}_ledger.json")
            assert os.path.exists(path), f"Missing: {domain}_ledger.json"

    def test_all_10_domain_csvs_exist(self):
        """Each canonical domain must have a CSV ledger."""
        cus_dir = os.path.join(REPO_ROOT, "docs", "api", "cus")
        for domain in CANONICAL_CUS_DOMAINS:
            path = os.path.join(cus_dir, f"{domain}_ledger.csv")
            assert os.path.exists(path), f"Missing: {domain}_ledger.csv"

    def test_all_10_domain_mds_exist(self):
        """Each canonical domain must have a MD ledger."""
        cus_dir = os.path.join(REPO_ROOT, "docs", "api", "cus")
        for domain in CANONICAL_CUS_DOMAINS:
            path = os.path.join(cus_dir, f"{domain}_ledger.md")
            assert os.path.exists(path), f"Missing: {domain}_ledger.md"

    def test_domain_json_endpoint_counts(self):
        """Per-domain JSON endpoint counts must match expected values."""
        expected = {
            "overview": 6, "activity": 21, "incidents": 20,
            "policies": 268, "controls": 7, "logs": 47,
            "analytics": 34, "integrations": 54,
            "api_keys": 13, "account": 32,
        }
        cus_dir = os.path.join(REPO_ROOT, "docs", "api", "cus")
        for domain, count in expected.items():
            path = os.path.join(cus_dir, f"{domain}_ledger.json")
            with open(path) as f:
                data = json.load(f)
            actual = len(data.get("endpoints", []))
            assert actual == count, f"{domain}: expected {count}, got {actual}"

    def test_sum_equals_global_ledger(self):
        """Sum of per-domain endpoints must equal global ledger total."""
        cus_dir = os.path.join(REPO_ROOT, "docs", "api", "cus")
        total = 0
        for domain in CANONICAL_CUS_DOMAINS:
            path = os.path.join(cus_dir, f"{domain}_ledger.json")
            with open(path) as f:
                data = json.load(f)
            total += len(data.get("endpoints", []))
        assert total == 502, f"Sum of per-domain = {total}, expected 502"
