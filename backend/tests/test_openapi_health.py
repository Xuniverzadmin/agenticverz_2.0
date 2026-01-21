# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI / pytest
#   Execution: sync
# Role: Regression test for OpenAPI schema generation
# Reference: PIN-444

"""
PIN-444: OpenAPI Schema Health Regression Tests

These tests catch OpenAPI schema generation issues BEFORE they cause production hangs:
- Timeout detection (generation should complete in < 5s)
- Cache-free generation verification
- Problematic pattern detection (recursion, unions, deep nesting)

ROOT CAUSE PATTERNS TO CATCH:
- Pattern A: Recursive model references (A → B → A)
- Pattern B: Union explosion (Union[A, B, C, D] with nested models)
- Pattern C: Executable defaults (default_factory with side effects)

When these tests fail, DO NOT:
- "increase timeout"
- "disable docs permanently"
- "hope it goes away"

Instead, use binary search:
1. Router-level: Comment out routers one by one
2. Endpoint-level: Remove response_model= one by one
3. Model-level: Simplify the bad model to find the exact field
"""

import os
import time

import pytest

# Skip if not in test environment with app available
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_OPENAPI_TESTS", "false").lower() == "true",
    reason="SKIP_OPENAPI_TESTS=true"
)


class TestOpenAPIGeneration:
    """Tests for OpenAPI schema generation health."""

    TIMEOUT_THRESHOLD = 5.0  # seconds - generation should be fast

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: import app and clear cache."""
        from app.main import app
        self.app = app
        # Clear cache to force regeneration
        self.app.openapi_schema = None

    def test_openapi_generates_within_timeout(self):
        """
        PIN-444: OpenAPI schema MUST generate within timeout.

        If this test fails:
        1. Check logs for OPENAPI: generation SLOW
        2. Run /__debug/openapi_inspect to find problematic models
        3. Binary search routers → endpoints → models
        4. Fix the recursive/union/default_factory pattern
        """
        start = time.perf_counter()
        schema = self.app.openapi()
        duration = time.perf_counter() - start

        assert schema is not None, "OpenAPI schema generation returned None"
        assert duration < self.TIMEOUT_THRESHOLD, (
            f"OpenAPI generation took {duration:.2f}s, threshold is {self.TIMEOUT_THRESHOLD}s. "
            f"Investigate response models for recursion/unions/default_factory."
        )

    def test_openapi_schema_has_paths(self):
        """Verify schema contains expected paths."""
        schema = self.app.openapi()

        assert "paths" in schema, "OpenAPI schema missing 'paths'"
        assert len(schema["paths"]) > 0, "OpenAPI schema has no paths"

        # Should have core API paths
        paths = schema["paths"]
        assert any("/health" in path for path in paths), "Missing /health endpoint"
        assert any("/api/v1" in path for path in paths), "Missing /api/v1 endpoints"

    def test_openapi_schema_has_components(self):
        """Verify schema contains component definitions."""
        schema = self.app.openapi()

        assert "components" in schema, "OpenAPI schema missing 'components'"
        components = schema["components"]

        assert "schemas" in components, "OpenAPI schema missing 'components.schemas'"
        # Should have some model definitions
        assert len(components["schemas"]) > 0, "OpenAPI schema has no model definitions"

    def test_openapi_no_excessive_recursion(self):
        """
        PIN-444: Detect models with excessive $ref counts (potential recursion).

        High $ref counts in a single model suggest recursive or deeply nested structures
        that can cause OpenAPI expansion issues.
        """
        schema = self.app.openapi()
        components = schema.get("components", {}).get("schemas", {})

        MAX_REF_COUNT = 10  # Models with more than this many refs are suspicious

        problematic_models = []
        for name, model_schema in components.items():
            schema_str = str(model_schema)
            ref_count = schema_str.count("$ref")
            if ref_count > MAX_REF_COUNT:
                problematic_models.append((name, ref_count))

        assert len(problematic_models) == 0, (
            f"Models with excessive $ref counts (>{MAX_REF_COUNT}): "
            f"{problematic_models}. These may cause OpenAPI expansion issues."
        )

    def test_openapi_union_count_reasonable(self):
        """
        PIN-444: Detect excessive union types (anyOf/oneOf).

        Union types with nested models cause combinatorial explosion in OpenAPI.
        """
        schema = self.app.openapi()
        components = schema.get("components", {}).get("schemas", {})

        union_models = []
        for name, model_schema in components.items():
            if "anyOf" in model_schema or "oneOf" in model_schema:
                union_models.append(name)

        MAX_UNION_MODELS = 20  # Reasonable limit for a large API

        assert len(union_models) <= MAX_UNION_MODELS, (
            f"Too many union types ({len(union_models)} > {MAX_UNION_MODELS}): "
            f"{union_models[:10]}... "
            f"Consider using discriminated unions or flattening models."
        )

    def test_openapi_cache_works(self):
        """Verify that OpenAPI caching prevents regeneration."""
        # First call - generates schema (timing not checked, just establishing cache)
        schema1 = self.app.openapi()

        # Second call - should be cached (near-instant)
        start2 = time.perf_counter()
        schema2 = self.app.openapi()
        duration2 = time.perf_counter() - start2

        assert schema1 is schema2, "OpenAPI cache not working - different schema objects"
        assert duration2 < 0.01, f"Cached call took {duration2:.4f}s, should be < 0.01s"

    def test_openapi_regenerates_after_cache_clear(self):
        """Verify schema can be regenerated after cache clear."""
        # Generate and cache
        schema1 = self.app.openapi()
        schema1_paths = len(schema1.get("paths", {}))

        # Clear cache
        self.app.openapi_schema = None

        # Regenerate
        start = time.perf_counter()
        schema2 = self.app.openapi()
        duration = time.perf_counter() - start

        schema2_paths = len(schema2.get("paths", {}))

        assert schema2 is not schema1, "Schema should be a new object after cache clear"
        assert schema1_paths == schema2_paths, "Path count changed after regeneration"
        assert duration < self.TIMEOUT_THRESHOLD, (
            f"Regeneration took {duration:.2f}s after cache clear"
        )


class TestOpenAPIDebugEndpoints:
    """Tests for the debug endpoints added in PIN-444."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_debug_openapi_nocache_endpoint(self, client):
        """
        PIN-444: Test the cache-free debug endpoint.

        This endpoint is critical for diagnosing:
        - If it hangs → schema graph problem
        - If it works but /openapi.json hangs → cache poisoning
        """
        response = client.get("/__debug/openapi_nocache", timeout=10)

        assert response.status_code == 200, f"Debug endpoint failed: {response.text}"

        data = response.json()
        assert "status" in data and data["status"] == "ok"
        assert "duration_ms" in data
        assert "schema_routes" in data
        assert data["schema_routes"] > 0, "Schema has no routes"

        # Should complete reasonably fast
        assert data["duration_ms"] < 5000, (
            f"Cache-free generation took {data['duration_ms']}ms - too slow"
        )

    def test_debug_openapi_inspect_endpoint(self, client):
        """PIN-444: Test the schema inspection endpoint."""
        response = client.get("/__debug/openapi_inspect", timeout=10)

        assert response.status_code == 200, f"Inspect endpoint failed: {response.text}"

        data = response.json()
        assert "total_schemas" in data
        assert "paths_count" in data
        assert "potential_issues" in data
        assert "health" in data

        # Verify structure
        issues = data["potential_issues"]
        assert "high_ref_count_models" in issues
        assert "union_types" in issues
        assert "deep_nesting" in issues


class TestOpenAPIResponseModels:
    """
    Spot-check specific response models for OpenAPI-safe patterns.

    Add models here when you suspect they might cause issues.
    """

    @pytest.fixture
    def schema(self):
        """Get OpenAPI schema."""
        from app.main import app
        app.openapi_schema = None  # Clear cache
        return app.openapi()

    def test_phase_b_models_are_flat(self, schema):
        """
        Verify Phase B (PB-S3, PB-S4, PB-S5) models are flat.

        These were initially suspected in the OpenAPI deadlock investigation.
        """
        components = schema.get("components", {}).get("schemas", {})

        # Phase B models that should be flat
        phase_b_models = [
            "FeedbackSummaryResponse",
            "FeedbackListResponse",
            "FeedbackDetailResponse",
            "ProposalSummaryResponse",
            "ProposalListResponse",
            "ProposalDetailResponse",
            "PredictionSummaryResponse",
            "PredictionListResponse",
            "PredictionDetailResponse",
        ]

        for model_name in phase_b_models:
            if model_name in components:
                model = components[model_name]
                # Check for excessive nesting
                model_str = str(model)
                ref_count = model_str.count("$ref")
                assert ref_count <= 5, (
                    f"Phase B model {model_name} has {ref_count} refs - may be too nested"
                )
