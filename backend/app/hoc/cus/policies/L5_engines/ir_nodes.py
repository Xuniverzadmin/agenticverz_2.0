# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Policy IR node definitions (pure data structures)
# Callers: policy/ir/*
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: Policy System
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure data structures

# M20 Policy IR Nodes
# Intermediate representation nodes with governance metadata
"""
IR nodes for PLang v2.0 compilation.

IR design principles:
- Category-aware: Every node carries governance metadata
- SSA-like: Single assignment for optimization
- Intent-oriented: Designed for M18 intent emission
- Deterministic: Reproducible execution paths
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from app.policy.compiler.grammar import ActionType, PolicyCategory


class IRType(Enum):
    """IR value types."""

    VOID = auto()
    BOOL = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    POLICY = auto()
    RULE = auto()
    ACTION = auto()
    INTENT = auto()


@dataclass
class IRGovernance:
    """
    Governance metadata for IR nodes.

    Propagated from AST through compilation to runtime.
    Used by M19 policy engine for validation.
    """

    category: PolicyCategory
    priority: int
    source_policy: Optional[str] = None
    source_rule: Optional[str] = None
    requires_approval: bool = False
    audit_level: int = 0  # 0=none, 1=basic, 2=detailed, 3=full

    @classmethod
    def from_ast(cls, governance: Any) -> "IRGovernance":
        """Create from AST governance metadata."""
        if governance is None:
            return cls(category=PolicyCategory.CUSTOM, priority=50)
        return cls(
            category=governance.category,
            priority=governance.priority,
            source_policy=governance.source_policy,
            source_rule=governance.source_rule,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category.value,
            "priority": self.priority,
            "source_policy": self.source_policy,
            "source_rule": self.source_rule,
            "requires_approval": self.requires_approval,
            "audit_level": self.audit_level,
        }


@dataclass
class IRNode(ABC):
    """Base class for all IR nodes."""

    id: int = 0
    governance: Optional[IRGovernance] = None

    @abstractmethod
    def __str__(self) -> str:
        pass


# ============================================================================
# Instructions
# ============================================================================


@dataclass
class IRInstruction(IRNode):
    """Base class for IR instructions."""

    result_type: IRType = IRType.VOID


@dataclass
class IRLoadConst(IRInstruction):
    """Load constant value."""

    value: Any = None

    def __str__(self) -> str:
        return f"%{self.id} = const {self.value!r}"


@dataclass
class IRLoadVar(IRInstruction):
    """Load variable value."""

    name: str = ""

    def __str__(self) -> str:
        return f"%{self.id} = load {self.name}"


@dataclass
class IRStoreVar(IRInstruction):
    """Store value to variable."""

    name: str = ""
    value_id: int = 0

    def __str__(self) -> str:
        return f"store {self.name}, %{self.value_id}"


@dataclass
class IRBinaryOp(IRInstruction):
    """Binary operation."""

    op: str = ""
    left_id: int = 0
    right_id: int = 0

    def __str__(self) -> str:
        return f"%{self.id} = {self.op} %{self.left_id}, %{self.right_id}"


@dataclass
class IRUnaryOp(IRInstruction):
    """Unary operation."""

    op: str = ""
    operand_id: int = 0

    def __str__(self) -> str:
        return f"%{self.id} = {self.op} %{self.operand_id}"


@dataclass
class IRCompare(IRInstruction):
    """Comparison operation."""

    op: str = ""
    left_id: int = 0
    right_id: int = 0
    result_type: IRType = IRType.BOOL

    def __str__(self) -> str:
        return f"%{self.id} = cmp {self.op} %{self.left_id}, %{self.right_id}"


@dataclass
class IRJump(IRInstruction):
    """Unconditional jump."""

    target_block: str = ""

    def __str__(self) -> str:
        return f"jump {self.target_block}"


@dataclass
class IRJumpIf(IRInstruction):
    """Conditional jump."""

    condition_id: int = 0
    true_block: str = ""
    false_block: str = ""

    def __str__(self) -> str:
        return f"jumpif %{self.condition_id}, {self.true_block}, {self.false_block}"


@dataclass
class IRCall(IRInstruction):
    """Function call."""

    callee: str = ""
    args: List[int] = field(default_factory=list)

    def __str__(self) -> str:
        args_str = ", ".join(f"%{a}" for a in self.args)
        return f"%{self.id} = call {self.callee}({args_str})"


@dataclass
class IRReturn(IRInstruction):
    """Return from function."""

    value_id: Optional[int] = None

    def __str__(self) -> str:
        if self.value_id is not None:
            return f"return %{self.value_id}"
        return "return"


@dataclass
class IRAction(IRInstruction):
    """
    Policy action instruction.

    Actions: deny, allow, escalate, route
    """

    action: ActionType = ActionType.DENY
    target: Optional[str] = None  # For route action
    reason_id: Optional[int] = None  # Optional reason expression

    def __str__(self) -> str:
        parts = [f"action {self.action.value}"]
        if self.target:
            parts.append(f"to {self.target}")
        if self.reason_id is not None:
            parts.append(f"reason %{self.reason_id}")
        return " ".join(parts)


@dataclass
class IRCheckPolicy(IRInstruction):
    """
    Check against M19 policy engine.

    Emits validation request to policy engine before action.
    """

    policy_id: str = ""
    context_id: Optional[int] = None  # Context expression
    result_type: IRType = IRType.BOOL

    def __str__(self) -> str:
        ctx = f", ctx=%{self.context_id}" if self.context_id is not None else ""
        return f"%{self.id} = check_policy {self.policy_id}{ctx}"


@dataclass
class IREmitIntent(IRInstruction):
    """
    Emit intent to M18 execution layer.

    Intents are executed by M18 with governance constraints.
    """

    intent_type: str = ""
    payload_ids: List[int] = field(default_factory=list)
    priority: int = 50
    requires_confirmation: bool = False

    def __str__(self) -> str:
        payload = ", ".join(f"%{p}" for p in self.payload_ids)
        parts = [f"emit_intent {self.intent_type}({payload})"]
        if self.priority != 50:
            parts.append(f"priority={self.priority}")
        if self.requires_confirmation:
            parts.append("requires_confirmation")
        return " ".join(parts)


# ============================================================================
# Blocks and Functions
# ============================================================================


@dataclass
class IRBlock:
    """
    Basic block in IR.

    Contains a sequence of instructions with single entry/exit.
    """

    name: str = ""
    instructions: List[IRInstruction] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)
    governance: Optional[IRGovernance] = None

    def add_instruction(self, instr: IRInstruction) -> None:
        self.instructions.append(instr)

    @property
    def is_terminated(self) -> bool:
        """Check if block ends with terminator instruction."""
        if not self.instructions:
            return False
        last = self.instructions[-1]
        return isinstance(last, (IRJump, IRJumpIf, IRReturn, IRAction))

    def __str__(self) -> str:
        lines = [f"{self.name}:"]
        for instr in self.instructions:
            lines.append(f"  {instr}")
        return "\n".join(lines)


@dataclass
class IRFunction:
    """
    Function in IR.

    Represents a policy or rule as a callable unit.
    """

    name: str = ""
    params: List[str] = field(default_factory=list)
    return_type: IRType = IRType.VOID
    blocks: Dict[str, IRBlock] = field(default_factory=dict)
    entry_block: str = "entry"
    governance: Optional[IRGovernance] = None

    def add_block(self, block: IRBlock) -> None:
        self.blocks[block.name] = block

    def get_block(self, name: str) -> Optional[IRBlock]:
        return self.blocks.get(name)

    def __str__(self) -> str:
        params_str = ", ".join(self.params)
        gov_str = ""
        if self.governance:
            gov_str = f" [{self.governance.category.value}:{self.governance.priority}]"
        lines = [f"func {self.name}({params_str}) -> {self.return_type.name}{gov_str}:"]
        for block in self.blocks.values():
            lines.append(str(block))
        return "\n".join(lines)


@dataclass
class IRModule:
    """
    Module in IR.

    Represents a complete compiled PLang program.
    """

    name: str = ""
    functions: Dict[str, IRFunction] = field(default_factory=dict)
    globals: Dict[str, Any] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)
    governance: Optional[IRGovernance] = None

    # Category-indexed function lookup
    functions_by_category: Dict[PolicyCategory, List[str]] = field(default_factory=dict)

    def add_function(self, func: IRFunction) -> None:
        self.functions[func.name] = func
        # Index by category
        if func.governance:
            cat = func.governance.category
            if cat not in self.functions_by_category:
                self.functions_by_category[cat] = []
            self.functions_by_category[cat].append(func.name)

    def get_function(self, name: str) -> Optional[IRFunction]:
        return self.functions.get(name)

    def get_functions_by_category(self, category: PolicyCategory) -> List[IRFunction]:
        """Get all functions in a category, sorted by priority."""
        names = self.functions_by_category.get(category, [])
        funcs = [self.functions[n] for n in names if n in self.functions]
        return sorted(funcs, key=lambda f: f.governance.priority if f.governance else 50, reverse=True)

    def __str__(self) -> str:
        lines = [f"module {self.name}"]
        if self.imports:
            lines.append(f"imports: {', '.join(self.imports)}")
        lines.append("")
        for func in self.functions.values():
            lines.append(str(func))
            lines.append("")
        return "\n".join(lines)
