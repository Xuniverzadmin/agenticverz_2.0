# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Policy DSL Interpreter (pure IR evaluation)
# Reference: PIN-341 Section 1.8, PIN-345

"""
Policy DSL Interpreter

Pure evaluation of compiled IR against runtime facts.

DESIGN CONSTRAINTS (BLOCKING - PIN-341):
- PURE: No side effects, no I/O, no DB, no network
- NO CONTEXT: No tenants, actors, permissions, time
- DESCRIPTIVE OUTPUT: Returns what is true, not what to do
- STACK-BASED: Explicit stack for condition evaluation
- NO COERCION: Type mismatches raise errors

INPUT:
- PolicyIR: Compiled intermediate representation
- Facts: dict[str, value] - runtime metric values

OUTPUT:
- EvaluationResult: Describes which clauses matched and what actions apply

GOVERNANCE:
- Interpreter output defines policy truth
- IR compiler and future JIT must conform to this
- Replay uses interpreter, always
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.dsl.ir_compiler import (
    PolicyIR,
    CompiledClause,
    Instruction,
    OpCode,
)


# =============================================================================
# ERROR TYPES
# =============================================================================

class EvaluationError(Exception):
    """
    Raised when evaluation fails.

    This is NOT a policy violation - it's a runtime error
    (e.g., type mismatch, missing required metric).
    """

    def __init__(self, message: str, instruction: Instruction | None = None) -> None:
        self.message = message
        self.instruction = instruction
        if instruction:
            super().__init__(f"{message} (at {instruction.opcode.value})")
        else:
            super().__init__(message)


class TypeMismatchError(EvaluationError):
    """Raised when types are incompatible for comparison."""
    pass


class MissingMetricError(EvaluationError):
    """Raised when a required metric is not in facts."""
    pass


# =============================================================================
# RESULT TYPES (Immutable, Descriptive)
# =============================================================================

@dataclass(frozen=True, slots=True)
class ActionResult:
    """
    A single action from evaluation.

    This is DESCRIPTIVE - it says what action applies,
    not what to do about it.
    """
    type: str  # "WARN", "BLOCK", "REQUIRE_APPROVAL"
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.type}
        if self.message is not None:
            result["message"] = self.message
        return result


@dataclass(frozen=True, slots=True)
class ClauseResult:
    """
    Evaluation result for a single clause.

    DESCRIPTIVE: Says whether the clause matched and what actions apply.
    """
    matched: bool
    actions: tuple[ActionResult, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matched": self.matched,
            "actions": [a.to_dict() for a in self.actions] if self.matched else [],
        }


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """
    Complete evaluation result for a policy.

    DESCRIPTIVE OUTPUT:
    - any_matched: Did any clause match?
    - clauses: Per-clause results
    - all_actions: Aggregated actions from all matching clauses

    This tells you WHAT IS TRUE, not what to do about it.
    """
    any_matched: bool
    clauses: tuple[ClauseResult, ...]
    all_actions: tuple[ActionResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "any_matched": self.any_matched,
            "clauses": [c.to_dict() for c in self.clauses],
            "all_actions": [a.to_dict() for a in self.all_actions],
        }

    @property
    def has_block(self) -> bool:
        """Check if any action is BLOCK."""
        return any(a.type == "BLOCK" for a in self.all_actions)

    @property
    def has_require_approval(self) -> bool:
        """Check if any action is REQUIRE_APPROVAL."""
        return any(a.type == "REQUIRE_APPROVAL" for a in self.all_actions)

    @property
    def warnings(self) -> list[str]:
        """Get all warning messages."""
        return [a.message for a in self.all_actions if a.type == "WARN" and a.message]


# =============================================================================
# INTERPRETER
# =============================================================================

class Interpreter:
    """
    Pure interpreter for Policy IR.

    PURITY GUARANTEE:
    - No side effects
    - No access to DB, time, network, globals
    - No knowledge of tenants, actors, permissions

    Input = IR + facts
    Output = EvaluationResult
    """

    def __init__(self) -> None:
        """Initialize interpreter (stateless)."""
        pass

    def evaluate(
        self,
        ir: PolicyIR,
        facts: dict[str, Any],
    ) -> EvaluationResult:
        """
        Evaluate policy IR against facts.

        Args:
            ir: Compiled PolicyIR
            facts: dict mapping metric names to values

        Returns:
            EvaluationResult describing what matched

        Raises:
            EvaluationError: On runtime errors (type mismatch, etc.)

        PURITY: This function has no side effects.
        """
        clause_results: list[ClauseResult] = []
        all_actions: list[ActionResult] = []

        for clause in ir.clauses:
            result = self._evaluate_clause(clause, facts)
            clause_results.append(result)

            if result.matched:
                all_actions.extend(result.actions)

        any_matched = any(c.matched for c in clause_results)

        return EvaluationResult(
            any_matched=any_matched,
            clauses=tuple(clause_results),
            all_actions=tuple(all_actions),
        )

    def _evaluate_clause(
        self,
        clause: CompiledClause,
        facts: dict[str, Any],
    ) -> ClauseResult:
        """Evaluate a single clause."""
        # Evaluate condition
        matched = self._evaluate_condition(clause.condition_ir, facts)

        if not matched:
            return ClauseResult(matched=False)

        # Collect actions
        actions = self._collect_actions(clause.action_ir)

        return ClauseResult(matched=True, actions=tuple(actions))

    def _evaluate_condition(
        self,
        instructions: tuple[Instruction, ...],
        facts: dict[str, Any],
    ) -> bool:
        """
        Evaluate condition instructions using a stack.

        Stack-based evaluation:
        - LOAD_METRIC: push facts[metric]
        - LOAD_CONST: push constant
        - COMPARE: pop two values, push comparison result
        - EXISTS: push whether metric exists
        - AND/OR: pop two booleans, push logical result
        """
        stack: list[Any] = []

        for inst in instructions:
            self._execute_instruction(inst, facts, stack)

        # Final stack should have exactly one boolean
        if len(stack) != 1:
            raise EvaluationError(
                f"Invalid stack state after condition evaluation: {len(stack)} items"
            )

        result = stack[0]
        if not isinstance(result, bool):
            raise EvaluationError(
                f"Condition must evaluate to bool, got {type(result).__name__}"
            )

        return result

    def _execute_instruction(
        self,
        inst: Instruction,
        facts: dict[str, Any],
        stack: list[Any],
    ) -> None:
        """Execute a single instruction."""
        opcode = inst.opcode

        if opcode == OpCode.LOAD_METRIC:
            metric = inst.operands[0]
            if metric not in facts:
                raise MissingMetricError(
                    f"Metric '{metric}' not found in facts",
                    inst,
                )
            stack.append(facts[metric])

        elif opcode == OpCode.LOAD_CONST:
            value = inst.operands[0]
            stack.append(value)

        elif opcode == OpCode.COMPARE:
            comparator = inst.operands[0]
            if len(stack) < 2:
                raise EvaluationError("Stack underflow in COMPARE", inst)

            right = stack.pop()  # constant
            left = stack.pop()   # metric value

            result = self._compare(left, comparator, right, inst)
            stack.append(result)

        elif opcode == OpCode.EXISTS:
            metric = inst.operands[0]
            exists = metric in facts
            stack.append(exists)

        elif opcode == OpCode.AND:
            if len(stack) < 2:
                raise EvaluationError("Stack underflow in AND", inst)

            right = stack.pop()
            left = stack.pop()

            if not isinstance(left, bool) or not isinstance(right, bool):
                raise TypeMismatchError(
                    f"AND requires booleans, got {type(left).__name__} and {type(right).__name__}",
                    inst,
                )

            stack.append(left and right)

        elif opcode == OpCode.OR:
            if len(stack) < 2:
                raise EvaluationError("Stack underflow in OR", inst)

            right = stack.pop()
            left = stack.pop()

            if not isinstance(left, bool) or not isinstance(right, bool):
                raise TypeMismatchError(
                    f"OR requires booleans, got {type(left).__name__} and {type(right).__name__}",
                    inst,
                )

            stack.append(left or right)

        elif opcode in (OpCode.EMIT_WARN, OpCode.EMIT_BLOCK,
                        OpCode.EMIT_REQUIRE_APPROVAL, OpCode.END):
            # Action opcodes should not appear in condition IR
            raise EvaluationError(
                f"Action opcode {opcode.value} in condition IR",
                inst,
            )

        else:
            raise EvaluationError(f"Unknown opcode: {opcode}", inst)

    def _compare(
        self,
        left: Any,
        comparator: str,
        right: Any,
        inst: Instruction,
    ) -> bool:
        """
        Perform comparison.

        NO COERCION: Types must be compatible or error.
        """
        # Check type compatibility
        if not self._types_compatible(left, right):
            raise TypeMismatchError(
                f"Cannot compare {type(left).__name__} with {type(right).__name__}",
                inst,
            )

        if comparator == ">":
            return left > right
        elif comparator == ">=":
            return left >= right
        elif comparator == "<":
            return left < right
        elif comparator == "<=":
            return left <= right
        elif comparator == "==":
            return left == right
        elif comparator == "!=":
            return left != right
        else:
            raise EvaluationError(f"Unknown comparator: {comparator}", inst)

    def _types_compatible(self, left: Any, right: Any) -> bool:
        """
        Check if types are compatible for comparison.

        Rules:
        - int and float are compatible (numeric)
        - Same types are compatible
        - bool only with bool
        - str only with str
        """
        # Numeric types are compatible
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            # But not bool (bool is subclass of int in Python)
            if isinstance(left, bool) or isinstance(right, bool):
                return type(left) == type(right)
            return True

        # Same types are compatible
        return type(left) == type(right)

    def _collect_actions(
        self,
        instructions: tuple[Instruction, ...],
    ) -> list[ActionResult]:
        """Collect action results from action IR."""
        actions: list[ActionResult] = []

        for inst in instructions:
            if inst.opcode == OpCode.EMIT_WARN:
                message = inst.operands[0] if inst.operands else None
                actions.append(ActionResult(type="WARN", message=message))

            elif inst.opcode == OpCode.EMIT_BLOCK:
                actions.append(ActionResult(type="BLOCK"))

            elif inst.opcode == OpCode.EMIT_REQUIRE_APPROVAL:
                actions.append(ActionResult(type="REQUIRE_APPROVAL"))

            elif inst.opcode == OpCode.END:
                break  # End of action sequence

            else:
                raise EvaluationError(
                    f"Unexpected opcode in action IR: {inst.opcode.value}",
                    inst,
                )

        return actions


# =============================================================================
# PUBLIC API
# =============================================================================

def evaluate(
    ir: PolicyIR,
    facts: dict[str, Any],
) -> EvaluationResult:
    """
    Evaluate policy IR against facts.

    This is the CANONICAL evaluation function.
    All other evaluation paths (JIT, cached, etc.) must produce
    identical results.

    Args:
        ir: Compiled PolicyIR
        facts: dict mapping metric names to values

    Returns:
        EvaluationResult describing what matched

    Raises:
        EvaluationError: On runtime errors

    Example:
        >>> from app.dsl import parse, validate, compile_policy
        >>> ast = parse('''
        ... policy CostGuard
        ... version 1
        ... scope PROJECT
        ... mode MONITOR
        ...
        ... when cost > 100
        ... then WARN "High cost"
        ... ''')
        >>> ir = compile_policy(ast)
        >>> result = evaluate(ir, {"cost": 150})
        >>> result.any_matched
        True
        >>> result.all_actions[0].type
        'WARN'
    """
    interpreter = Interpreter()
    return interpreter.evaluate(ir, facts)


def evaluate_policy(
    ir: PolicyIR,
    facts: dict[str, Any],
    strict: bool = True,
) -> EvaluationResult:
    """
    Evaluate policy with optional strict mode.

    Args:
        ir: Compiled PolicyIR
        facts: dict mapping metric names to values
        strict: If True, missing metrics raise error.
                If False, missing metrics treated as not-exists.

    Returns:
        EvaluationResult describing what matched

    Note: strict=False is useful for partial evaluation,
          but strict=True is required for audit-grade evaluation.
    """
    if strict:
        return evaluate(ir, facts)

    # Non-strict mode: wrap evaluation to handle missing metrics
    # by treating them as non-matching (exists returns False)
    interpreter = _LenientInterpreter()
    return interpreter.evaluate(ir, facts)


class _LenientInterpreter(Interpreter):
    """
    Lenient interpreter that treats missing metrics as non-matching.

    NOT for audit-grade evaluation - only for previews/simulation.
    """

    def _execute_instruction(
        self,
        inst: Instruction,
        facts: dict[str, Any],
        stack: list[Any],
    ) -> None:
        """Execute instruction with lenient missing metric handling."""
        if inst.opcode == OpCode.LOAD_METRIC:
            metric = inst.operands[0]
            if metric not in facts:
                # Push a sentinel that will cause comparison to fail
                stack.append(_MISSING_SENTINEL)
                return

        super()._execute_instruction(inst, facts, stack)

    def _compare(
        self,
        left: Any,
        comparator: str,
        right: Any,
        inst: Instruction,
    ) -> bool:
        """Compare with sentinel handling."""
        if left is _MISSING_SENTINEL or right is _MISSING_SENTINEL:
            return False  # Missing metric = comparison fails
        return super()._compare(left, comparator, right, inst)


# Sentinel for missing metrics in lenient mode
class _MissingSentinel:
    """Sentinel value for missing metrics."""
    pass


_MISSING_SENTINEL = _MissingSentinel()
