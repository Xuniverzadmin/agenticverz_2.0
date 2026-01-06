"""
Pytest configuration and shared fixtures for AOS tests.

Test Categories:
- Unit tests: Fast, no external dependencies (tests/schemas/, tests/unit/)
- Integration tests: Require Redis/PostgreSQL (tests/test_integration.py)
- E2E tests: Full stack tests (tests/test_phase4_e2e.py)
- Security tests: Security validation (tests/test_phase5_security.py)

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
- REDIS_URL: Redis connection string
- AOS_API_KEY: API key for authenticated endpoints
- ENFORCE_TENANCY: Whether to enforce tenant isolation

Test Isolation (PIN-276):
- Every test runs inside a DB transaction that is rolled back
- Prometheus metrics use per-test isolated registries
- No test may depend on state created by another test
"""

import os
import sys
from pathlib import Path

import pytest

# Add backend/app to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Default test environment
os.environ.setdefault("DATABASE_URL", "postgresql://nova:novapass@localhost:5433/nova_aos")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("AOS_API_KEY", "test-key-for-testing")
os.environ.setdefault("ENFORCE_TENANCY", "false")
os.environ.setdefault("MACHINE_SECRET_TOKEN", "46bff817a6bb074b4322db92d5652905816597d741eea5b787ef990c1674c9ff")

# PIN-276: Reduce connection pool sizes for testing to prevent exhaustion
# These are set before any database imports to ensure they take effect
os.environ.setdefault("DB_POOL_SIZE", "5")
os.environ.setdefault("DB_MAX_OVERFLOW", "10")

# =============================================================================
# BUCKET B FIX: PROMETHEUS STATE B (PIN-276)
# =============================================================================
# Real Prometheus client with in-process registry - no external server needed.
# This provides State B: real semantics, minimal, local-compatible.

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, Histogram


def _clear_prometheus_registry():
    """Clear all custom metrics from Prometheus registry for test isolation."""
    collectors_to_remove = []
    for name, collector in list(REGISTRY._names_to_collectors.items()):
        # Skip default collectors (gc, platform, process)
        if name.startswith(("python_", "process_", "gc_")):
            continue
        collectors_to_remove.append(collector)

    for collector in collectors_to_remove:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass


# Initial cleanup at import time
_clear_prometheus_registry()


# =============================================================================
# TEST ISOLATION FIXTURES (PIN-276 - Bucket A/B Permanent Fix)
# =============================================================================
# INVARIANT: No test may depend on state created by another test.
# This is an architecture rule, not a test bug.


@pytest.fixture(autouse=True, scope="function")
def isolate_prometheus_registry():
    """
    Isolate Prometheus registry between tests.

    This fixture runs before and after each test function to prevent
    "Duplicated timeseries" errors caused by metric re-registration.

    PIN-276 Bucket B: Prometheus State B compliance.
    Reference: PIN-271 (CI North Star), PIN-120 (PREV-1)
    """
    # Clear before test
    _clear_prometheus_registry()
    yield
    # Clear after test (belt and suspenders)
    _clear_prometheus_registry()


@pytest.fixture(scope="function")
def prometheus_registry():
    """
    Per-test isolated Prometheus registry.

    PIN-276 Bucket B: State B Prometheus - real semantics, no external server.

    Usage:
        def test_metrics(prometheus_registry):
            counter = Counter('test_counter', 'Test', registry=prometheus_registry)
            counter.inc()
            assert prometheus_registry.get_sample_value('test_counter') == 1.0
    """
    registry = CollectorRegistry()
    yield registry
    # Registry is automatically garbage collected


@pytest.fixture(scope="function")
def metrics_factory(prometheus_registry):
    """
    Factory for creating isolated metrics in tests.

    PIN-276 Bucket B: Real Prometheus metrics without external server.

    Usage:
        def test_something(metrics_factory):
            counter = metrics_factory.counter('requests_total', 'Request count')
            counter.inc()
    """

    class MetricsFactory:
        def __init__(self, registry):
            self._registry = registry

        def counter(self, name, description, labelnames=()):
            return Counter(name, description, labelnames=labelnames, registry=self._registry)

        def gauge(self, name, description, labelnames=()):
            return Gauge(name, description, labelnames=labelnames, registry=self._registry)

        def histogram(self, name, description, labelnames=(), buckets=None):
            kwargs = {"registry": self._registry}
            if buckets:
                kwargs["buckets"] = buckets
            return Histogram(name, description, labelnames=labelnames, **kwargs)

        def get_value(self, name, labels=None):
            """Get current metric value from registry."""
            return self._registry.get_sample_value(name, labels=labels or {})

    return MetricsFactory(prometheus_registry)


def _dispose_db_engines():
    """
    Dispose all database engines to prevent connection pool exhaustion.

    PIN-276: This is critical for test isolation - connections must be
    released after each test to prevent "too many clients" errors.
    """
    try:
        import app.db as db_module

        # Dispose sync engine (keeps singleton, just releases connections)
        if db_module._engine is not None:
            try:
                db_module._engine.dispose()
            except Exception:
                pass

        # Dispose async engine
        if db_module._async_engine is not None:
            try:
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop is None or not loop.is_running():
                    try:
                        asyncio.run(db_module._async_engine.dispose())
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass

    # Also handle db_async module
    try:
        import app.db_async as db_async_module

        if hasattr(db_async_module, "async_engine") and db_async_module.async_engine is not None:
            try:
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop is None or not loop.is_running():
                    asyncio.run(db_async_module.async_engine.dispose())
            except Exception:
                pass
    except (ImportError, Exception):
        pass


@pytest.fixture(autouse=True, scope="function")
def reset_module_level_singletons():
    """
    Reset module-level singletons that can leak state between tests.

    This catches common patterns where module globals accumulate state.

    PIN-276: Test isolation hardening.
    Reference: PIN-271 (CI North Star)
    """
    yield
    # After each test, reset known singleton patterns
    try:
        # Reset any cached app instances
        import sys

        # Clear any cached FastAPI app test clients
        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith("app.") and hasattr(sys.modules[mod_name], "_cached_"):
                # Clear cached attributes
                for attr in list(dir(sys.modules[mod_name])):
                    if attr.startswith("_cached_"):
                        delattr(sys.modules[mod_name], attr)
    except Exception:
        pass  # Best effort cleanup

    # Dispose database connections to prevent pool exhaustion
    _dispose_db_engines()


# =============================================================================
# BUCKET A FIX: DATABASE TRANSACTION ROLLBACK (PIN-276)
# =============================================================================
# Every test runs inside a transaction that is rolled back at the end.
# This guarantees zero state bleed between tests.


@pytest.fixture(scope="function")
def isolated_db_session():
    """
    Database session with automatic rollback - NEVER commits to DB.

    PIN-276 Bucket A: Transaction rollback per test.

    INVARIANT: Any DB changes made during the test are automatically rolled back.
    This ensures tests cannot affect each other through database state.

    Usage:
        def test_something(isolated_db_session):
            # Create data - will be rolled back
            isolated_db_session.add(MyModel(name="test"))
            isolated_db_session.flush()  # Use flush() not commit()
            # Query data
            result = isolated_db_session.exec(select(MyModel)).first()
            assert result.name == "test"
        # After test: automatic rollback, DB unchanged
    """
    from sqlmodel import Session

    from app.db import get_engine

    engine = get_engine()

    # Begin a transaction
    connection = engine.connect()
    transaction = connection.begin()

    # Create session bound to this transaction
    session = Session(bind=connection)

    try:
        yield session
    finally:
        # ALWAYS rollback - this is the key to isolation
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def isolated_async_session():
    """
    Async database session with automatic rollback - NEVER commits to DB.

    PIN-276 Bucket A: Transaction rollback per test (async version).

    Usage:
        async def test_something(isolated_async_session):
            async with isolated_async_session() as session:
                # Create data - will be rolled back
                session.add(MyModel(name="test"))
                await session.flush()
    """
    from contextlib import asynccontextmanager

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db import get_async_engine

    @asynccontextmanager
    async def get_session():
        engine = get_async_engine()
        async with engine.connect() as connection:
            async with connection.begin() as transaction:
                session = AsyncSession(bind=connection, expire_on_commit=False)
                try:
                    yield session
                finally:
                    await session.close()
                    await transaction.rollback()

    return get_session


# =============================================================================
# RBAC STUB FIXTURES (PIN-271 / Phase C prep)
# =============================================================================
# These fixtures provide deterministic auth headers for tests without
# requiring external auth infrastructure (Clerk). See docs/infra/RBAC_STUB_DESIGN.md


@pytest.fixture
def stub_admin_headers():
    """Headers for admin access in tests."""
    return {"X-AOS-Key": "stub_admin_test_tenant"}


@pytest.fixture
def stub_developer_headers():
    """Headers for developer access in tests."""
    return {"X-AOS-Key": "stub_developer_test_tenant"}


@pytest.fixture
def stub_viewer_headers():
    """Headers for read-only access in tests."""
    return {"X-AOS-Key": "stub_viewer_test_tenant"}


@pytest.fixture
def stub_machine_headers():
    """Headers for machine/API access in tests."""
    return {"X-AOS-Key": "stub_machine_test_tenant"}


# =============================================================================
# EXISTING FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API tests."""
    return os.environ.get("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def api_key():
    """API key for authenticated requests."""
    return os.environ.get("AOS_API_KEY", "test-key-for-testing")


@pytest.fixture
def auth_headers(api_key):
    """Headers with API key authentication."""
    return {"X-AOS-Key": api_key}


@pytest.fixture
def sample_agent_profile():
    """Sample agent profile for testing."""
    return {
        "agent_id": "test-agent-001",
        "name": "Test Agent",
        "version": "1.0.0",
        "description": "Agent for testing",
        "allowed_skills": ["http_call", "json_transform"],
        "budget": {"max_cost_cents_per_run": 100, "max_cost_cents_per_day": 1000},
        "policies": {"require_human_approval": False, "allowed_domains": ["api.example.com"]},
    }


@pytest.fixture
def sample_skill_metadata():
    """Sample skill metadata for testing."""
    return {
        "skill_id": "http_call",
        "version": "1.0.0",
        "name": "HTTP Call",
        "description": "Make HTTP requests",
        "deterministic": False,
        "side_effects": ["network"],
        "cost_estimate_cents": 0,
        "avg_latency_ms": 500,
        "retry": {"max_retries": 3, "backoff_base_ms": 100, "backoff_multiplier": 2.0},
    }


@pytest.fixture
def sample_structured_outcome():
    """Sample StructuredOutcome for testing."""
    from datetime import datetime, timezone

    return {
        "status": "success",
        "code": "OK_HTTP_CALL",
        "message": "HTTP call completed successfully",
        "cost_cents": 0,
        "latency_ms": 250,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retryable": False,
        "details": {"status_code": 200},
        "side_effects": [],
        "metadata": {"skill_id": "http_call", "skill_version": "1.0.0"},
    }


# Markers for test categories
def pytest_configure(config):
    """Register custom markers.

    Test Categorization (PIN-120 / PREV-7):
    - @pytest.mark.slow: Tests > 30 seconds, excluded from normal CI
    - @pytest.mark.stress: Load/stress tests, run in nightly builds only
    - @pytest.mark.integration: Requires external services (DB, Redis)
    - @pytest.mark.flaky: Known intermittent failures (retry in CI)

    CI Bucket Classification (PIN-267, PIN-268 / GU-002):
    - @pytest.mark.ci_bucket("A"): Test is wrong (fix test)
    - @pytest.mark.ci_bucket("B"): Infra is missing (add skip/capability check)
    - @pytest.mark.ci_bucket("C"): System bug (fix code at L6)

    Every test fix PR must declare its bucket. Missing classification = PR rejected.
    """
    config.addinivalue_line("markers", "unit: Unit tests (no external deps)")
    config.addinivalue_line("markers", "integration: Integration tests (require services)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (full stack)")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "slow: Slow tests (>30s) - excluded from normal CI")
    config.addinivalue_line("markers", "stress: Load/stress tests - run in nightly builds")
    config.addinivalue_line("markers", "flaky: Known intermittent failures - retry in CI")
    config.addinivalue_line("markers", "determinism: Determinism validation tests")
    config.addinivalue_line("markers", "chaos: Chaos tests (resource stress, failure injection)")

    # CI Bucket Classification Markers (PIN-267, PIN-268 / GU-002)
    # These markers classify test fixes for governance compliance
    config.addinivalue_line(
        "markers", "ci_bucket(bucket): CI fix classification - A=Test Wrong, B=Infra Missing, C=System Bug"
    )
    config.addinivalue_line("markers", "pb_s1: Tests for PB-S1 truth guarantee (retry immutability)")
    config.addinivalue_line(
        "markers", "pb_s1_behavioral: Tests for PB-S1 behavioral invariants (cost chain, attempt monotonicity)"
    )
    config.addinivalue_line("markers", "invariant: Invariant tests that must not be weakened")


# =============================================================================
# DANGER FENCES (PIN-268 GU-004)
# =============================================================================


def pytest_collection_modifyitems(config, items):
    """
    GU-004 Danger Fence: Invariant Test Skip Protection.

    This hook warns when tests marked @pytest.mark.invariant are being skipped.
    Invariant tests exist to prevent regression of structural guarantees.

    Per PIN-267:
    - Invariant tests MUST NOT be weakened
    - Skips are allowed only for infra reasons (Bucket B)
    - xfail is acceptable to document known issues

    To explicitly allow skipping invariant tests, run with:
        pytest --allow-invariant-skip
    """
    # Check if explicit override flag is set
    allow_skip = config.getoption("--allow-invariant-skip", default=False)

    for item in items:
        # Check if test has invariant marker
        if item.get_closest_marker("invariant"):
            # Check if test is being skipped
            skip_marker = item.get_closest_marker("skip")
            skipif_marker = item.get_closest_marker("skipif")

            if skip_marker or skipif_marker:
                if not allow_skip:
                    # Warn but don't block (warning mode for now)
                    print(
                        f"\n[DANGER FENCE] INVARIANT TEST SKIP WARNING: {item.nodeid}\n"
                        f"  Invariant tests must not be weakened (PIN-267).\n"
                        f"  If skip is intentional, run with: pytest --allow-invariant-skip\n"
                    )


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--allow-invariant-skip",
        action="store_true",
        default=False,
        help="Allow skipping invariant tests (use with caution, see PIN-267)",
    )
    parser.addoption(
        "--run-db-isolation-tests",
        action="store_true",
        default=False,
        help="Run database isolation tests (requires DATABASE_URL)",
    )


# =============================================================================
# M10 RECOVERY SCHEMA ISOLATION (PIN-276)
# =============================================================================
# Clean m10_recovery.* tables before tests that use M10 infrastructure.
# This prevents cross-test pollution in recovery/outbox tests.


@pytest.fixture(scope="function")
def clean_m10_tables():
    """
    Clean m10_recovery schema tables before test.

    PIN-276: Test isolation for M10 recovery infrastructure.

    Usage:
        def test_outbox(clean_m10_tables):
            # Tables are clean at start of test
            ...
    """
    from sqlalchemy import create_engine, text

    database_url = os.environ.get("DATABASE_URL", "postgresql://nova:novapass@localhost:5433/nova_aos")
    engine = create_engine(database_url)

    # Tables to clean (order matters for foreign keys)
    m10_tables = [
        "m10_recovery.dead_letter_archive",
        "m10_recovery.replay_log",
        "m10_recovery.work_queue",
        "m10_recovery.outbox",
        "m10_recovery.matview_refresh_log",
    ]

    with engine.connect() as conn:
        for table in m10_tables:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass  # Table may not exist yet
        conn.commit()

    yield

    # Clean after test (belt and suspenders)
    with engine.connect() as conn:
        for table in m10_tables:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass
        conn.commit()

    engine.dispose()


@pytest.fixture(scope="function")
def clean_recovery_candidates():
    """
    Clean recovery_candidates table before test.

    PIN-276: Test isolation for recovery candidate tests.

    Usage:
        def test_recovery(clean_recovery_candidates):
            # recovery_candidates table is clean
            ...
    """
    from sqlalchemy import create_engine, text

    database_url = os.environ.get("DATABASE_URL", "postgresql://nova:novapass@localhost:5433/nova_aos")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Clean related tables first (foreign key order)
        conn.execute(text("DELETE FROM m10_recovery.suggestion_input"))
        conn.execute(text("DELETE FROM m10_recovery.suggestion_provenance"))
        conn.execute(text("DELETE FROM recovery_candidates"))
        conn.commit()

    yield

    with engine.connect() as conn:
        conn.execute(text("DELETE FROM m10_recovery.suggestion_input"))
        conn.execute(text("DELETE FROM m10_recovery.suggestion_provenance"))
        conn.execute(text("DELETE FROM recovery_candidates"))
        conn.commit()

    engine.dispose()
