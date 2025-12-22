# M20 Policy AST Nodes
# AST node definitions with M19 governance metadata
"""
AST nodes for PLang v2.0.

Each node includes:
- Source location (line, column)
- Governance metadata where applicable
- Type-safe structure for analysis
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional

from app.policy.compiler.grammar import ActionType, PolicyCategory


@dataclass
class GovernanceMetadata:
    """
    M19 Governance metadata attached to AST nodes.

    This metadata is carried through compilation to runtime
    for governance-aware execution.
    """

    category: PolicyCategory
    priority: int = 50  # Default medium priority
    source_policy: Optional[str] = None
    source_rule: Optional[str] = None
    provenance: Optional[str] = None  # Audit trail

    def merge_with(self, other: "GovernanceMetadata") -> "GovernanceMetadata":
        """
        Merge governance metadata, taking higher priority.
        """
        # Higher priority wins
        if other.priority > self.priority:
            return GovernanceMetadata(
                category=other.category,
                priority=other.priority,
                source_policy=other.source_policy or self.source_policy,
                source_rule=other.source_rule or self.source_rule,
                provenance=f"{self.provenance or ''} -> {other.provenance or ''}".strip(" ->"),
            )
        return self


@dataclass
class ASTNode(ABC):
    """Base class for all AST nodes."""

    line: int = 0
    column: int = 0
    governance: Optional[GovernanceMetadata] = None

    @abstractmethod
    def accept(self, visitor: "ASTVisitor") -> Any:
        """Accept a visitor for traversal."""
        pass

    @property
    def location(self) -> str:
        """Get source location string."""
        return f"L{self.line}:{self.column}"


@dataclass
class ExprNode(ASTNode):
    """Base class for expression nodes."""

    pass


# ============================================================================
# Program Structure
# ============================================================================


@dataclass
class ProgramNode(ASTNode):
    """Root node representing a complete PLang program."""

    statements: List[ASTNode] = field(default_factory=list)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_program(self)


@dataclass
class PolicyDeclNode(ASTNode):
    """Policy declaration node."""

    name: str = ""
    category: PolicyCategory = PolicyCategory.CUSTOM
    body: List[ASTNode] = field(default_factory=list)

    def __post_init__(self):
        # Create governance metadata from category
        from app.policy.compiler.grammar import PLANG_GRAMMAR

        self.governance = GovernanceMetadata(
            category=self.category,
            priority=PLANG_GRAMMAR.get_category_priority(self.category.value),
            source_policy=self.name,
        )

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_policy_decl(self)


@dataclass
class RuleDeclNode(ASTNode):
    """Rule declaration node."""

    name: str = ""
    category: PolicyCategory = PolicyCategory.CUSTOM
    body: List[ASTNode] = field(default_factory=list)

    def __post_init__(self):
        from app.policy.compiler.grammar import PLANG_GRAMMAR

        self.governance = GovernanceMetadata(
            category=self.category,
            priority=PLANG_GRAMMAR.get_category_priority(self.category.value),
            source_rule=self.name,
        )

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_rule_decl(self)


@dataclass
class ImportNode(ASTNode):
    """Import statement node."""

    path: str = ""

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_import(self)


@dataclass
class RuleRefNode(ASTNode):
    """Reference to a named rule."""

    name: str = ""

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_rule_ref(self)


@dataclass
class PriorityNode(ASTNode):
    """Priority declaration node."""

    value: int = 50

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_priority(self)


# ============================================================================
# Condition and Action Blocks
# ============================================================================


@dataclass
class ConditionBlockNode(ASTNode):
    """When/then condition block."""

    condition: ExprNode = None
    action: "ActionBlockNode" = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_condition_block(self)


@dataclass
class ActionBlockNode(ASTNode):
    """Action block (deny, allow, escalate, route)."""

    action: ActionType = ActionType.DENY
    target: Optional["RouteTargetNode"] = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_action_block(self)


@dataclass
class RouteTargetNode(ASTNode):
    """Route target specification."""

    target: str = ""

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_route_target(self)


# ============================================================================
# Expressions
# ============================================================================


@dataclass
class BinaryOpNode(ExprNode):
    """Binary operation (and, or, ==, !=, etc.)."""

    op: str = ""
    left: ExprNode = None
    right: ExprNode = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_binary_op(self)


@dataclass
class UnaryOpNode(ExprNode):
    """Unary operation (not)."""

    op: str = ""
    operand: ExprNode = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_unary_op(self)


@dataclass
class ValueNode(ExprNode):
    """Base class for value nodes."""

    pass


@dataclass
class IdentNode(ValueNode):
    """Identifier node."""

    name: str = ""

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_ident(self)


@dataclass
class LiteralNode(ValueNode):
    """Literal value node (number, string, boolean)."""

    value: Any = None

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_literal(self)


@dataclass
class FuncCallNode(ExprNode):
    """Function call node."""

    callee: ExprNode = None
    args: List[ExprNode] = field(default_factory=list)

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_func_call(self)


@dataclass
class AttrAccessNode(ExprNode):
    """Attribute access node (obj.attr)."""

    obj: ExprNode = None
    attr: str = ""

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_attr_access(self)


# Type alias for visitor (forward reference resolved in visitors.py)
class ASTVisitor:
    """Forward reference for AST visitor."""

    pass
