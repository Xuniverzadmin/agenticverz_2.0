# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policies (via driver)
#   Writes: none
# Role: Deterministic policy execution engine
# Callers: policy evaluators, workers
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-514, PIN-515, Policy System

# M20 Policy Runtime - Deterministic Engine
# MN-OS Layer 0: No randomness, reproducible execution
"""
Deterministic execution engine for PLang v2.0.

Key principles:
- NO RANDOMNESS: Every execution is reproducible
- GOVERNANCE-FIRST: Safety checks before any action
- AUDITABLE: Full execution trace for debugging
- DETERMINISTIC: Same input = same output

Integration points:
- M18: Intent emission for execution
- M19: Policy validation before actions
- M4: Execution plan generation
"""

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

from app.hoc.cus.policies.L5_schemas.policy_check import PolicyCheckValidator

# Safe regex constants
MAX_PATTERN_LEN = 128
MAX_INPUT_LEN = 1024
_REDOS_PATTERN = re.compile(r"(.+[+*])\1|\\[0-9]")


def safe_regex_match(input_str: str, pattern: str) -> bool:
    """
    Safe regex match with length limits and ReDoS guards.

    Returns False on any failure (fail-closed).
    """
    if not isinstance(input_str, str) or not isinstance(pattern, str):
        return False
    if len(pattern) > MAX_PATTERN_LEN or len(input_str) > MAX_INPUT_LEN:
        return False
    # Reject patterns with nested quantifiers or backreferences
    if _REDOS_PATTERN.search(pattern):
        return False
    try:
        return bool(re.search(pattern, input_str))
    except re.error:
        return False

from app.policy.compiler.grammar import ActionType, PolicyCategory
from app.policy.ir.ir_nodes import (
    IRAction,
    IRBinaryOp,
    IRCall,
    IRCheckPolicy,
    IRCompare,
    IREmitIntent,
    IRFunction,
    IRInstruction,
    IRJump,
    IRJumpIf,
    IRLoadConst,
    IRLoadVar,
    IRModule,
    IRReturn,
    IRStoreVar,
    IRUnaryOp,
)
from app.hoc.cus.policies.L5_engines.intent import Intent, IntentEmitter, IntentPayload, IntentType


class ExecutionStatus(Enum):
    """Status of policy execution."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    BLOCKED = auto()


@dataclass
class ExecutionContext:
    """
    Execution context for policy evaluation.

    Contains all runtime state needed for deterministic execution.
    """

    # Unique execution ID (deterministic from inputs)
    execution_id: str = ""

    # Input context
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None

    # Variables (deterministic state)
    variables: Dict[str, Any] = field(default_factory=dict)

    # Call stack for function calls
    call_stack: List[str] = field(default_factory=list)

    # Execution trace for audit
    trace: List[Dict[str, Any]] = field(default_factory=list)

    # Results
    final_action: Optional[ActionType] = None
    emitted_intents: List[Intent] = field(default_factory=list)

    # Timing (deterministic - based on step count, not wall clock)
    step_count: int = 0
    max_steps: int = 10000  # Prevent infinite loops

    # Status
    status: ExecutionStatus = ExecutionStatus.PENDING

    def __post_init__(self):
        if not self.execution_id:
            self.execution_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate deterministic execution ID from context."""
        content = f"{self.request_id}:{self.user_id}:{self.agent_id}"
        return f"exec_{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def get_variable(self, name: str) -> Any:
        """Get a variable value."""
        # Handle context accessors
        if name == "ctx":
            return self
        if name == "request":
            return {"id": self.request_id}
        if name == "user":
            return {"id": self.user_id}
        if name == "agent":
            return {"id": self.agent_id}
        return self.variables.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value."""
        self.variables[name] = value

    def push_call(self, function_name: str) -> None:
        """Push function onto call stack."""
        self.call_stack.append(function_name)

    def pop_call(self) -> Optional[str]:
        """Pop function from call stack."""
        if self.call_stack:
            return self.call_stack.pop()
        return None

    def add_trace(self, event: str, data: Dict[str, Any]) -> None:
        """Add event to execution trace."""
        self.trace.append(
            {
                "step": self.step_count,
                "event": event,
                "data": data,
            }
        )


@dataclass
class ExecutionResult:
    """
    Result of policy execution.

    Contains final decision, intents, and audit trail.
    """

    success: bool
    action: Optional[ActionType] = None
    intents: List[Intent] = field(default_factory=list)
    trace: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    execution_id: str = ""
    step_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "success": self.success,
            "action": self.action.value if self.action else None,
            "intents": [i.to_dict() for i in self.intents],
            "trace_summary": {
                "total_steps": self.step_count,
                "events": len(self.trace),
            },
            "error": self.error,
            "execution_id": self.execution_id,
        }


class DeterministicEngine:
    """
    Deterministic policy execution engine.

    Executes compiled IR with:
    - No randomness (reproducible)
    - Governance validation
    - Intent emission
    - Full audit trail
    """

    def __init__(
        self,
        policy_validator: Optional[PolicyCheckValidator] = None,
        intent_validator=None,
        emission_sink=None,
    ):
        self.intent_emitter = IntentEmitter(
            intent_validator=intent_validator,
            emission_sink=emission_sink,
        )
        self._policy_validator = policy_validator
        self._builtin_functions: Dict[str, Callable[..., Any]] = self._register_builtins()

    def _register_builtins(self) -> Dict[str, Callable[..., Any]]:
        """Register built-in functions."""
        return {
            "contains": lambda s, sub: sub in s if s else False,
            "startswith": lambda s, pre: s.startswith(pre) if s else False,
            "endswith": lambda s, suf: s.endswith(suf) if s else False,
            "len": lambda x: len(x) if x else 0,
            "lower": lambda s: s.lower() if s else "",
            "upper": lambda s: s.upper() if s else "",
            "matches": lambda s, pattern: safe_regex_match(s, pattern),
            "in_list": lambda item, lst: item in lst if lst else False,
            "is_empty": lambda x: not x,
            "__getattr__": lambda obj, attr: obj.get(attr) if isinstance(obj, dict) else getattr(obj, attr, None),
        }

    async def execute(
        self,
        module: IRModule,
        context: ExecutionContext,
        entry_function: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute a compiled policy module.

        Args:
            module: Compiled IR module
            context: Execution context
            entry_function: Entry point (default: first function)

        Returns:
            ExecutionResult with action, intents, and trace
        """
        context.status = ExecutionStatus.RUNNING
        self.intent_emitter.clear()

        try:
            # Find entry function
            if entry_function:
                func = module.get_function(entry_function)
            elif module.functions:
                # Use first SAFETY function, or first function
                safety_funcs = module.get_functions_by_category(PolicyCategory.SAFETY)
                func = safety_funcs[0] if safety_funcs else list(module.functions.values())[0]
            else:
                return ExecutionResult(
                    success=False,
                    error="No functions in module",
                    execution_id=context.execution_id,
                )

            if not func:
                return ExecutionResult(
                    success=False,
                    error=f"Function not found: {entry_function}",
                    execution_id=context.execution_id,
                )

            # Execute function
            result_action = await self._execute_function(module, func, context)

            # Emit all pending intents
            emitted = await self.intent_emitter.emit_all()

            context.status = ExecutionStatus.COMPLETED
            context.final_action = result_action

            return ExecutionResult(
                success=True,
                action=result_action,
                intents=emitted,
                trace=context.trace,
                execution_id=context.execution_id,
                step_count=context.step_count,
            )

        except Exception as e:
            context.status = ExecutionStatus.FAILED
            return ExecutionResult(
                success=False,
                error=str(e),
                trace=context.trace,
                execution_id=context.execution_id,
                step_count=context.step_count,
            )

    async def _execute_function(
        self,
        module: IRModule,
        func: IRFunction,
        context: ExecutionContext,
    ) -> Optional[ActionType]:
        """Execute a single function."""
        context.push_call(func.name)
        context.add_trace("function_enter", {"name": func.name})

        # Initialize register file (SSA values)
        registers: Dict[int, Any] = {}

        # Start at entry block
        current_block = func.blocks.get(func.entry_block)
        if not current_block:
            context.pop_call()
            return None

        result_action: Optional[ActionType] = None

        while current_block:
            context.add_trace("block_enter", {"name": current_block.name})

            next_block_name: Optional[str] = None

            for instr in current_block.instructions:
                context.step_count += 1

                # Check step limit
                if context.step_count > context.max_steps:
                    raise RuntimeError(f"Execution exceeded max steps ({context.max_steps})")

                # Execute instruction
                result = await self._execute_instruction(instr, registers, context, module)

                # Handle control flow
                if isinstance(result, str):
                    # Jump to block
                    next_block_name = result
                    break
                elif isinstance(result, ActionType):
                    result_action = result

            # Move to next block
            if next_block_name:
                current_block = func.blocks.get(next_block_name)
            else:
                current_block = None

        context.pop_call()
        context.add_trace(
            "function_exit", {"name": func.name, "action": result_action.value if result_action else None}
        )

        return result_action

    async def _execute_instruction(
        self,
        instr: IRInstruction,
        registers: Dict[int, Any],
        context: ExecutionContext,
        module: IRModule,
    ) -> Any:
        """Execute a single instruction."""

        if isinstance(instr, IRLoadConst):
            registers[instr.id] = instr.value
            return None

        elif isinstance(instr, IRLoadVar):
            registers[instr.id] = context.get_variable(instr.name)
            return None

        elif isinstance(instr, IRStoreVar):
            value = registers.get(instr.value_id)
            context.set_variable(instr.name, value)
            return None

        elif isinstance(instr, IRBinaryOp):
            left = registers.get(instr.left_id)
            right = registers.get(instr.right_id)
            result = self._eval_binary_op(instr.op, left, right)
            registers[instr.id] = result
            return None

        elif isinstance(instr, IRUnaryOp):
            operand = registers.get(instr.operand_id)
            result = self._eval_unary_op(instr.op, operand)
            registers[instr.id] = result
            return None

        elif isinstance(instr, IRCompare):
            left = registers.get(instr.left_id)
            right = registers.get(instr.right_id)
            result = self._eval_compare(instr.op, left, right)
            registers[instr.id] = result
            return None

        elif isinstance(instr, IRJump):
            return instr.target_block

        elif isinstance(instr, IRJumpIf):
            condition = registers.get(instr.condition_id, False)
            if condition:
                return instr.true_block
            else:
                return instr.false_block

        elif isinstance(instr, IRCall):
            args = [registers.get(a) for a in instr.args]
            result = await self._call_function(instr.callee, args, context, module)
            registers[instr.id] = result
            return None

        elif isinstance(instr, IRReturn):
            if instr.value_id is not None:
                return registers.get(instr.value_id)
            return None

        elif isinstance(instr, IRAction):
            context.add_trace(
                "action",
                {
                    "action": instr.action.value,
                    "target": instr.target,
                },
            )

            # Create intent for the action
            intent_type = self._action_to_intent_type(instr.action)
            payload = IntentPayload(
                target_agent=instr.target,
                request_id=context.request_id,
                user_id=context.user_id,
            )

            self.intent_emitter.create_intent(
                intent_type=intent_type,
                payload=payload,
                priority=instr.governance.priority if instr.governance else 50,
                source_policy=instr.governance.source_policy if instr.governance else None,
                source_rule=instr.governance.source_rule if instr.governance else None,
                category=instr.governance.category.value if instr.governance else None,
                requires_confirmation=instr.action == ActionType.ESCALATE,
            )

            return instr.action

        elif isinstance(instr, IRCheckPolicy):
            if self._policy_validator is not None:
                try:
                    check_result = await self._policy_validator.validate_policy(
                        policy_id=getattr(instr, "policy_name", str(instr.id)),
                        context=context.variables,
                    )
                    registers[instr.id] = check_result["allowed"]
                except Exception:
                    # Fail-closed: validation error → deny
                    registers[instr.id] = False
            else:
                # Fail-closed: no validator → deny
                registers[instr.id] = False
            return None

        elif isinstance(instr, IREmitIntent):
            payload_data = {"data": [registers.get(p) for p in instr.payload_ids]}
            self.intent_emitter.create_intent(
                intent_type=IntentType[instr.intent_type.upper()] if instr.intent_type else IntentType.EXECUTE,
                payload=IntentPayload(context=payload_data),
                priority=instr.priority,
                requires_confirmation=instr.requires_confirmation,
            )
            return None

        return None

    def _eval_binary_op(self, op: str, left: Any, right: Any) -> Any:
        """Evaluate binary operation."""
        if op == "and":
            return bool(left) and bool(right)
        elif op == "or":
            return bool(left) or bool(right)
        return None

    def _eval_unary_op(self, op: str, operand: Any) -> Any:
        """Evaluate unary operation."""
        if op == "not":
            return not bool(operand)
        return None

    def _eval_compare(self, op: str, left: Any, right: Any) -> bool:
        """Evaluate comparison."""
        ops = {
            "==": lambda l, r: l == r,
            "!=": lambda l, r: l != r,
            "<": lambda l, r: l < r,
            ">": lambda l, r: l > r,
            "<=": lambda l, r: l <= r,
            ">=": lambda l, r: l >= r,
        }
        try:
            return bool(ops.get(op, lambda l, r: False)(left, right))
        except Exception:
            return False

    async def _call_function(
        self,
        name: str,
        args: List[Any],
        context: ExecutionContext,
        module: IRModule,
    ) -> Any:
        """Call a function (builtin or user-defined)."""
        # Check builtins first
        if name in self._builtin_functions:
            try:
                return self._builtin_functions[name](*args)
            except Exception:
                return None

        # Check module functions
        func = module.get_function(name)
        if func:
            # Save context and execute
            return await self._execute_function(module, func, context)

        return None

    def _action_to_intent_type(self, action: ActionType) -> IntentType:
        """Convert action to intent type."""
        mapping = {
            ActionType.DENY: IntentType.DENY,
            ActionType.ALLOW: IntentType.ALLOW,
            ActionType.ESCALATE: IntentType.ESCALATE,
            ActionType.ROUTE: IntentType.ROUTE,
        }
        return mapping.get(action, IntentType.EXECUTE)
