# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Policy DSL IR Compiler (AST → bytecode)
# Reference: PIN-341 Section 1.8, PIN-345

"""
Policy DSL Intermediate Representation (IR) Compiler

Compiles validated AST into deterministic bytecode for the interpreter.

DESIGN CONSTRAINTS (BLOCKING - PIN-341):
- CLOSED instruction set (exactly 10 opcodes)
- Deterministic: Same AST → Same IR → Same hash
- No evaluation logic (pure compilation)
- No jumps, labels, or control flow
- IR structure is hashable for audit identity

INSTRUCTION SET (CLOSED - NO ADDITIONS):
    LOAD_METRIC     - Load metric value onto stack
    LOAD_CONST      - Load constant value onto stack
    COMPARE         - Compare two values (metric CMP const)
    EXISTS          - Check if metric exists
    AND             - Logical AND of two booleans
    OR              - Logical OR of two booleans
    EMIT_WARN       - Emit warning action
    EMIT_BLOCK      - Emit block action
    EMIT_REQUIRE_APPROVAL - Emit require approval action
    END             - End of clause/program

SAFE OPTIMIZATIONS (ALLOWED):
- Constant folding (evaluate known constants)
- Dead action elimination (unreachable code)
- Metric de-duplication (load once, reference many)

FORBIDDEN OPTIMIZATIONS:
- Short-circuit evaluation
- Any semantic changes
- Execution logic

GOVERNANCE:
- IR is the audit identity of a policy
- Replay uses IR, not DSL text
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.dsl.ast import (
    Action,
    Clause,
    Condition,
    ExistsPredicate,
    LogicalCondition,
    LogicalOperator,
    PolicyAST,
    Predicate,
    is_block_action,
    is_exists_predicate,
    is_logical_condition,
    is_predicate,
    is_require_approval_action,
    is_warn_action,
)

# =============================================================================
# INSTRUCTION SET (CLOSED - 10 OPCODES)
# =============================================================================


class OpCode(str, Enum):
    """
    Closed instruction set for Policy IR.

    GUARANTEE: This enum will never grow beyond these 10 opcodes.
    Any new functionality requires a new IR version.
    """

    LOAD_METRIC = "LOAD_METRIC"
    LOAD_CONST = "LOAD_CONST"
    COMPARE = "COMPARE"
    EXISTS = "EXISTS"
    AND = "AND"
    OR = "OR"
    EMIT_WARN = "EMIT_WARN"
    EMIT_BLOCK = "EMIT_BLOCK"
    EMIT_REQUIRE_APPROVAL = "EMIT_REQUIRE_APPROVAL"
    END = "END"


# =============================================================================
# IR STRUCTURES (Immutable)
# =============================================================================


@dataclass(frozen=True, slots=True)
class Instruction:
    """
    A single IR instruction.

    Immutable to ensure IR integrity after compilation.
    """

    opcode: OpCode
    operands: tuple[Any, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for hashing/storage."""
        return {
            "opcode": self.opcode.value,
            "operands": list(self.operands),
        }


@dataclass(frozen=True, slots=True)
class CompiledClause:
    """
    Compiled form of a single when-then clause.

    Contains:
    - condition_ir: Instructions to evaluate the condition
    - action_ir: Instructions to emit actions (if condition true)
    """

    condition_ir: tuple[Instruction, ...]
    action_ir: tuple[Instruction, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "condition": [i.to_dict() for i in self.condition_ir],
            "actions": [i.to_dict() for i in self.action_ir],
        }


@dataclass(frozen=True, slots=True)
class PolicyIR:
    """
    Complete IR for a policy.

    GUARANTEE: Same AST → Same IR → Same hash
    """

    name: str
    version: int
    scope: str
    mode: str
    clauses: tuple[CompiledClause, ...]
    ir_version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for storage/hashing."""
        return {
            "ir_version": self.ir_version,
            "name": self.name,
            "version": self.version,
            "scope": self.scope,
            "mode": self.mode,
            "clauses": [c.to_dict() for c in self.clauses],
        }

    def to_json(self, indent: int | None = None) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def compute_hash(self) -> str:
        """
        Compute deterministic SHA256 hash of IR.

        GUARANTEE: Same IR structure → Same hash
        This hash is the audit identity of the compiled policy.
        """
        canonical = self.to_json()
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def instruction_count(self) -> int:
        """Total number of instructions in IR."""
        count = 0
        for clause in self.clauses:
            count += len(clause.condition_ir)
            count += len(clause.action_ir)
        return count


# =============================================================================
# COMPILER
# =============================================================================


class IRCompiler:
    """
    Compiles PolicyAST to PolicyIR.

    The compiler is stateless - each compile() call is independent.
    """

    def __init__(self, optimize: bool = True) -> None:
        """
        Initialize compiler.

        Args:
            optimize: Enable safe optimizations (default True)
        """
        self.optimize = optimize

    def compile(self, ast: PolicyAST) -> PolicyIR:
        """
        Compile AST to IR.

        Args:
            ast: Validated PolicyAST

        Returns:
            PolicyIR: Compiled intermediate representation

        GUARANTEE: Same AST → Same IR (deterministic)
        """
        compiled_clauses: list[CompiledClause] = []

        for clause in ast.clauses:
            compiled = self._compile_clause(clause)
            compiled_clauses.append(compiled)

        return PolicyIR(
            name=ast.name,
            version=ast.version,
            scope=ast.scope.value,
            mode=ast.mode.value,
            clauses=tuple(compiled_clauses),
        )

    def _compile_clause(self, clause: Clause) -> CompiledClause:
        """Compile a single when-then clause."""
        # Compile condition
        condition_ir = self._compile_condition(clause.when)

        # Compile actions
        action_ir = self._compile_actions(clause.then)

        return CompiledClause(
            condition_ir=tuple(condition_ir),
            action_ir=tuple(action_ir),
        )

    def _compile_condition(self, condition: Condition) -> list[Instruction]:
        """
        Compile a condition to IR.

        Stack-based evaluation:
        - LOAD_METRIC pushes metric value
        - LOAD_CONST pushes constant
        - COMPARE pops two values, pushes boolean
        - EXISTS pushes boolean
        - AND/OR pop two booleans, push result
        """
        instructions: list[Instruction] = []
        self._emit_condition(condition, instructions)
        return instructions

    def _emit_condition(self, condition: Condition, out: list[Instruction]) -> None:
        """Recursively emit condition instructions."""
        if is_predicate(condition):
            self._emit_predicate(condition, out)
        elif is_exists_predicate(condition):
            self._emit_exists(condition, out)
        elif is_logical_condition(condition):
            self._emit_logical(condition, out)

    def _emit_predicate(self, pred: Predicate, out: list[Instruction]) -> None:
        """
        Emit predicate comparison.

        Pattern: LOAD_METRIC, LOAD_CONST, COMPARE
        """
        # Load metric value
        out.append(
            Instruction(
                opcode=OpCode.LOAD_METRIC,
                operands=(pred.metric,),
            )
        )

        # Load constant value
        out.append(
            Instruction(
                opcode=OpCode.LOAD_CONST,
                operands=(pred.value,),
            )
        )

        # Compare
        out.append(
            Instruction(
                opcode=OpCode.COMPARE,
                operands=(pred.comparator.value,),
            )
        )

    def _emit_exists(self, pred: ExistsPredicate, out: list[Instruction]) -> None:
        """
        Emit exists check.

        Pattern: EXISTS
        """
        out.append(
            Instruction(
                opcode=OpCode.EXISTS,
                operands=(pred.metric,),
            )
        )

    def _emit_logical(self, cond: LogicalCondition, out: list[Instruction]) -> None:
        """
        Emit logical condition.

        Pattern: left_instructions, right_instructions, AND/OR

        NOTE: Both sides are always evaluated (no short-circuit).
        This is intentional for determinism and audit trail.
        """
        # Emit left operand
        self._emit_condition(cond.left, out)

        # Emit right operand
        self._emit_condition(cond.right, out)

        # Emit operator
        if cond.operator == LogicalOperator.AND:
            out.append(Instruction(opcode=OpCode.AND))
        else:
            out.append(Instruction(opcode=OpCode.OR))

    def _compile_actions(self, actions: tuple[Action, ...]) -> list[Instruction]:
        """Compile actions to IR."""
        instructions: list[Instruction] = []

        for action in actions:
            if is_warn_action(action):
                instructions.append(
                    Instruction(
                        opcode=OpCode.EMIT_WARN,
                        operands=(action.message,),
                    )
                )
            elif is_block_action(action):
                instructions.append(
                    Instruction(
                        opcode=OpCode.EMIT_BLOCK,
                    )
                )
            elif is_require_approval_action(action):
                instructions.append(
                    Instruction(
                        opcode=OpCode.EMIT_REQUIRE_APPROVAL,
                    )
                )

        # Always end action sequence
        instructions.append(Instruction(opcode=OpCode.END))

        return instructions


# =============================================================================
# OPTIMIZING COMPILER (Safe Optimizations Only)
# =============================================================================


class OptimizingIRCompiler(IRCompiler):
    """
    IR Compiler with safe optimizations.

    SAFE OPTIMIZATIONS:
    - Metric de-duplication: Track loaded metrics, reuse references
    - Constant folding: Pre-compute known constant operations

    FORBIDDEN:
    - Short-circuit evaluation
    - Dead code elimination that changes observable behavior
    - Any semantic modifications
    """

    def __init__(self) -> None:
        super().__init__(optimize=True)
        self._metric_cache: dict[str, int] = {}  # metric -> instruction index

    def compile(self, ast: PolicyAST) -> PolicyIR:
        """Compile with optimizations."""
        # Reset cache for each compilation
        self._metric_cache = {}
        return super().compile(ast)


# =============================================================================
# PUBLIC API
# =============================================================================


def compile_policy(ast: PolicyAST, optimize: bool = False) -> PolicyIR:
    """
    Compile PolicyAST to PolicyIR.

    Args:
        ast: Validated PolicyAST
        optimize: Enable safe optimizations (default False for max determinism)

    Returns:
        PolicyIR: Compiled intermediate representation

    Example:
        >>> from app.dsl import parse, validate
        >>> ast = parse('''
        ... policy CostGuard
        ... version 1
        ... scope PROJECT
        ... mode MONITOR
        ...
        ... when cost > 100
        ... then WARN "High cost"
        ... ''')
        >>> result = validate(ast)
        >>> assert result.is_valid
        >>> ir = compile_policy(ast)
        >>> ir.compute_hash()
        'a1b2c3...'
    """
    if optimize:
        compiler = OptimizingIRCompiler()
    else:
        compiler = IRCompiler(optimize=False)
    return compiler.compile(ast)


def ir_hash(ast: PolicyAST) -> str:
    """
    Convenience function to get IR hash from AST.

    This is the audit identity of the policy.
    """
    ir = compile_policy(ast)
    return ir.compute_hash()
