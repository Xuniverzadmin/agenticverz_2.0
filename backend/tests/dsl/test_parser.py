# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: DSL parser tests
# Reference: PIN-341, PIN-345

"""
Tests for Policy DSL Parser.

COVERAGE:
- Valid policy parsing
- Error handling (invalid syntax)
- Roundtrip: DSL → AST → JSON
- All grammar constructs
"""

import json

import pytest

from app.dsl.ast import (
    Comparator,
    LogicalOperator,
    Mode,
    Scope,
    is_block_action,
    is_exists_predicate,
    is_logical_condition,
    is_predicate,
    is_require_approval_action,
    is_warn_action,
)
from app.dsl.parser import (
    Lexer,
    ParseError,
    parse,
    parse_condition,
)

# =============================================================================
# LEXER TESTS
# =============================================================================


class TestLexer:
    """Tests for the lexer."""

    def test_tokenize_keywords(self) -> None:
        """Test that keywords are recognized."""
        source = "policy version scope mode when then"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        types = [t.type for t in tokens[:-1]]  # Exclude EOF
        assert types == ["POLICY", "VERSION", "SCOPE_KW", "MODE_KW", "WHEN", "THEN"]

    def test_tokenize_comparators(self) -> None:
        """Test all comparators."""
        source = "> >= < <= == !="
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        types = [t.type for t in tokens[:-1]]
        assert types == ["GT", "GTE", "LT", "LTE", "EQ", "NEQ"]

    def test_tokenize_literals(self) -> None:
        """Test literal values."""
        source = '42 3.14 "hello" true false'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        values = [(t.type, t.value) for t in tokens[:-1]]
        assert values == [
            ("INT", 42),
            ("FLOAT", 3.14),
            ("STRING", "hello"),
            ("TRUE", True),
            ("FALSE", False),
        ]

    def test_tokenize_identifiers(self) -> None:
        """Test identifier recognition."""
        source = "cost_per_hour error_rate some_metric_123"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        values = [t.value for t in tokens[:-1]]
        assert values == ["cost_per_hour", "error_rate", "some_metric_123"]

    def test_tokenize_comments(self) -> None:
        """Test that comments are skipped."""
        source = """
        # This is a comment
        policy  # inline comment
        version
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        types = [t.type for t in tokens[:-1]]
        assert types == ["POLICY", "VERSION"]

    def test_tokenize_tracks_position(self) -> None:
        """Test that line/column tracking works."""
        source = "policy\nversion"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        assert tokens[0].line == 1
        assert tokens[0].column == 1
        assert tokens[1].line == 2
        assert tokens[1].column == 1

    def test_tokenize_invalid_character(self) -> None:
        """Test error on invalid character."""
        source = "policy @invalid"
        lexer = Lexer(source)
        with pytest.raises(ParseError) as exc_info:
            lexer.tokenize()
        assert "Unexpected character" in str(exc_info.value)


# =============================================================================
# BASIC PARSER TESTS
# =============================================================================


class TestParserBasic:
    """Basic parser tests."""

    def test_parse_minimal_policy(self) -> None:
        """Test parsing a minimal valid policy."""
        source = """
        policy CostGuard
        version 1
        scope PROJECT
        mode MONITOR

        when cost > 100
        then WARN "Alert"
        """
        ast = parse(source)

        assert ast.name == "CostGuard"
        assert ast.version == 1
        assert ast.scope == Scope.PROJECT
        assert ast.mode == Mode.MONITOR
        assert len(ast.clauses) == 1

    def test_parse_org_scope(self) -> None:
        """Test parsing ORG scope."""
        source = """
        policy OrgPolicy
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then BLOCK
        """
        ast = parse(source)
        assert ast.scope == Scope.ORG
        assert ast.mode == Mode.ENFORCE

    def test_parse_multiple_clauses(self) -> None:
        """Test parsing multiple when-then clauses."""
        source = """
        policy MultiClause
        version 1
        scope PROJECT
        mode ENFORCE

        when cost > 100
        then WARN "High cost"

        when error_rate > 0.1
        then BLOCK

        when anomaly_flag == true
        then REQUIRE_APPROVAL
        """
        ast = parse(source)
        assert len(ast.clauses) == 3

    def test_parse_multiple_actions(self) -> None:
        """Test parsing multiple actions in one clause."""
        source = """
        policy MultiAction
        version 1
        scope PROJECT
        mode ENFORCE

        when cost > 1000
        then WARN "Very high cost" BLOCK REQUIRE_APPROVAL
        """
        ast = parse(source)
        assert len(ast.clauses[0].then) == 3
        assert is_warn_action(ast.clauses[0].then[0])
        assert is_block_action(ast.clauses[0].then[1])
        assert is_require_approval_action(ast.clauses[0].then[2])


# =============================================================================
# CONDITION PARSING TESTS
# =============================================================================


class TestConditionParsing:
    """Tests for condition parsing."""

    def test_parse_simple_predicate(self) -> None:
        """Test simple comparison predicate."""
        cond = parse_condition("cost > 100")
        assert is_predicate(cond)
        assert cond.metric == "cost"
        assert cond.comparator == Comparator.GT
        assert cond.value == 100

    def test_parse_all_comparators(self) -> None:
        """Test all comparator types."""
        tests = [
            ("a > 1", Comparator.GT),
            ("a >= 1", Comparator.GTE),
            ("a < 1", Comparator.LT),
            ("a <= 1", Comparator.LTE),
            ("a == 1", Comparator.EQ),
            ("a != 1", Comparator.NEQ),
        ]
        for source, expected in tests:
            cond = parse_condition(source)
            assert cond.comparator == expected

    def test_parse_value_types(self) -> None:
        """Test different value types."""
        # Integer
        cond = parse_condition("x == 42")
        assert cond.value == 42
        assert isinstance(cond.value, int)

        # Float
        cond = parse_condition("x == 3.14")
        assert cond.value == 3.14
        assert isinstance(cond.value, float)

        # String
        cond = parse_condition('x == "hello"')
        assert cond.value == "hello"
        assert isinstance(cond.value, str)

        # Boolean
        cond = parse_condition("x == true")
        assert cond.value is True

        cond = parse_condition("x == false")
        assert cond.value is False

    def test_parse_negative_numbers(self) -> None:
        """Test negative number values."""
        cond = parse_condition("x > -100")
        assert cond.value == -100

        cond = parse_condition("x > -3.14")
        assert cond.value == -3.14

    def test_parse_exists_predicate(self) -> None:
        """Test exists predicate."""
        cond = parse_condition("exists(anomaly_flag)")
        assert is_exists_predicate(cond)
        assert cond.metric == "anomaly_flag"

    def test_parse_and_condition(self) -> None:
        """Test AND logical condition."""
        cond = parse_condition("cost > 100 AND error_rate > 0.1")
        assert is_logical_condition(cond)
        assert cond.operator == LogicalOperator.AND
        assert is_predicate(cond.left)
        assert is_predicate(cond.right)

    def test_parse_or_condition(self) -> None:
        """Test OR logical condition."""
        cond = parse_condition("cost > 100 OR error_rate > 0.1")
        assert is_logical_condition(cond)
        assert cond.operator == LogicalOperator.OR

    def test_parse_mixed_logical(self) -> None:
        """Test mixed AND/OR (AND binds tighter)."""
        # a OR b AND c → a OR (b AND c)
        cond = parse_condition("a > 1 OR b > 2 AND c > 3")
        assert cond.operator == LogicalOperator.OR
        assert is_predicate(cond.left)  # a > 1
        assert is_logical_condition(cond.right)  # b > 2 AND c > 3
        assert cond.right.operator == LogicalOperator.AND

    def test_parse_parenthesized(self) -> None:
        """Test parenthesized expressions."""
        # (a OR b) AND c
        cond = parse_condition("(a > 1 OR b > 2) AND c > 3")
        assert cond.operator == LogicalOperator.AND
        assert is_logical_condition(cond.left)  # (a > 1 OR b > 2)
        assert is_predicate(cond.right)  # c > 3
        assert cond.left.operator == LogicalOperator.OR

    def test_parse_deeply_nested(self) -> None:
        """Test deeply nested conditions."""
        cond = parse_condition("((a > 1 AND b > 2) OR (c > 3 AND d > 4)) AND e > 5")
        # Should parse without error
        assert is_logical_condition(cond)


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestParserErrors:
    """Tests for parser error handling."""

    def test_missing_policy_name(self) -> None:
        """Test error on missing policy name."""
        source = """
        policy
        version 1
        scope ORG
        mode MONITOR
        when x > 0
        then WARN "test"
        """
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "Expected IDENT" in str(exc_info.value)

    def test_missing_version(self) -> None:
        """Test error on missing version."""
        source = """
        policy Test
        scope ORG
        mode MONITOR
        when x > 0
        then WARN "test"
        """
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "Expected VERSION" in str(exc_info.value)

    def test_invalid_scope(self) -> None:
        """Test error on invalid scope."""
        source = """
        policy Test
        version 1
        scope INVALID
        mode MONITOR
        when x > 0
        then WARN "test"
        """
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "Expected ORG or PROJECT" in str(exc_info.value)

    def test_invalid_mode(self) -> None:
        """Test error on invalid mode."""
        source = """
        policy Test
        version 1
        scope ORG
        mode INVALID
        when x > 0
        then WARN "test"
        """
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "Expected MONITOR or ENFORCE" in str(exc_info.value)

    def test_missing_clause(self) -> None:
        """Test error on policy with no clauses."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR
        """
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "at least one clause" in str(exc_info.value)

    def test_missing_condition(self) -> None:
        """Test error on clause without condition."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR
        when
        then WARN "test"
        """
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        # Error will be about expecting an identifier for predicate
        assert exc_info.value.location is not None

    def test_missing_action(self) -> None:
        """Test error on clause without action."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR
        when x > 0
        then
        """
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "at least one action" in str(exc_info.value)

    def test_missing_warn_message(self) -> None:
        """Test error on WARN without message."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR
        when x > 0
        then WARN
        """
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "Expected STRING" in str(exc_info.value)

    def test_unclosed_parenthesis(self) -> None:
        """Test error on unclosed parenthesis."""
        source = 'policy Test version 1 scope ORG mode MONITOR when (x > 0 then WARN "test"'
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert "Expected RPAREN" in str(exc_info.value)

    def test_error_includes_location(self) -> None:
        """Test that errors include line/column info."""
        source = "invalid_start"
        with pytest.raises(ParseError) as exc_info:
            parse(source)
        assert exc_info.value.location is not None
        assert "line" in str(exc_info.value)


# =============================================================================
# ROUNDTRIP TESTS
# =============================================================================


class TestRoundtrip:
    """Tests for DSL → AST → JSON roundtrip."""

    def test_roundtrip_simple(self) -> None:
        """Test simple policy roundtrip."""
        source = """
        policy CostGuard
        version 1
        scope PROJECT
        mode MONITOR

        when cost_per_hour > 200
        then WARN "Cost exceeded threshold"
        """
        ast = parse(source)
        json_str = ast.to_json()
        data = json.loads(json_str)

        assert data["metadata"]["name"] == "CostGuard"
        assert data["metadata"]["version"] == 1
        assert data["metadata"]["scope"] == "PROJECT"
        assert data["metadata"]["mode"] == "MONITOR"
        assert len(data["clauses"]) == 1
        assert data["clauses"][0]["when"]["metric"] == "cost_per_hour"

    def test_roundtrip_complex(self) -> None:
        """Test complex policy roundtrip."""
        source = """
        policy ComplexPolicy
        version 5
        scope ORG
        mode ENFORCE

        # High cost with errors
        when cost > 1000 AND error_rate > 0.05
        then WARN "High cost with errors" BLOCK

        # Anomaly detection
        when exists(anomaly_flag) OR safety_score < 0.8
        then REQUIRE_APPROVAL
        """
        ast = parse(source)
        json_str = ast.to_json()
        data = json.loads(json_str)

        assert data["metadata"]["name"] == "ComplexPolicy"
        assert data["metadata"]["version"] == 5
        assert len(data["clauses"]) == 2

        # First clause: logical AND
        clause1 = data["clauses"][0]
        assert clause1["when"]["type"] == "logical"
        assert clause1["when"]["operator"] == "AND"
        assert len(clause1["then"]) == 2

        # Second clause: logical OR with exists
        clause2 = data["clauses"][1]
        assert clause2["when"]["type"] == "logical"
        assert clause2["when"]["operator"] == "OR"
        assert clause2["when"]["left"]["type"] == "exists"

    def test_hash_consistency(self) -> None:
        """Test that parsing produces consistent hashes."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 10
        then WARN "Alert"
        """
        ast1 = parse(source)
        ast2 = parse(source)

        assert ast1.compute_hash() == ast2.compute_hash()

    def test_hash_differs_with_content(self) -> None:
        """Test that different content produces different hashes."""
        source1 = """
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 10
        then WARN "Alert"
        """
        source2 = """
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 20
        then WARN "Alert"
        """
        ast1 = parse(source1)
        ast2 = parse(source2)

        assert ast1.compute_hash() != ast2.compute_hash()


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_quoted_strings(self) -> None:
        """Test single-quoted strings."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN 'Single quoted'
        """
        ast = parse(source)
        assert ast.clauses[0].then[0].message == "Single quoted"

    def test_whitespace_handling(self) -> None:
        """Test various whitespace patterns."""
        source = """


        policy     Test
        version    1
        scope      ORG
        mode       MONITOR

        when   x   >   0
        then   WARN   "test"


        """
        ast = parse(source)
        assert ast.name == "Test"

    def test_inline_comments(self) -> None:
        """Test inline comments."""
        source = """
        policy Test  # Policy name
        version 1    # Version number
        scope ORG    # Scope
        mode MONITOR # Mode

        when x > 0   # Condition
        then WARN "test"  # Action
        """
        ast = parse(source)
        assert ast.name == "Test"

    def test_float_values(self) -> None:
        """Test float value handling."""
        cond = parse_condition("error_rate >= 0.05")
        assert cond.value == 0.05
        assert isinstance(cond.value, float)

    def test_underscore_identifiers(self) -> None:
        """Test identifiers with underscores."""
        cond = parse_condition("cost_per_hour_avg > 100")
        assert cond.metric == "cost_per_hour_avg"

    def test_long_string_message(self) -> None:
        """Test long string messages."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "This is a very long warning message that explains the issue in detail"
        """
        ast = parse(source)
        assert "very long warning" in ast.clauses[0].then[0].message


# =============================================================================
# FULL POLICY EXAMPLES
# =============================================================================


class TestFullPolicies:
    """Tests with realistic full policy examples."""

    def test_cost_guard_policy(self) -> None:
        """Test a realistic cost guard policy."""
        source = """
        # CostGuard Policy v3
        # Monitors and enforces cost limits

        policy CostGuard
        version 3
        scope PROJECT
        mode ENFORCE

        # Warn on high hourly costs
        when cost_per_hour > 200
        then WARN "Hourly cost exceeds $200"

        # Block on very high costs
        when cost_per_hour > 500
        then WARN "CRITICAL: Cost exceeds $500/hr" BLOCK

        # Require approval for expensive operations with errors
        when total_cost > 10000 AND error_rate > 0.01
        then WARN "High cost with errors detected" REQUIRE_APPROVAL
        """
        ast = parse(source)

        assert ast.name == "CostGuard"
        assert ast.version == 3
        assert ast.scope == Scope.PROJECT
        assert ast.mode == Mode.ENFORCE
        assert len(ast.clauses) == 3

    def test_safety_policy(self) -> None:
        """Test a realistic safety policy."""
        source = """
        policy SafetyGuard
        version 1
        scope ORG
        mode ENFORCE

        # Block if safety score is too low
        when safety_score < 0.8
        then BLOCK

        # Require approval if anomaly detected
        when exists(anomaly_flag)
        then REQUIRE_APPROVAL

        # Warn on borderline safety
        when safety_score >= 0.8 AND safety_score < 0.9
        then WARN "Safety score is borderline"
        """
        ast = parse(source)

        assert ast.name == "SafetyGuard"
        assert len(ast.clauses) == 3

        # Check exists predicate
        clause2 = ast.clauses[1]
        assert is_exists_predicate(clause2.when)
