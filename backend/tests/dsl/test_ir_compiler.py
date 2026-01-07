# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: IR Compiler tests
# Reference: PIN-341, PIN-345

"""
Tests for Policy DSL IR Compiler.

COVERAGE:
- Basic compilation
- Instruction correctness (closed set)
- Determinism (same AST → same IR → same hash)
- Complex conditions (AND, OR, nested)
- All action types
- Serialization
"""

import json
import pytest

from app.dsl.parser import parse
from app.dsl.ir_compiler import (
    compile_policy,
    ir_hash,
    PolicyIR,
    CompiledClause,
    Instruction,
    OpCode,
    IRCompiler,
)
from app.dsl.ast import (
    PolicyAST,
    PolicyMetadata,
    Clause,
    Predicate,
    ExistsPredicate,
    LogicalCondition,
    WarnAction,
    BlockAction,
    RequireApprovalAction,
    Scope,
    Mode,
    Comparator,
    LogicalOperator,
)


# =============================================================================
# INSTRUCTION TESTS
# =============================================================================

class TestInstruction:
    """Tests for Instruction structure."""

    def test_instruction_creation(self) -> None:
        """Test creating an instruction."""
        inst = Instruction(opcode=OpCode.LOAD_METRIC, operands=("cost",))
        assert inst.opcode == OpCode.LOAD_METRIC
        assert inst.operands == ("cost",)

    def test_instruction_immutability(self) -> None:
        """Test that instructions are immutable."""
        inst = Instruction(opcode=OpCode.LOAD_CONST, operands=(100,))
        with pytest.raises(AttributeError):
            inst.opcode = OpCode.AND  # type: ignore

    def test_instruction_to_dict(self) -> None:
        """Test instruction serialization."""
        inst = Instruction(opcode=OpCode.COMPARE, operands=(">",))
        d = inst.to_dict()
        assert d == {"opcode": "COMPARE", "operands": [">"]}

    def test_instruction_default_operands(self) -> None:
        """Test instruction with no operands."""
        inst = Instruction(opcode=OpCode.AND)
        assert inst.operands == ()
        assert inst.to_dict() == {"opcode": "AND", "operands": []}


# =============================================================================
# OPCODE TESTS
# =============================================================================

class TestOpCode:
    """Tests for closed instruction set."""

    def test_exactly_ten_opcodes(self) -> None:
        """Verify closed instruction set has exactly 10 opcodes."""
        opcodes = list(OpCode)
        assert len(opcodes) == 10

    def test_all_expected_opcodes_exist(self) -> None:
        """Verify all expected opcodes are present."""
        expected = [
            "LOAD_METRIC",
            "LOAD_CONST",
            "COMPARE",
            "EXISTS",
            "AND",
            "OR",
            "EMIT_WARN",
            "EMIT_BLOCK",
            "EMIT_REQUIRE_APPROVAL",
            "END",
        ]
        actual = [op.value for op in OpCode]
        assert sorted(actual) == sorted(expected)


# =============================================================================
# BASIC COMPILATION TESTS
# =============================================================================

class TestBasicCompilation:
    """Tests for basic compilation."""

    def test_compile_simple_policy(self) -> None:
        """Test compiling a simple policy."""
        ast = parse("""
        policy CostGuard
        version 1
        scope PROJECT
        mode MONITOR

        when cost > 100
        then WARN "High cost"
        """)
        ir = compile_policy(ast)

        assert ir.name == "CostGuard"
        assert ir.version == 1
        assert ir.scope == "PROJECT"
        assert ir.mode == "MONITOR"
        assert len(ir.clauses) == 1

    def test_compile_preserves_metadata(self) -> None:
        """Test that compilation preserves all metadata."""
        ast = parse("""
        policy OrgPolicy
        version 5
        scope ORG
        mode ENFORCE

        when x > 0
        then BLOCK
        """)
        ir = compile_policy(ast)

        assert ir.name == "OrgPolicy"
        assert ir.version == 5
        assert ir.scope == "ORG"
        assert ir.mode == "ENFORCE"
        assert ir.ir_version == "1.0"

    def test_compile_multiple_clauses(self) -> None:
        """Test compiling policy with multiple clauses."""
        ast = parse("""
        policy Multi
        version 1
        scope ORG
        mode ENFORCE

        when a > 1
        then WARN "A"

        when b > 2
        then BLOCK

        when c > 3
        then REQUIRE_APPROVAL
        """)
        ir = compile_policy(ast)
        assert len(ir.clauses) == 3


# =============================================================================
# CONDITION COMPILATION TESTS
# =============================================================================

class TestConditionCompilation:
    """Tests for condition compilation."""

    def test_compile_simple_predicate(self) -> None:
        """Test compiling a simple predicate."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when cost > 100
        then WARN "Alert"
        """)
        ir = compile_policy(ast)
        condition_ir = ir.clauses[0].condition_ir

        # Should have: LOAD_METRIC, LOAD_CONST, COMPARE
        assert len(condition_ir) == 3
        assert condition_ir[0].opcode == OpCode.LOAD_METRIC
        assert condition_ir[0].operands == ("cost",)
        assert condition_ir[1].opcode == OpCode.LOAD_CONST
        assert condition_ir[1].operands == (100,)
        assert condition_ir[2].opcode == OpCode.COMPARE
        assert condition_ir[2].operands == (">",)

    def test_compile_exists_predicate(self) -> None:
        """Test compiling an exists predicate."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when exists(flag)
        then WARN "Alert"
        """)
        ir = compile_policy(ast)
        condition_ir = ir.clauses[0].condition_ir

        # Should have: EXISTS
        assert len(condition_ir) == 1
        assert condition_ir[0].opcode == OpCode.EXISTS
        assert condition_ir[0].operands == ("flag",)

    def test_compile_and_condition(self) -> None:
        """Test compiling AND condition."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when a > 1 AND b > 2
        then WARN "Alert"
        """)
        ir = compile_policy(ast)
        condition_ir = ir.clauses[0].condition_ir

        # Should have: LOAD_METRIC, LOAD_CONST, COMPARE (a > 1)
        #              LOAD_METRIC, LOAD_CONST, COMPARE (b > 2)
        #              AND
        assert len(condition_ir) == 7
        assert condition_ir[6].opcode == OpCode.AND

    def test_compile_or_condition(self) -> None:
        """Test compiling OR condition."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when a > 1 OR b > 2
        then WARN "Alert"
        """)
        ir = compile_policy(ast)
        condition_ir = ir.clauses[0].condition_ir

        assert len(condition_ir) == 7
        assert condition_ir[6].opcode == OpCode.OR

    def test_compile_nested_conditions(self) -> None:
        """Test compiling nested logical conditions."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when (a > 1 AND b > 2) OR c > 3
        then WARN "Alert"
        """)
        ir = compile_policy(ast)
        condition_ir = ir.clauses[0].condition_ir

        # (a > 1): 3 instructions
        # (b > 2): 3 instructions
        # AND: 1 instruction
        # (c > 3): 3 instructions
        # OR: 1 instruction
        # Total: 11 instructions
        assert len(condition_ir) == 11
        # Last instruction should be OR
        assert condition_ir[-1].opcode == OpCode.OR

    def test_compile_all_comparators(self) -> None:
        """Test all comparator types are compiled correctly."""
        comparators = [
            (">", ">"),
            (">=", ">="),
            ("<", "<"),
            ("<=", "<="),
            ("==", "=="),
            ("!=", "!="),
        ]
        for dsl_op, ir_op in comparators:
            ast = parse(f"""
            policy Test
            version 1
            scope ORG
            mode MONITOR

            when x {dsl_op} 0
            then WARN "Alert"
            """)
            ir = compile_policy(ast)
            compare_inst = ir.clauses[0].condition_ir[2]
            assert compare_inst.opcode == OpCode.COMPARE
            assert compare_inst.operands == (ir_op,)


# =============================================================================
# ACTION COMPILATION TESTS
# =============================================================================

class TestActionCompilation:
    """Tests for action compilation."""

    def test_compile_warn_action(self) -> None:
        """Test compiling WARN action."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert message"
        """)
        ir = compile_policy(ast)
        action_ir = ir.clauses[0].action_ir

        # Should have: EMIT_WARN, END
        assert len(action_ir) == 2
        assert action_ir[0].opcode == OpCode.EMIT_WARN
        assert action_ir[0].operands == ("Alert message",)
        assert action_ir[1].opcode == OpCode.END

    def test_compile_block_action(self) -> None:
        """Test compiling BLOCK action."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then BLOCK
        """)
        ir = compile_policy(ast)
        action_ir = ir.clauses[0].action_ir

        assert len(action_ir) == 2
        assert action_ir[0].opcode == OpCode.EMIT_BLOCK
        assert action_ir[0].operands == ()
        assert action_ir[1].opcode == OpCode.END

    def test_compile_require_approval_action(self) -> None:
        """Test compiling REQUIRE_APPROVAL action."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then REQUIRE_APPROVAL
        """)
        ir = compile_policy(ast)
        action_ir = ir.clauses[0].action_ir

        assert len(action_ir) == 2
        assert action_ir[0].opcode == OpCode.EMIT_REQUIRE_APPROVAL
        assert action_ir[1].opcode == OpCode.END

    def test_compile_multiple_actions(self) -> None:
        """Test compiling multiple actions in one clause."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when x > 0
        then WARN "Alert" BLOCK REQUIRE_APPROVAL
        """)
        ir = compile_policy(ast)
        action_ir = ir.clauses[0].action_ir

        # Should have: EMIT_WARN, EMIT_BLOCK, EMIT_REQUIRE_APPROVAL, END
        assert len(action_ir) == 4
        assert action_ir[0].opcode == OpCode.EMIT_WARN
        assert action_ir[1].opcode == OpCode.EMIT_BLOCK
        assert action_ir[2].opcode == OpCode.EMIT_REQUIRE_APPROVAL
        assert action_ir[3].opcode == OpCode.END


# =============================================================================
# DETERMINISM TESTS
# =============================================================================

class TestDeterminism:
    """Tests for IR determinism."""

    def test_same_ast_same_ir(self) -> None:
        """Test that same AST produces same IR."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when cost > 100 AND error_rate > 0.1
        then WARN "Alert"
        """
        ast1 = parse(source)
        ast2 = parse(source)

        ir1 = compile_policy(ast1)
        ir2 = compile_policy(ast2)

        assert ir1.to_json() == ir2.to_json()

    def test_same_ir_same_hash(self) -> None:
        """Test that same IR produces same hash."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when cost > 100
        then WARN "Alert"
        """
        ast1 = parse(source)
        ast2 = parse(source)

        ir1 = compile_policy(ast1)
        ir2 = compile_policy(ast2)

        assert ir1.compute_hash() == ir2.compute_hash()

    def test_different_content_different_hash(self) -> None:
        """Test that different content produces different hash."""
        ast1 = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when cost > 100
        then WARN "Alert"
        """)
        ast2 = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when cost > 200
        then WARN "Alert"
        """)

        ir1 = compile_policy(ast1)
        ir2 = compile_policy(ast2)

        assert ir1.compute_hash() != ir2.compute_hash()

    def test_ir_hash_convenience_function(self) -> None:
        """Test ir_hash convenience function."""
        source = """
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """
        ast = parse(source)

        hash1 = ir_hash(ast)
        hash2 = compile_policy(ast).compute_hash()

        assert hash1 == hash2

    def test_hash_is_stable_hex(self) -> None:
        """Test that hash is a valid hex string."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        h = ir_hash(ast)

        # SHA256 produces 64 hex characters
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestSerialization:
    """Tests for IR serialization."""

    def test_compiled_clause_to_dict(self) -> None:
        """Test CompiledClause serialization."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        ir = compile_policy(ast)
        clause_dict = ir.clauses[0].to_dict()

        assert "condition" in clause_dict
        assert "actions" in clause_dict
        assert isinstance(clause_dict["condition"], list)
        assert isinstance(clause_dict["actions"], list)

    def test_policy_ir_to_dict(self) -> None:
        """Test PolicyIR serialization."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        ir = compile_policy(ast)
        d = ir.to_dict()

        assert d["ir_version"] == "1.0"
        assert d["name"] == "Test"
        assert d["version"] == 1
        assert d["scope"] == "ORG"
        assert d["mode"] == "MONITOR"
        assert len(d["clauses"]) == 1

    def test_policy_ir_to_json(self) -> None:
        """Test PolicyIR JSON serialization."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        ir = compile_policy(ast)
        json_str = ir.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["name"] == "Test"

    def test_json_is_sorted(self) -> None:
        """Test that JSON keys are sorted (for determinism)."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        ir = compile_policy(ast)
        json_str = ir.to_json()

        # Keys should appear in sorted order
        assert json_str.index('"clauses"') < json_str.index('"ir_version"')
        assert json_str.index('"ir_version"') < json_str.index('"mode"')


# =============================================================================
# INSTRUCTION COUNT TESTS
# =============================================================================

class TestInstructionCount:
    """Tests for instruction counting."""

    def test_instruction_count_simple(self) -> None:
        """Test instruction count for simple policy."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode MONITOR

        when x > 0
        then WARN "Alert"
        """)
        ir = compile_policy(ast)

        # Condition: LOAD_METRIC, LOAD_CONST, COMPARE = 3
        # Actions: EMIT_WARN, END = 2
        # Total: 5
        assert ir.instruction_count == 5

    def test_instruction_count_complex(self) -> None:
        """Test instruction count for complex policy."""
        ast = parse("""
        policy Test
        version 1
        scope ORG
        mode ENFORCE

        when a > 1 AND b > 2
        then WARN "W1" BLOCK

        when exists(flag)
        then REQUIRE_APPROVAL
        """)
        ir = compile_policy(ast)

        # Clause 1 condition: 3 + 3 + 1 (AND) = 7
        # Clause 1 actions: 2 + 1 (END) = 3
        # Clause 2 condition: 1 (EXISTS)
        # Clause 2 actions: 1 + 1 (END) = 2
        # Total: 7 + 3 + 1 + 2 = 13
        assert ir.instruction_count == 13


# =============================================================================
# FULL POLICY TESTS
# =============================================================================

class TestFullPolicies:
    """Integration tests with full policies."""

    def test_cost_guard_policy(self) -> None:
        """Test compiling a realistic cost guard policy."""
        ast = parse("""
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
        """)
        ir = compile_policy(ast)

        assert ir.name == "CostGuard"
        assert ir.version == 3
        assert len(ir.clauses) == 3

        # Verify hash is stable
        hash1 = ir.compute_hash()
        ir2 = compile_policy(ast)
        hash2 = ir2.compute_hash()
        assert hash1 == hash2

    def test_safety_policy(self) -> None:
        """Test compiling a realistic safety policy."""
        ast = parse("""
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
        """)
        ir = compile_policy(ast)

        assert ir.name == "SafetyGuard"
        assert len(ir.clauses) == 3

        # Check that EXISTS is used in second clause
        clause2_condition = ir.clauses[1].condition_ir
        assert clause2_condition[0].opcode == OpCode.EXISTS
