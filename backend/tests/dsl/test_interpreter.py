# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Interpreter tests
# Reference: PIN-341, PIN-345

"""
Tests for Policy DSL Interpreter.

COVERAGE:
- Basic evaluation
- All comparators
- Logical operators (AND, OR)
- EXISTS predicate
- All action types
- Error handling (type mismatch, missing metric)
- Lenient mode
- Result structure
"""

import pytest

from app.dsl.parser import parse
from app.dsl.ir_compiler import compile_policy
from app.dsl.interpreter import (
    evaluate,
    evaluate_policy,
    Interpreter,
    EvaluationResult,
    ClauseResult,
    ActionResult,
    EvaluationError,
    TypeMismatchError,
    MissingMetricError,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def compile_and_evaluate(source: str, facts: dict) -> EvaluationResult:
    """Helper to parse, compile, and evaluate a policy."""
    ast = parse(source)
    ir = compile_policy(ast)
    return evaluate(ir, facts)


# =============================================================================
# RESULT STRUCTURE TESTS
# =============================================================================

class TestResultStructure:
    """Tests for result data structures."""

    def test_action_result_warn(self) -> None:
        """Test ActionResult for WARN."""
        action = ActionResult(type="WARN", message="Alert")
        assert action.type == "WARN"
        assert action.message == "Alert"
        assert action.to_dict() == {"type": "WARN", "message": "Alert"}

    def test_action_result_block(self) -> None:
        """Test ActionResult for BLOCK."""
        action = ActionResult(type="BLOCK")
        assert action.type == "BLOCK"
        assert action.message is None
        assert action.to_dict() == {"type": "BLOCK"}

    def test_clause_result_matched(self) -> None:
        """Test ClauseResult when matched."""
        actions = (ActionResult(type="WARN", message="Test"),)
        result = ClauseResult(matched=True, actions=actions)
        assert result.matched
        assert len(result.actions) == 1
        d = result.to_dict()
        assert d["matched"] is True
        assert len(d["actions"]) == 1

    def test_clause_result_not_matched(self) -> None:
        """Test ClauseResult when not matched."""
        result = ClauseResult(matched=False)
        assert not result.matched
        assert len(result.actions) == 0
        d = result.to_dict()
        assert d["matched"] is False
        assert d["actions"] == []

    def test_evaluation_result_properties(self) -> None:
        """Test EvaluationResult helper properties."""
        actions = (
            ActionResult(type="WARN", message="W1"),
            ActionResult(type="BLOCK"),
            ActionResult(type="REQUIRE_APPROVAL"),
        )
        result = EvaluationResult(
            any_matched=True,
            clauses=(ClauseResult(matched=True, actions=actions),),
            all_actions=actions,
        )

        assert result.has_block
        assert result.has_require_approval
        assert result.warnings == ["W1"]


# =============================================================================
# BASIC EVALUATION TESTS
# =============================================================================

class TestBasicEvaluation:
    """Tests for basic evaluation."""

    def test_simple_matching_policy(self) -> None:
        """Test simple policy that matches."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when cost > 100
            then WARN "High cost"
            """,
            {"cost": 150}
        )

        assert result.any_matched
        assert len(result.all_actions) == 1
        assert result.all_actions[0].type == "WARN"
        assert result.all_actions[0].message == "High cost"

    def test_simple_non_matching_policy(self) -> None:
        """Test simple policy that does not match."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when cost > 100
            then WARN "High cost"
            """,
            {"cost": 50}
        )

        assert not result.any_matched
        assert len(result.all_actions) == 0

    def test_boundary_value_greater_than(self) -> None:
        """Test exact boundary for > comparator."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when cost > 100
            then WARN "Alert"
            """,
            {"cost": 100}  # Exactly 100, should NOT match
        )
        assert not result.any_matched

    def test_boundary_value_greater_equal(self) -> None:
        """Test exact boundary for >= comparator."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when cost >= 100
            then WARN "Alert"
            """,
            {"cost": 100}  # Exactly 100, should match
        )
        assert result.any_matched


# =============================================================================
# COMPARATOR TESTS
# =============================================================================

class TestComparators:
    """Tests for all comparator types."""

    @pytest.mark.parametrize("op,value,expected", [
        (">", 101, True),
        (">", 100, False),
        (">", 99, False),
        (">=", 101, True),
        (">=", 100, True),
        (">=", 99, False),
        ("<", 99, True),
        ("<", 100, False),
        ("<", 101, False),
        ("<=", 99, True),
        ("<=", 100, True),
        ("<=", 101, False),
        ("==", 100, True),
        ("==", 99, False),
        ("!=", 99, True),
        ("!=", 100, False),
    ])
    def test_numeric_comparisons(self, op: str, value: int, expected: bool) -> None:
        """Test all numeric comparisons."""
        result = compile_and_evaluate(
            f"""
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when x {op} 100
            then WARN "Match"
            """,
            {"x": value}
        )
        assert result.any_matched == expected

    def test_float_comparison(self) -> None:
        """Test float value comparison."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when rate > 0.05
            then WARN "High rate"
            """,
            {"rate": 0.1}
        )
        assert result.any_matched

    def test_string_comparison(self) -> None:
        """Test string equality."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when status == "error"
            then WARN "Error status"
            """,
            {"status": "error"}
        )
        assert result.any_matched

    def test_boolean_comparison(self) -> None:
        """Test boolean comparison."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when flag == true
            then WARN "Flag set"
            """,
            {"flag": True}
        )
        assert result.any_matched


# =============================================================================
# LOGICAL OPERATOR TESTS
# =============================================================================

class TestLogicalOperators:
    """Tests for AND/OR operators."""

    def test_and_both_true(self) -> None:
        """Test AND when both sides are true."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0 AND b > 0
            then WARN "Both positive"
            """,
            {"a": 10, "b": 20}
        )
        assert result.any_matched

    def test_and_left_false(self) -> None:
        """Test AND when left side is false."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0 AND b > 0
            then WARN "Both positive"
            """,
            {"a": -5, "b": 20}
        )
        assert not result.any_matched

    def test_and_right_false(self) -> None:
        """Test AND when right side is false."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0 AND b > 0
            then WARN "Both positive"
            """,
            {"a": 10, "b": -5}
        )
        assert not result.any_matched

    def test_or_both_true(self) -> None:
        """Test OR when both sides are true."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0 OR b > 0
            then WARN "At least one positive"
            """,
            {"a": 10, "b": 20}
        )
        assert result.any_matched

    def test_or_left_true(self) -> None:
        """Test OR when only left is true."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0 OR b > 0
            then WARN "At least one positive"
            """,
            {"a": 10, "b": -5}
        )
        assert result.any_matched

    def test_or_right_true(self) -> None:
        """Test OR when only right is true."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0 OR b > 0
            then WARN "At least one positive"
            """,
            {"a": -5, "b": 20}
        )
        assert result.any_matched

    def test_or_both_false(self) -> None:
        """Test OR when both sides are false."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0 OR b > 0
            then WARN "At least one positive"
            """,
            {"a": -5, "b": -10}
        )
        assert not result.any_matched

    def test_nested_logical(self) -> None:
        """Test nested logical expressions."""
        # (a > 0 AND b > 0) OR c > 0
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when (a > 0 AND b > 0) OR c > 0
            then WARN "Complex match"
            """,
            {"a": -5, "b": -5, "c": 10}  # Only c matches
        )
        assert result.any_matched


# =============================================================================
# EXISTS PREDICATE TESTS
# =============================================================================

class TestExistsPredicate:
    """Tests for exists predicate."""

    def test_exists_true(self) -> None:
        """Test exists when metric is present."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when exists(flag)
            then WARN "Flag exists"
            """,
            {"flag": True}
        )
        assert result.any_matched

    def test_exists_false(self) -> None:
        """Test exists when metric is absent."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when exists(flag)
            then WARN "Flag exists"
            """,
            {"other_metric": 123}
        )
        assert not result.any_matched

    def test_exists_with_none_value(self) -> None:
        """Test exists with None value (metric exists but is None)."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when exists(flag)
            then WARN "Flag exists"
            """,
            {"flag": None}  # Metric exists, even if value is None
        )
        assert result.any_matched

    def test_exists_combined_with_and(self) -> None:
        """Test exists combined with AND."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when exists(anomaly) AND severity > 5
            then WARN "Anomaly detected"
            """,
            {"anomaly": True, "severity": 8}
        )
        assert result.any_matched


# =============================================================================
# ACTION TESTS
# =============================================================================

class TestActions:
    """Tests for all action types."""

    def test_warn_action(self) -> None:
        """Test WARN action evaluation."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when x > 0
            then WARN "Warning message"
            """,
            {"x": 10}
        )

        assert len(result.all_actions) == 1
        assert result.all_actions[0].type == "WARN"
        assert result.all_actions[0].message == "Warning message"

    def test_block_action(self) -> None:
        """Test BLOCK action evaluation."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode ENFORCE

            when x > 0
            then BLOCK
            """,
            {"x": 10}
        )

        assert len(result.all_actions) == 1
        assert result.all_actions[0].type == "BLOCK"
        assert result.has_block

    def test_require_approval_action(self) -> None:
        """Test REQUIRE_APPROVAL action evaluation."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode ENFORCE

            when x > 0
            then REQUIRE_APPROVAL
            """,
            {"x": 10}
        )

        assert len(result.all_actions) == 1
        assert result.all_actions[0].type == "REQUIRE_APPROVAL"
        assert result.has_require_approval

    def test_multiple_actions(self) -> None:
        """Test multiple actions in one clause."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode ENFORCE

            when x > 0
            then WARN "Alert" BLOCK REQUIRE_APPROVAL
            """,
            {"x": 10}
        )

        assert len(result.all_actions) == 3
        types = [a.type for a in result.all_actions]
        assert types == ["WARN", "BLOCK", "REQUIRE_APPROVAL"]


# =============================================================================
# MULTIPLE CLAUSES TESTS
# =============================================================================

class TestMultipleClauses:
    """Tests for policies with multiple clauses."""

    def test_multiple_clauses_all_match(self) -> None:
        """Test when all clauses match."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0
            then WARN "A positive"

            when b > 0
            then WARN "B positive"
            """,
            {"a": 10, "b": 20}
        )

        assert result.any_matched
        assert len(result.clauses) == 2
        assert all(c.matched for c in result.clauses)
        assert len(result.all_actions) == 2

    def test_multiple_clauses_partial_match(self) -> None:
        """Test when some clauses match."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0
            then WARN "A positive"

            when b > 0
            then WARN "B positive"
            """,
            {"a": 10, "b": -5}
        )

        assert result.any_matched
        assert result.clauses[0].matched
        assert not result.clauses[1].matched
        assert len(result.all_actions) == 1

    def test_multiple_clauses_none_match(self) -> None:
        """Test when no clauses match."""
        result = compile_and_evaluate(
            """
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when a > 0
            then WARN "A positive"

            when b > 0
            then WARN "B positive"
            """,
            {"a": -5, "b": -10}
        )

        assert not result.any_matched
        assert len(result.all_actions) == 0


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Tests for error conditions."""

    def test_missing_metric_strict_mode(self) -> None:
        """Test that missing metric raises error in strict mode."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when unknown_metric > 0
        then WARN "Alert"
        """)
        ir = compile_policy(ast)

        with pytest.raises(MissingMetricError) as exc_info:
            evaluate(ir, {"other_metric": 123})

        assert "unknown_metric" in str(exc_info.value)

    def test_type_mismatch_string_to_int(self) -> None:
        """Test type mismatch error."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 100
        then WARN "Alert"
        """)
        ir = compile_policy(ast)

        with pytest.raises(TypeMismatchError):
            evaluate(ir, {"x": "not a number"})

    def test_type_mismatch_bool_to_int(self) -> None:
        """Test bool vs int type mismatch."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 100
        then WARN "Alert"
        """)
        ir = compile_policy(ast)

        with pytest.raises(TypeMismatchError):
            evaluate(ir, {"x": True})


# =============================================================================
# LENIENT MODE TESTS
# =============================================================================

class TestLenientMode:
    """Tests for lenient (non-strict) evaluation."""

    def test_lenient_missing_metric(self) -> None:
        """Test that missing metric does not raise in lenient mode."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when unknown_metric > 0
        then WARN "Alert"
        """)
        ir = compile_policy(ast)

        # Should not raise
        result = evaluate_policy(ir, {"other_metric": 123}, strict=False)

        # Clause should not match (missing metric treated as not-matching)
        assert not result.any_matched

    def test_lenient_exists_missing(self) -> None:
        """Test exists in lenient mode with missing metric."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when exists(flag)
        then WARN "Alert"
        """)
        ir = compile_policy(ast)

        result = evaluate_policy(ir, {}, strict=False)
        assert not result.any_matched

    def test_strict_mode_by_default(self) -> None:
        """Test that evaluate() uses strict mode."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        ir = compile_policy(ast)

        with pytest.raises(MissingMetricError):
            evaluate(ir, {})


# =============================================================================
# FULL POLICY TESTS
# =============================================================================

class TestFullPolicies:
    """Integration tests with realistic policies."""

    def test_cost_guard_policy(self) -> None:
        """Test realistic cost guard policy."""
        result = compile_and_evaluate(
            """
            policy CostGuard
            version 3
            scope PROJECT
            mode ENFORCE

            when cost_per_hour > 200
            then WARN "Hourly cost exceeds $200"

            when cost_per_hour > 500
            then WARN "CRITICAL: Cost exceeds $500/hr" BLOCK

            when total_cost > 10000 AND error_rate > 0.01
            then WARN "High cost with errors" REQUIRE_APPROVAL
            """,
            {"cost_per_hour": 600, "total_cost": 15000, "error_rate": 0.05}
        )

        # All three clauses should match
        assert result.any_matched
        assert len(result.clauses) == 3
        assert all(c.matched for c in result.clauses)

        # Check actions
        assert result.has_block
        assert result.has_require_approval
        assert len(result.warnings) == 3

    def test_safety_policy(self) -> None:
        """Test realistic safety policy."""
        result = compile_and_evaluate(
            """
            policy SafetyGuard
            version 1
            scope ORG
            mode ENFORCE

            when safety_score < 0.8
            then BLOCK

            when exists(anomaly_flag)
            then REQUIRE_APPROVAL

            when safety_score >= 0.8 AND safety_score < 0.9
            then WARN "Safety score is borderline"
            """,
            {"safety_score": 0.85, "anomaly_flag": True}
        )

        # First clause: 0.85 < 0.8 is FALSE
        # Second clause: anomaly_flag exists, TRUE
        # Third clause: 0.85 >= 0.8 AND 0.85 < 0.9, TRUE
        assert result.any_matched
        assert not result.clauses[0].matched
        assert result.clauses[1].matched
        assert result.clauses[2].matched
        assert result.has_require_approval
        assert len(result.warnings) == 1
