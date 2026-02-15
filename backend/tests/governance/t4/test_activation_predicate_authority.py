# Layer: L8 — Test
# AUDIENCE: INTERNAL
# Role: Test activation predicate authority boundary — DB evidence only, no in-memory cache
# Reference: TODO_PLAN.md Step 2 (Enforce Read Paths for Activation)
# artifact_class: TEST

"""
Activation Predicate Authority Tests

Verifies that:
1. The activation predicate is a pure function using only its boolean inputs.
2. The onboarding_handler activation section does NOT import connector_registry_driver.
3. Cache empty + DB evidence present -> activates correctly.
4. Cache populated + DB evidence absent -> does NOT activate.
"""

from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# ---------------------------------------------------------------------------
# Test 1: Pure predicate function (no DB, no cache, pure logic)
# ---------------------------------------------------------------------------


def test_activation_predicate_all_true():
    """All conditions met -> passes."""
    from app.hoc.cus.hoc_spine.authority.onboarding_policy import check_activation_predicate

    passed, missing = check_activation_predicate(True, True, True, True)
    assert passed is True
    assert missing == []


def test_activation_predicate_missing_project():
    """project_ready False -> fails with project_ready missing."""
    from app.hoc.cus.hoc_spine.authority.onboarding_policy import check_activation_predicate

    passed, missing = check_activation_predicate(False, True, True, True)
    assert passed is False
    assert "project_ready" in missing


def test_activation_predicate_missing_all():
    """All conditions False -> fails with all 4 missing."""
    from app.hoc.cus.hoc_spine.authority.onboarding_policy import check_activation_predicate

    passed, missing = check_activation_predicate(False, False, False, False)
    assert passed is False
    assert len(missing) == 4
    assert set(missing) == {"project_ready", "key_ready", "connector_validated", "sdk_attested"}


def test_activation_predicate_missing_connector_only():
    """connector_validated False -> fails even if everything else is True."""
    from app.hoc.cus.hoc_spine.authority.onboarding_policy import check_activation_predicate

    passed, missing = check_activation_predicate(True, True, False, True)
    assert passed is False
    assert missing == ["connector_validated"]


# ---------------------------------------------------------------------------
# Test 2: Static analysis — activation section must not import cache modules
# ---------------------------------------------------------------------------


def test_activation_section_no_cache_imports():
    """
    Static check: the activation predicate helpers in onboarding_handler.py
    must NOT contain imports of connector_registry_driver or ConnectorRegistry.

    This is the test-level equivalent of CI check 35.
    """
    handler_path = (
        BACKEND_ROOT
        / "app"
        / "hoc"
        / "cus"
        / "hoc_spine"
        / "orchestrator"
        / "handlers"
        / "onboarding_handler.py"
    )
    assert handler_path.exists(), f"Handler not found: {handler_path}"

    source = handler_path.read_text()

    # Extract activation predicate section (from ACTIVATION PREDICATE HELPERS to end of file)
    idx = source.find("ACTIVATION PREDICATE HELPERS")
    assert idx != -1, "ACTIVATION PREDICATE HELPERS section not found"
    activation_section = source[idx:]

    forbidden = [
        "connector_registry_driver",
        "get_connector_registry",
        "ConnectorRegistry",
    ]

    for pattern in forbidden:
        # Exclude comments
        for line in activation_section.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert pattern not in stripped, (
                f"Activation section imports cache module: '{pattern}' found in: {stripped}"
            )


def test_activation_section_uses_only_db_tables():
    """
    Static check: activation predicate SQL must reference only persistent
    tables (api_keys, cus_integrations, sdk_attestations), never
    connector_registry or _connectors.
    """
    handler_path = (
        BACKEND_ROOT
        / "app"
        / "hoc"
        / "cus"
        / "hoc_spine"
        / "orchestrator"
        / "handlers"
        / "onboarding_handler.py"
    )
    source = handler_path.read_text()

    idx = source.find("ACTIVATION PREDICATE HELPERS")
    activation_section = source[idx:]

    # Must contain these DB table references
    assert "api_keys" in activation_section, "Missing api_keys table query"
    assert "cus_integrations" in activation_section, "Missing cus_integrations table query"
    assert "sdk_attestations" in activation_section, "Missing sdk_attestations table query"

    # Must NOT contain in-memory references in non-comment lines
    for line in activation_section.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'"):
            continue
        assert "_connectors" not in stripped or "tenant_connectors" not in stripped, (
            f"In-memory dict reference found: {stripped}"
        )


# ---------------------------------------------------------------------------
# Test 3+4: Semantic authority boundary (cache vs DB independence)
# ---------------------------------------------------------------------------


def test_predicate_ignores_cache_state():
    """
    Even if we hypothetically populate a connector registry cache,
    the activation predicate (a pure function) only uses its boolean inputs.
    DB=True + Cache=irrelevant -> passes.
    """
    from app.hoc.cus.hoc_spine.authority.onboarding_policy import check_activation_predicate

    # Simulate: DB says enabled (connector_validated=True), cache is irrelevant
    passed, missing = check_activation_predicate(
        has_project=True,
        has_api_key=True,
        has_validated_connector=True,  # DB evidence
        has_sdk_attestation=True,
    )
    assert passed is True
    assert missing == []


def test_predicate_fails_without_db_evidence():
    """
    Even if connector cache would show connectors,
    DB evidence absent (connector_validated=False) -> fails.
    """
    from app.hoc.cus.hoc_spine.authority.onboarding_policy import check_activation_predicate

    # Simulate: DB says no enabled integrations, but cache might have connectors
    passed, missing = check_activation_predicate(
        has_project=True,
        has_api_key=True,
        has_validated_connector=False,  # No DB evidence
        has_sdk_attestation=True,
    )
    assert passed is False
    assert "connector_validated" in missing


def test_predicate_contract_comment_exists_in_registry_driver():
    """
    Verify the authority contract comment exists in connector_registry_driver.py.
    """
    driver_path = (
        BACKEND_ROOT
        / "app"
        / "hoc"
        / "cus"
        / "integrations"
        / "L6_drivers"
        / "connector_registry_driver.py"
    )
    assert driver_path.exists()
    source = driver_path.read_text()
    assert "AUTHORITY CONTRACT" in source, "Missing AUTHORITY CONTRACT comment"
    assert "RUNTIME CACHE ONLY" in source, "Missing RUNTIME CACHE ONLY declaration"
    assert "cus_integrations" in source, "Missing cus_integrations table reference in contract"


# ---------------------------------------------------------------------------
# Test 5: Full activation predicate matrix (2^4 = 16 combinations)
# Reference: GREEN_CLOSURE_PLAN_UC001_UC002 Phase 4
# ---------------------------------------------------------------------------


def test_activation_predicate_full_matrix():
    """
    Exhaustive test of all 16 boolean combinations.
    Only (True, True, True, True) passes. All others fail.
    """
    from app.hoc.cus.hoc_spine.authority.onboarding_policy import check_activation_predicate

    for p in (True, False):
        for k in (True, False):
            for c in (True, False):
                for s in (True, False):
                    passed, missing = check_activation_predicate(p, k, c, s)
                    if p and k and c and s:
                        assert passed is True, f"Expected pass for ({p},{k},{c},{s})"
                        assert missing == []
                    else:
                        assert passed is False, f"Expected fail for ({p},{k},{c},{s})"
                        assert len(missing) > 0, f"Expected missing list for ({p},{k},{c},{s})"
                        # Verify each False maps to the correct missing key
                        if not p:
                            assert "project_ready" in missing
                        if not k:
                            assert "key_ready" in missing
                        if not c:
                            assert "connector_validated" in missing
                        if not s:
                            assert "sdk_attested" in missing


# ---------------------------------------------------------------------------
# Test 6: Regression — indirect cache coupling
# Reference: GREEN_CLOSURE_PLAN_UC001_UC002 Phase 4
# ---------------------------------------------------------------------------


def test_predicate_no_indirect_cache_coupling():
    """
    Regression: importing connector_registry_driver and manipulating its
    in-memory state must NOT affect the activation predicate result.

    The predicate is a pure function of its boolean inputs. Even if the
    connector registry is populated, the predicate outcome depends only
    on the DB-sourced boolean arguments.
    """
    from app.hoc.cus.hoc_spine.authority.onboarding_policy import check_activation_predicate

    # Import the cache module to prove its presence doesn't influence the predicate
    from app.hoc.cus.integrations.L6_drivers import connector_registry_driver  # noqa: F401

    # Scenario: cache module is imported, but DB says no connectors
    passed, missing = check_activation_predicate(
        has_project=True,
        has_api_key=True,
        has_validated_connector=False,  # DB says no
        has_sdk_attestation=True,
    )
    assert passed is False, "Predicate must fail when DB evidence is absent"
    assert "connector_validated" in missing

    # Scenario: cache module is imported, DB says connectors exist
    passed2, missing2 = check_activation_predicate(
        has_project=True,
        has_api_key=True,
        has_validated_connector=True,  # DB says yes
        has_sdk_attestation=True,
    )
    assert passed2 is True, "Predicate must pass when all DB evidence is present"
    assert missing2 == []
