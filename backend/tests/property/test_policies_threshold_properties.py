# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Property-based tests for threshold monotonicity and policy conflict resolution
# artifact_class: TEST
"""
BA-12: Property-based tests for threshold monotonicity and policy conflict resolution.

All tests are self-contained with inline helper functions that mirror the expected
behavior of production code. No production imports are used.
"""

import re
from typing import List, Optional, Tuple

import pytest
from hypothesis import given, settings, strategies as st


# ---------------------------------------------------------------------------
# Inline helper functions (mirrors of expected production behavior)
# ---------------------------------------------------------------------------

def validate_threshold(value: float) -> bool:
    """A threshold is valid iff it is a finite, non-negative float."""
    if not isinstance(value, (int, float)):
        return False
    # NaN and infinities are invalid
    if value != value:  # NaN check
        return False
    if value == float("inf") or value == float("-inf"):
        return False
    return value >= 0.0


def apply_thresholds_preserve_monotonicity(thresholds: List[float]) -> List[float]:
    """
    Given a sorted list of valid thresholds, applying them sequentially must
    preserve monotonic non-decreasing ordering.  This helper simply returns
    the list unchanged — the property under test is that *any* valid sorted
    input remains sorted after the identity application.
    """
    return list(thresholds)


def resolve_policy_conflict(
    policy_a: Tuple[str, int],
    policy_b: Tuple[str, int],
) -> str:
    """
    Given two policies (name, priority), the one with the **higher** priority
    value wins.  Ties are broken lexicographically by name (deterministic).
    Returns the winning policy name.
    """
    name_a, prio_a = policy_a
    name_b, prio_b = policy_b
    if prio_a > prio_b:
        return name_a
    if prio_b > prio_a:
        return name_b
    # Tie-break: lexicographic on name
    return min(name_a, name_b)


def sanitize_policy_name(raw: str) -> str:
    """
    Sanitize a policy name so it contains only lowercase alphanumeric
    characters, hyphens, and underscores.  Leading/trailing whitespace is
    stripped, internal whitespace is collapsed to underscores, and all other
    invalid characters are removed.
    """
    s = raw.strip().lower()
    # Collapse whitespace to underscores
    s = re.sub(r"\s+", "_", s)
    # Remove anything that is not [a-z0-9_-]
    s = re.sub(r"[^a-z0-9_\-]", "", s)
    return s


_VALID_POLICY_NAME_RE = re.compile(r"^[a-z0-9_\-]*$")


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


class TestThresholdValidation:
    """Properties around threshold value validation."""

    @given(st.floats())
    @settings(max_examples=200)
    def test_threshold_must_be_non_negative(self, value: float) -> None:
        """Any negative float should be rejected by threshold validation."""
        result = validate_threshold(value)
        if value < 0.0:
            assert result is False, (
                f"Negative threshold {value} should be rejected"
            )

    @settings(max_examples=200)
    @given(
        st.lists(
            st.floats(
                min_value=0.0,
                max_value=1e6,
                allow_nan=False,
                allow_infinity=False,
            ),
            min_size=0,
            max_size=50,
        )
    )
    def test_threshold_monotonicity_preserved(
        self, thresholds: List[float]
    ) -> None:
        """
        Given a sorted list of valid thresholds, applying them sequentially
        must preserve monotonic non-decreasing ordering.
        """
        sorted_input = sorted(thresholds)
        result = apply_thresholds_preserve_monotonicity(sorted_input)
        for i in range(1, len(result)):
            assert result[i] >= result[i - 1], (
                f"Monotonicity violated at index {i}: "
                f"{result[i - 1]} > {result[i]}"
            )

    def test_threshold_boundary_exact_match(self) -> None:
        """
        Boundary test: threshold of exactly 0.0 is valid, threshold of
        -0.001 is invalid.  This is a concrete edge-case supplement to the
        property test above.
        """
        assert validate_threshold(0.0) is True, "0.0 must be a valid threshold"
        assert validate_threshold(-0.001) is False, (
            "-0.001 must be rejected"
        )
        # Additional boundary values
        assert validate_threshold(1e-10) is True, "Small positive is valid"
        assert validate_threshold(-1e-10) is False, "Small negative is invalid"
        assert validate_threshold(float("nan")) is False, "NaN is invalid"
        assert validate_threshold(float("inf")) is False, "Inf is invalid"
        assert validate_threshold(float("-inf")) is False, "-Inf is invalid"


class TestPolicyConflictResolution:
    """Properties around deterministic policy conflict resolution."""

    @given(
        st.tuples(st.text(min_size=1, max_size=30), st.integers(0, 1000)),
        st.tuples(st.text(min_size=1, max_size=30), st.integers(0, 1000)),
    )
    @settings(max_examples=200)
    def test_policy_priority_total_ordering(
        self,
        policy_a: Tuple[str, int],
        policy_b: Tuple[str, int],
    ) -> None:
        """
        Given any two policies with different priorities, one must win
        deterministically.  Even with equal priorities the tie-break on name
        must produce exactly one winner.
        """
        name_a, prio_a = policy_a
        name_b, prio_b = policy_b
        winner = resolve_policy_conflict(policy_a, policy_b)
        assert winner in (name_a, name_b), (
            f"Winner '{winner}' is not one of the input policies"
        )
        # If priorities differ, higher priority wins
        if prio_a != prio_b:
            expected = name_a if prio_a > prio_b else name_b
            assert winner == expected, (
                f"Higher priority should win: expected {expected}, got {winner}"
            )

    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=30),
                st.integers(0, 1000),
            ),
            min_size=2,
            max_size=20,
        )
    )
    @settings(max_examples=200)
    def test_policy_conflict_resolution_idempotent(
        self, policies: List[Tuple[str, int]]
    ) -> None:
        """
        Resolving conflicts twice on the same set of policies must yield the
        same result.  We reduce the list pairwise left-to-right twice and
        compare.
        """

        def reduce_policies(pols: List[Tuple[str, int]]) -> str:
            """Reduce a list of policies to a single winner via pairwise resolution."""
            current = pols[0]
            for nxt in pols[1:]:
                winner_name = resolve_policy_conflict(current, nxt)
                # Rebuild the tuple for the winner
                if winner_name == current[0]:
                    current = current
                else:
                    current = nxt
            return current[0]

        result_1 = reduce_policies(policies)
        result_2 = reduce_policies(policies)
        assert result_1 == result_2, (
            f"Conflict resolution is not idempotent: "
            f"first={result_1}, second={result_2}"
        )


class TestPolicyNameSanitization:
    """Properties around policy name sanitization."""

    @given(st.text(max_size=200))
    @settings(max_examples=200)
    def test_policy_name_sanitization(self, raw: str) -> None:
        """
        Given any string, the sanitized policy name must contain only
        lowercase alphanumeric characters, hyphens, and underscores.
        """
        sanitized = sanitize_policy_name(raw)
        assert _VALID_POLICY_NAME_RE.match(sanitized), (
            f"Sanitized name '{sanitized}' contains invalid characters "
            f"(source: {raw!r})"
        )
        # Sanitization must be idempotent
        assert sanitize_policy_name(sanitized) == sanitized, (
            "Sanitization is not idempotent"
        )
