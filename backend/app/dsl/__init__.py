# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Policy DSL module initialization
# Reference: PIN-341, PIN-345

"""
GC_L Policy DSL Module

This module provides the core DSL infrastructure for policy evaluation:
- AST definitions (immutable, typed structures)
- Parser (DSL text → AST)
- Validator (semantic rule enforcement)
- IR Compiler (AST → bytecode)
- Interpreter (pure evaluation)

GOVERNANCE: This module is PURE. No I/O, no DB, no side effects.
"""

from app.dsl.ast import (
    PolicyAST,
    PolicyMetadata,
    Clause,
    Condition,
    Predicate,
    ExistsPredicate,
    LogicalCondition,
    WarnAction,
    BlockAction,
    RequireApprovalAction,
    Scope,
    Mode,
    Comparator,
    Action,
    LogicalOperator,
)

from app.dsl.parser import (
    parse,
    parse_condition,
    ParseError,
    ParseLocation,
)

from app.dsl.validator import (
    validate,
    is_valid,
    PolicyValidator,
    ValidationResult,
    ValidationIssue,
    Severity,
)

from app.dsl.ir_compiler import (
    compile_policy,
    ir_hash,
    PolicyIR,
    CompiledClause,
    Instruction,
    OpCode,
    IRCompiler,
)

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

__all__ = [
    # AST Types
    "PolicyAST",
    "PolicyMetadata",
    "Clause",
    "Condition",
    "Predicate",
    "ExistsPredicate",
    "LogicalCondition",
    "WarnAction",
    "BlockAction",
    "RequireApprovalAction",
    "Scope",
    "Mode",
    "Comparator",
    "LogicalOperator",
    "Action",
    # Parser
    "parse",
    "parse_condition",
    "ParseError",
    "ParseLocation",
    # Validator
    "validate",
    "is_valid",
    "PolicyValidator",
    "ValidationResult",
    "ValidationIssue",
    "Severity",
    # IR Compiler
    "compile_policy",
    "ir_hash",
    "PolicyIR",
    "CompiledClause",
    "Instruction",
    "OpCode",
    "IRCompiler",
    # Interpreter
    "evaluate",
    "evaluate_policy",
    "Interpreter",
    "EvaluationResult",
    "ClauseResult",
    "ActionResult",
    "EvaluationError",
    "TypeMismatchError",
    "MissingMetricError",
]
