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
    Action,
    BlockAction,
    Clause,
    Comparator,
    Condition,
    ExistsPredicate,
    LogicalCondition,
    LogicalOperator,
    Mode,
    PolicyAST,
    PolicyMetadata,
    Predicate,
    RequireApprovalAction,
    Scope,
    WarnAction,
)
from app.dsl.interpreter import (
    ActionResult,
    ClauseResult,
    EvaluationError,
    EvaluationResult,
    Interpreter,
    MissingMetricError,
    TypeMismatchError,
    evaluate,
    evaluate_policy,
)
from app.dsl.ir_compiler import (
    CompiledClause,
    Instruction,
    IRCompiler,
    OpCode,
    PolicyIR,
    compile_policy,
    ir_hash,
)
from app.dsl.parser import (
    ParseError,
    ParseLocation,
    parse,
    parse_condition,
)
from app.dsl.validator import (
    PolicyValidator,
    Severity,
    ValidationIssue,
    ValidationResult,
    is_valid,
    validate,
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
