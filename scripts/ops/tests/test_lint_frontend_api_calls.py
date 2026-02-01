#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Regression tests for lint_frontend_api_calls.py
# artifact_class: CODE
"""
Regression tests for lint_frontend_api_calls.py

PIN-314: Ensures lint rules match actual API contracts.

Test Matrix:
  - H1 Replay UX: incident_id is CORRECT (not call_id)
  - Legacy Replay: call_id is CORRECT
  - Incident endpoints: incident_id is CORRECT
"""

import sys
import traceback
from pathlib import Path

# Add parent directory to path for import
sys.path.insert(0, str(Path(__file__).parent.parent))

from lint_frontend_api_calls import (  # noqa: E402
    ENDPOINT_ID_CONTRACTS,
    find_issues,
)


class TestH1ReplayUrlPatterns:
    """H1 Replay UX uses incident_id - these should NOT trigger errors."""

    def test_incident_id_in_h1_replay_slice_is_valid(self):
        """incident.id in H1 replay slice URL is CORRECT."""
        code = "fetch(`/replay/${incident.id}/slice`)"
        issues = find_issues(code, "test.tsx")
        # Should NOT find any issues - incident.id is correct for H1
        assert len(issues) == 0, (
            f"False positive: incident.id is valid for H1 replay. Got: {issues}"
        )

    def test_incident_id_in_h1_replay_summary_is_valid(self):
        """incident.id in H1 replay summary URL is CORRECT."""
        code = "fetch(`/replay/${incident.id}/summary`)"
        issues = find_issues(code, "test.tsx")
        assert len(issues) == 0, (
            f"False positive: incident.id is valid for H1 replay. Got: {issues}"
        )

    def test_incident_id_in_h1_replay_timeline_is_valid(self):
        """incident.id in H1 replay timeline URL is CORRECT."""
        code = "fetch(`/replay/${incident.id}/timeline`)"
        issues = find_issues(code, "test.tsx")
        assert len(issues) == 0, (
            f"False positive: incident.id is valid for H1 replay. Got: {issues}"
        )

    def test_inc_prefix_in_h1_replay_is_valid(self):
        """inc_ prefix in H1 replay URL is CORRECT (incident_id format)."""
        code = "const url = `/replay/inc_${id}/slice`"
        issues = find_issues(code, "test.tsx")
        assert len(issues) == 0, (
            f"False positive: inc_ prefix is valid for H1 replay. Got: {issues}"
        )


class TestH1ReplayCallIdErrors:
    """Using call_id in H1 Replay UX should trigger errors."""

    def test_call_id_in_h1_replay_slice_is_error(self):
        """call_id in H1 replay slice URL is WRONG."""
        code = "fetch(`/replay/${incident.call_id}/slice`)"
        issues = find_issues(code, "test.tsx")
        error_issues = [i for i in issues if i[4] == "error"]
        assert len(error_issues) > 0, "Should detect call_id misuse in H1 replay"
        assert any("call_id_in_h1_replay" in i[1] for i in error_issues)

    def test_call_id_in_h1_replay_summary_is_error(self):
        """call_id in H1 replay summary URL is WRONG."""
        code = "fetch(`/replay/${call_id}/summary`)"
        issues = find_issues(code, "test.tsx")
        error_issues = [i for i in issues if i[4] == "error"]
        assert len(error_issues) > 0, "Should detect call_id misuse in H1 replay"

    def test_call_id_in_h1_replay_timeline_is_error(self):
        """call_id in H1 replay timeline URL is WRONG."""
        code = "const url = `/replay/${item.call_id}/timeline`"
        issues = find_issues(code, "test.tsx")
        error_issues = [i for i in issues if i[4] == "error"]
        assert len(error_issues) > 0, "Should detect call_id misuse in H1 replay"


class TestIncidentEndpointPatterns:
    """Incident endpoints use incident_id."""

    def test_incident_id_in_incident_endpoint_is_valid(self):
        """incident.id in /incidents/ endpoint is CORRECT."""
        code = "fetch(`/incidents/${incident.id}`)"
        issues = find_issues(code, "test.tsx")
        # Should NOT trigger call_id_in_incident_endpoint
        call_id_issues = [i for i in issues if "call_id_in_incident" in i[1]]
        assert len(call_id_issues) == 0, (
            f"False positive on incident.id. Got: {call_id_issues}"
        )

    def test_call_id_in_incident_endpoint_is_warning(self):
        """call_id in /incidents/ endpoint is WRONG."""
        code = "fetch(`/incidents/${incident.call_id}`)"
        issues = find_issues(code, "test.tsx")
        warning_issues = [
            i for i in issues if i[4] == "warning" and "call_id_in_incident" in i[1]
        ]
        assert len(warning_issues) > 0, "Should warn about call_id in incident endpoint"


class TestEndpointIdContracts:
    """Verify ENDPOINT_ID_CONTRACTS are correctly defined."""

    def test_h1_replay_endpoints_use_incident_id(self):
        """H1 Replay UX endpoints should expect incident_id."""
        assert ENDPOINT_ID_CONTRACTS.get("/replay/{id}/slice") == "incident_id"
        assert ENDPOINT_ID_CONTRACTS.get("/replay/{id}/summary") == "incident_id"
        assert ENDPOINT_ID_CONTRACTS.get("/replay/{id}/timeline") == "incident_id"
        assert ENDPOINT_ID_CONTRACTS.get("/replay/{id}/explain/") == "incident_id"

    def test_legacy_replay_endpoints_use_call_id(self):
        """Legacy replay endpoints should expect call_id."""
        assert ENDPOINT_ID_CONTRACTS.get("/guard/replay/{id}") == "call_id"
        assert ENDPOINT_ID_CONTRACTS.get("/v1/replay/{id}") == "call_id"
        assert ENDPOINT_ID_CONTRACTS.get("/operator/replay/{id}") == "call_id"

    def test_incident_endpoints_use_incident_id(self):
        """Incident management endpoints should expect incident_id."""
        assert ENDPOINT_ID_CONTRACTS.get("/incidents/{id}") == "incident_id"
        assert ENDPOINT_ID_CONTRACTS.get("/incidents/{id}/acknowledge") == "incident_id"
        assert ENDPOINT_ID_CONTRACTS.get("/incidents/{id}/resolve") == "incident_id"


class TestNoFalsePositives:
    """Ensure common patterns don't trigger false positives."""

    def test_generic_id_variable_no_issue(self):
        """Generic ${id} should not trigger issues."""
        code = "fetch(`/replay/${id}/slice`)"
        issues = find_issues(code, "test.tsx")
        # Generic id is ambiguous but not a clear error
        error_issues = [i for i in issues if i[4] == "error"]
        assert len(error_issues) == 0, (
            f"False positive on generic id. Got: {error_issues}"
        )

    def test_selectedIncident_id_no_issue(self):
        """selectedIncident.id should not trigger issues."""
        code = "fetch(`/replay/${selectedIncident.id}/timeline`)"
        issues = find_issues(code, "test.tsx")
        error_issues = [i for i in issues if i[4] == "error"]
        assert len(error_issues) == 0, (
            f"False positive on selectedIncident.id. Got: {error_issues}"
        )


def run_tests():
    """Run all tests and report results."""
    test_classes = [
        TestH1ReplayUrlPatterns,
        TestH1ReplayCallIdErrors,
        TestIncidentEndpointPatterns,
        TestEndpointIdContracts,
        TestNoFalsePositives,
    ]

    passed = 0
    failed = 0
    errors = []

    for test_class in test_classes:
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    passed += 1
                    print(f"  PASS: {test_class.__name__}.{method_name}")
                except AssertionError as exc:
                    failed += 1
                    errors.append((f"{test_class.__name__}.{method_name}", str(exc)))
                    print(f"  FAIL: {test_class.__name__}.{method_name}")
                except Exception:
                    failed += 1
                    errors.append(
                        (f"{test_class.__name__}.{method_name}", traceback.format_exc())
                    )
                    print(f"  ERROR: {test_class.__name__}.{method_name}")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")

    if errors:
        print("\nFailures:")
        for name, msg in errors:
            print(f"\n  {name}:")
            print(f"    {msg}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
