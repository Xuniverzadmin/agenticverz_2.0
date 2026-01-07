# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Round-trip determinism tests
# Reference: PIN-341, PIN-345

"""
Round-Trip Determinism Tests

GUARANTEE: DSL → AST → IR → Interpreter produces identical outputs
for identical inputs, across runs, without external dependencies.

COVERAGE:
- Parse determinism (same DSL → same AST)
- Compile determinism (same AST → same IR)
- Evaluate determinism (same IR + facts → same result)
- Hash stability (IR hash is stable across runs)
- Full pipeline determinism
"""

import json
import pytest

from app.dsl.parser import parse
from app.dsl.validator import validate
from app.dsl.ir_compiler import compile_policy, ir_hash
from app.dsl.interpreter import evaluate


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def cost_guard_dsl() -> str:
    """Realistic cost guard policy DSL."""
    return """
    # CostGuard Policy v3
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
    """


@pytest.fixture
def safety_guard_dsl() -> str:
    """Realistic safety guard policy DSL."""
    return """
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
    """


@pytest.fixture
def complex_condition_dsl() -> str:
    """Policy with complex nested conditions."""
    return """
    policy ComplexPolicy
    version 1
    scope ORG
    mode MONITOR

    when (a > 1 AND b > 2) OR (c > 3 AND d > 4)
    then WARN "Complex match"

    when exists(flag1) AND (x > 10 OR y < 5)
    then WARN "Exists with logic"
    """


# =============================================================================
# PARSE DETERMINISM TESTS
# =============================================================================

class TestParseDeterminism:
    """Tests that parsing is deterministic."""

    def test_same_dsl_same_ast_json(self, cost_guard_dsl: str) -> None:
        """Same DSL text produces identical AST JSON."""
        ast1 = parse(cost_guard_dsl)
        ast2 = parse(cost_guard_dsl)

        json1 = ast1.to_json()
        json2 = ast2.to_json()

        assert json1 == json2

    def test_same_dsl_same_ast_hash(self, cost_guard_dsl: str) -> None:
        """Same DSL text produces identical AST hash."""
        ast1 = parse(cost_guard_dsl)
        ast2 = parse(cost_guard_dsl)

        assert ast1.compute_hash() == ast2.compute_hash()

    def test_whitespace_normalization(self) -> None:
        """Different whitespace produces same AST."""
        dsl1 = """
        policy   Test
        version  1
        scope    ORG
        mode     MONITOR
        when x > 0
        then WARN "Alert"
        """

        dsl2 = """policy Test version 1 scope ORG mode MONITOR when x > 0 then WARN "Alert" """

        ast1 = parse(dsl1)
        ast2 = parse(dsl2)

        # Same structural content
        assert ast1.name == ast2.name
        assert ast1.version == ast2.version
        assert ast1.to_json() == ast2.to_json()

    def test_comment_normalization(self) -> None:
        """Comments do not affect AST."""
        dsl1 = """
        policy Test
        version 1
        scope ORG
        mode MONITOR
        when x > 0
        then WARN "Alert"
        """

        dsl2 = """
        # This is a comment
        policy Test  # inline comment
        version 1    # another comment
        scope ORG
        mode MONITOR
        # Comment before clause
        when x > 0   # condition comment
        then WARN "Alert"  # action comment
        """

        ast1 = parse(dsl1)
        ast2 = parse(dsl2)

        assert ast1.to_json() == ast2.to_json()


# =============================================================================
# COMPILE DETERMINISM TESTS
# =============================================================================

class TestCompileDeterminism:
    """Tests that compilation is deterministic."""

    def test_same_ast_same_ir_json(self, cost_guard_dsl: str) -> None:
        """Same AST produces identical IR JSON."""
        ast = parse(cost_guard_dsl)

        ir1 = compile_policy(ast)
        ir2 = compile_policy(ast)

        assert ir1.to_json() == ir2.to_json()

    def test_same_ast_same_ir_hash(self, cost_guard_dsl: str) -> None:
        """Same AST produces identical IR hash."""
        ast = parse(cost_guard_dsl)

        ir1 = compile_policy(ast)
        ir2 = compile_policy(ast)

        assert ir1.compute_hash() == ir2.compute_hash()

    def test_ir_hash_convenience_matches(self, cost_guard_dsl: str) -> None:
        """ir_hash() produces same result as compile + compute_hash."""
        ast = parse(cost_guard_dsl)

        hash1 = ir_hash(ast)
        hash2 = compile_policy(ast).compute_hash()

        assert hash1 == hash2

    def test_instruction_order_stable(self, complex_condition_dsl: str) -> None:
        """Instruction order is stable across compilations."""
        ast = parse(complex_condition_dsl)

        ir1 = compile_policy(ast)
        ir2 = compile_policy(ast)

        for i, (clause1, clause2) in enumerate(zip(ir1.clauses, ir2.clauses)):
            # Condition instructions must match exactly
            for j, (inst1, inst2) in enumerate(
                zip(clause1.condition_ir, clause2.condition_ir)
            ):
                assert inst1.opcode == inst2.opcode, f"Clause {i}, instruction {j}"
                assert inst1.operands == inst2.operands, f"Clause {i}, instruction {j}"

            # Action instructions must match exactly
            for j, (inst1, inst2) in enumerate(
                zip(clause1.action_ir, clause2.action_ir)
            ):
                assert inst1.opcode == inst2.opcode, f"Clause {i}, action {j}"
                assert inst1.operands == inst2.operands, f"Clause {i}, action {j}"


# =============================================================================
# EVALUATE DETERMINISM TESTS
# =============================================================================

class TestEvaluateDeterminism:
    """Tests that evaluation is deterministic."""

    def test_same_ir_facts_same_result(self, cost_guard_dsl: str) -> None:
        """Same IR + facts produces identical result."""
        ast = parse(cost_guard_dsl)
        ir = compile_policy(ast)
        facts = {"cost_per_hour": 600, "total_cost": 15000, "error_rate": 0.05}

        result1 = evaluate(ir, facts)
        result2 = evaluate(ir, facts)

        assert result1.to_dict() == result2.to_dict()

    def test_result_structure_stable(self, cost_guard_dsl: str) -> None:
        """Result structure is stable across evaluations."""
        ast = parse(cost_guard_dsl)
        ir = compile_policy(ast)
        facts = {"cost_per_hour": 600, "total_cost": 15000, "error_rate": 0.05}

        result1 = evaluate(ir, facts)
        result2 = evaluate(ir, facts)

        # Same number of clauses
        assert len(result1.clauses) == len(result2.clauses)

        # Same match status per clause
        for c1, c2 in zip(result1.clauses, result2.clauses):
            assert c1.matched == c2.matched

        # Same actions
        assert len(result1.all_actions) == len(result2.all_actions)
        for a1, a2 in zip(result1.all_actions, result2.all_actions):
            assert a1.type == a2.type
            assert a1.message == a2.message

    def test_json_serialization_stable(self, cost_guard_dsl: str) -> None:
        """Result JSON serialization is stable."""
        ast = parse(cost_guard_dsl)
        ir = compile_policy(ast)
        facts = {"cost_per_hour": 600, "total_cost": 15000, "error_rate": 0.05}

        result1 = evaluate(ir, facts)
        result2 = evaluate(ir, facts)

        json1 = json.dumps(result1.to_dict(), sort_keys=True)
        json2 = json.dumps(result2.to_dict(), sort_keys=True)

        assert json1 == json2


# =============================================================================
# FULL PIPELINE DETERMINISM TESTS
# =============================================================================

class TestFullPipelineDeterminism:
    """Tests for full pipeline determinism: DSL → AST → IR → Result"""

    def test_full_pipeline_identical_results(self, cost_guard_dsl: str) -> None:
        """Full pipeline produces identical results across runs."""
        facts = {"cost_per_hour": 600, "total_cost": 15000, "error_rate": 0.05}

        # Run 1
        ast1 = parse(cost_guard_dsl)
        assert validate(ast1).is_valid
        ir1 = compile_policy(ast1)
        result1 = evaluate(ir1, facts)

        # Run 2
        ast2 = parse(cost_guard_dsl)
        assert validate(ast2).is_valid
        ir2 = compile_policy(ast2)
        result2 = evaluate(ir2, facts)

        # All outputs must be identical
        assert ast1.compute_hash() == ast2.compute_hash()
        assert ir1.compute_hash() == ir2.compute_hash()
        assert result1.to_dict() == result2.to_dict()

    def test_pipeline_hash_chain(self, safety_guard_dsl: str) -> None:
        """Hash chain is stable across pipeline runs."""
        # Run pipeline twice
        hashes_run1 = []
        hashes_run2 = []

        for hashes in [hashes_run1, hashes_run2]:
            ast = parse(safety_guard_dsl)
            hashes.append(ast.compute_hash())

            ir = compile_policy(ast)
            hashes.append(ir.compute_hash())

        # Both runs should produce identical hash chains
        assert hashes_run1 == hashes_run2

    def test_multiple_policies_independent(
        self,
        cost_guard_dsl: str,
        safety_guard_dsl: str,
    ) -> None:
        """Compiling/evaluating one policy doesn't affect another."""
        # Compile and evaluate cost guard
        cost_ast = parse(cost_guard_dsl)
        cost_ir = compile_policy(cost_ast)
        cost_hash_before = cost_ir.compute_hash()

        # Compile and evaluate safety guard
        safety_ast = parse(safety_guard_dsl)
        safety_ir = compile_policy(safety_ast)

        # Cost guard hash should be unchanged
        cost_hash_after = compile_policy(cost_ast).compute_hash()
        assert cost_hash_before == cost_hash_after

        # Different policies have different hashes
        assert cost_ir.compute_hash() != safety_ir.compute_hash()


# =============================================================================
# HASH STABILITY TESTS
# =============================================================================

class TestHashStability:
    """Tests for hash stability properties."""

    def test_ir_hash_is_sha256(self, cost_guard_dsl: str) -> None:
        """IR hash is valid SHA256 (64 hex chars)."""
        ast = parse(cost_guard_dsl)
        h = ir_hash(ast)

        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_different_versions_different_hash(self) -> None:
        """Different policy versions produce different hashes."""
        dsl_v1 = """
        policy Test version 1 scope ORG mode MONITOR
        when x > 0 then WARN "Alert"
        """
        dsl_v2 = """
        policy Test version 2 scope ORG mode MONITOR
        when x > 0 then WARN "Alert"
        """

        h1 = ir_hash(parse(dsl_v1))
        h2 = ir_hash(parse(dsl_v2))

        assert h1 != h2

    def test_different_values_different_hash(self) -> None:
        """Different threshold values produce different hashes."""
        dsl1 = """
        policy Test version 1 scope ORG mode MONITOR
        when x > 100 then WARN "Alert"
        """
        dsl2 = """
        policy Test version 1 scope ORG mode MONITOR
        when x > 200 then WARN "Alert"
        """

        h1 = ir_hash(parse(dsl1))
        h2 = ir_hash(parse(dsl2))

        assert h1 != h2

    def test_different_messages_different_hash(self) -> None:
        """Different warning messages produce different hashes."""
        dsl1 = """
        policy Test version 1 scope ORG mode MONITOR
        when x > 0 then WARN "Message A"
        """
        dsl2 = """
        policy Test version 1 scope ORG mode MONITOR
        when x > 0 then WARN "Message B"
        """

        h1 = ir_hash(parse(dsl1))
        h2 = ir_hash(parse(dsl2))

        assert h1 != h2

    def test_clause_order_matters_for_hash(self) -> None:
        """Different clause order produces different hashes."""
        dsl1 = """
        policy Test version 1 scope ORG mode MONITOR
        when a > 0 then WARN "A"
        when b > 0 then WARN "B"
        """
        dsl2 = """
        policy Test version 1 scope ORG mode MONITOR
        when b > 0 then WARN "B"
        when a > 0 then WARN "A"
        """

        h1 = ir_hash(parse(dsl1))
        h2 = ir_hash(parse(dsl2))

        assert h1 != h2


# =============================================================================
# BOUNDARY CONDITION TESTS
# =============================================================================

class TestBoundaryConditions:
    """Tests for determinism at boundary conditions."""

    def test_zero_value_determinism(self) -> None:
        """Zero values are handled deterministically."""
        dsl = """
        policy Test version 1 scope ORG mode MONITOR
        when x >= 0 then WARN "Non-negative"
        """
        ast = parse(dsl)
        ir = compile_policy(ast)

        result1 = evaluate(ir, {"x": 0})
        result2 = evaluate(ir, {"x": 0})

        assert result1.any_matched == result2.any_matched
        assert result1.to_dict() == result2.to_dict()

    def test_negative_value_determinism(self) -> None:
        """Negative values are handled deterministically."""
        dsl = """
        policy Test version 1 scope ORG mode MONITOR
        when x > -100 then WARN "Above threshold"
        """
        ast = parse(dsl)
        ir = compile_policy(ast)

        result1 = evaluate(ir, {"x": -50})
        result2 = evaluate(ir, {"x": -50})

        assert result1.to_dict() == result2.to_dict()

    def test_float_precision_determinism(self) -> None:
        """Float comparisons are deterministic."""
        dsl = """
        policy Test version 1 scope ORG mode MONITOR
        when rate > 0.05 then WARN "High rate"
        """
        ast = parse(dsl)
        ir = compile_policy(ast)

        # Test at exact boundary
        result1 = evaluate(ir, {"rate": 0.05})
        result2 = evaluate(ir, {"rate": 0.05})

        assert result1.any_matched == result2.any_matched
        assert result1.to_dict() == result2.to_dict()

    def test_empty_string_determinism(self) -> None:
        """Empty string values are handled deterministically."""
        dsl = """
        policy Test version 1 scope ORG mode MONITOR
        when status == "" then WARN "Empty status"
        """
        ast = parse(dsl)
        ir = compile_policy(ast)

        result1 = evaluate(ir, {"status": ""})
        result2 = evaluate(ir, {"status": ""})

        assert result1.to_dict() == result2.to_dict()
